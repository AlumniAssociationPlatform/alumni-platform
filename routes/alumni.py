from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from utils.user_role_enum import UserRole
from extensions import db
from models.alumni import Alumni
from models.student import Student
from models.guidance import Guidance, GuidanceSession
from models.announcement import Announcement
from datetime import datetime

alumni = Blueprint("alumni", __name__, url_prefix="/alumni")

# =========================
# ALUMNI-ONLY DECORATOR
# =========================
def alumni_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        role_value = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if role_value != UserRole.ALUMNI.value:
            return redirect(url_for("auth.post_login"))

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


# =========================
# DASHBOARD
# =========================
@alumni.route("/dashboard")
@alumni_required
def dashboard():
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    return render_template("alumni/dashboard.html", recent_announcements=recent_announcements)


# =========================
# PROFILE
# =========================
@alumni.route("/profile", methods=["GET"])
@alumni_required
def profile():
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    return render_template("alumni/profile/profile.html", alumni=alumni_profile)


@alumni.route("/profile/edit", methods=["GET", "POST"])
@alumni_required
def edit_profile():
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    if not alumni_profile:
        if request.method == "POST" and request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": "Alumni profile not found."}), 404
        flash("Alumni profile not found.", "error")
        return redirect(url_for("alumni.profile"))
    
    if request.method == "POST":
        try:
            # Update basic user information
            current_user.name = request.form.get("name", "").strip()
            
            # Update alumni-specific information
            alumni_profile.department = request.form.get("department", "").strip()
            alumni_profile.batch_year = int(request.form.get("batch_year", 0)) if request.form.get("batch_year") else alumni_profile.batch_year
            alumni_profile.current_company = request.form.get("current_company", "").strip() or None
            alumni_profile.current_role = request.form.get("current_role", "").strip() or None
            alumni_profile.linkedin_profile = request.form.get("linkedin_profile", "").strip() or None
            alumni_profile.phone_number = request.form.get("phone_number", "").strip() or None
            
            db.session.commit()
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Profile updated successfully!",
                    "redirect_url": url_for("alumni.profile")
                })
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for("alumni.profile"))
            
        except Exception as e:
            db.session.rollback()
            error_msg = "An error occurred while updating your profile."
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("alumni.edit_profile"))
    
    return render_template("alumni/profile/edit_profile.html", alumni=alumni_profile)


# =========================
# ANNOUNCEMENTS
# =========================
@alumni.route("/announcements")
@alumni_required
def announcements():
    """View all announcements"""
    page = request.args.get("page", 1, type=int)
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("alumni/announcements.html", announcements=announcements)


# =========================
# JOBS & INTERNSHIPS
# =========================
@alumni.route("/jobs")
@alumni_required
def jobs_list():
    """Display all jobs posted by the current alumni"""
    from models.job import Job
    page = request.args.get("page", 1, type=int)
    jobs = Job.query.filter_by(posted_by=current_user.id).order_by(
        Job.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template("alumni/jobs/jobs.html", jobs=jobs)


@alumni.route("/jobs/create", methods=["GET", "POST"])
@alumni_required
def create_job():
    """Create a new job/internship posting"""
    from models.job import Job
    import os
    from werkzeug.utils import secure_filename
    import time
    
    if request.method == "POST":
        try:
            submit_mode = request.form.get("submit_mode", "form").strip()
            
            # BANNER MODE - Handle banner image upload
            if submit_mode == "banner":
                try:
                    if 'banner_image' not in request.files:
                        error_msg = "No image file provided."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.create_job"))
                    
                    file = request.files['banner_image']
                    
                    if file.filename == '':
                        error_msg = "No image file selected."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.create_job"))
                    
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        error_msg = "Please upload a valid image file (PNG, JPG, JPEG, GIF)."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.create_job"))
                    
                    # Save the file
                    upload_folder = 'static/uploads/jobs'
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid filename conflicts
                    filename = f"{int(time.time())}_{filename}"
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Get banner title and company from the form
                    banner_title = request.form.get("banner_title", "").strip()
                    banner_company = request.form.get("banner_company", "").strip()
                    
                    if not banner_title or not banner_company:
                        # Delete the uploaded file if validation fails
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        error_msg = "Please enter both job title and company name."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.create_job"))
                    
                    # Create job entry with banner and provided details
                    new_job = Job(
                        title=banner_title,
                        company=banner_company,
                        description="[Pending Review - Banner image uploaded]",
                        job_type="Job",
                        banner_image=filename,
                        is_from_banner=True,
                        posted_by=current_user.id,
                        is_active=False,
                        is_verified=False
                    )
                    
                    db.session.add(new_job)
                    db.session.commit()
                    
                    success_msg = "Banner uploaded successfully! Admin will review it and post the job details."
                    
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "success": True,
                            "message": success_msg,
                            "redirect_url": url_for("alumni.jobs_list")
                        })
                    
                    flash(success_msg, "success")
                    return redirect(url_for("alumni.jobs_list"))
                
                except Exception as banner_error:
                    # If file was saved, try to delete it on error
                    try:
                        if 'file_path' in locals() and os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass
                    
                    db.session.rollback()
                    error_msg = f"Error uploading banner: {str(banner_error)}"
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("alumni.create_job"))
            
            # FORM MODE - Handle form submission
            else:
                # Validate required fields
                title = request.form.get("title", "").strip()
                company = request.form.get("company", "").strip()
                description = request.form.get("description", "").strip()
                job_type = request.form.get("job_type", "").strip()
                
                if not all([title, company, description, job_type]):
                    error_msg = "Please fill in all required fields."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("alumni.create_job"))
                
                if job_type not in ["Job", "Internship", "Both"]:
                    error_msg = "Invalid job type selected."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("alumni.create_job"))
                
                # Parse optional fields
                location = request.form.get("location", "").strip() or None
                salary_range = request.form.get("salary_range", "").strip() or None
                eligibility = request.form.get("eligibility", "").strip() or None
                department = request.form.get("department", "").strip() or None
                contact_email = request.form.get("contact_email", "").strip() or None
                contact_phone = request.form.get("contact_phone", "").strip() or None
                apply_link = request.form.get("apply_link", "").strip() or None
                
                # Parse deadline
                deadline_str = request.form.get("application_deadline", "").strip()
                application_deadline = None
                if deadline_str:
                    try:
                        application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                    except ValueError:
                        error_msg = "Invalid date format for application deadline."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.create_job"))
                
                # Create new job
                new_job = Job(
                    title=title,
                    company=company,
                    description=description,
                    job_type=job_type,
                    location=location,
                    salary_range=salary_range,
                    eligibility=eligibility,
                    department=department,
                    contact_email=contact_email,
                    contact_phone=contact_phone,
                    apply_link=apply_link,
                    application_deadline=application_deadline,
                    posted_by=current_user.id,
                    is_active=True
                )
                
                db.session.add(new_job)
                db.session.commit()
                
                success_msg = f"Job/Internship '{title}' posted successfully!"
                
                # Check if request expects JSON (AJAX)
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("alumni.jobs_list")
                    })
                
                flash(success_msg, "success")
                return redirect(url_for("alumni.jobs_list"))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_msg = f"An error occurred: {str(e)}"
            traceback.print_exc()
            
            # Always return JSON if Accept header indicates it or it's a POST request
            if request.headers.get('Accept') == 'application/json':
                try:
                    return jsonify({
                        "success": False,
                        "message": error_msg
                    }), 400
                except Exception as json_error:
                    return '{"success": false, "message": "An unexpected server error occurred"}', 500, {'Content-Type': 'application/json'}
            
            # If it's a POST request but not expecting JSON, still try to return JSON for AJAX safety
            if request.method == 'POST':
                try:
                    return jsonify({
                        "success": False,
                        "message": error_msg
                    }), 400
                except Exception as json_error:
                    return '{"success": false, "message": "An unexpected server error occurred"}', 500, {'Content-Type': 'application/json'}
            
            flash(error_msg, "error")
            return redirect(url_for("alumni.create_job"))
    
    return render_template("alumni/jobs/job_form.html", job=None)


@alumni.route("/jobs/<int:job_id>", methods=["GET"])
@alumni_required
def view_job(job_id):
    """View a single job posting"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    
    return render_template("alumni/jobs/job_detail.html", job=job)


@alumni.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@alumni_required
def edit_job(job_id):
    """Edit an existing job/internship posting"""
    from models.job import Job
    import os
    from werkzeug.utils import secure_filename
    import time
    
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        flash("You don't have permission to edit this job posting.", "error")
        return redirect(url_for("alumni.jobs_list"))
    
    if request.method == "POST":
        try:
            submit_mode = request.form.get("submit_mode", "form").strip()
            
            # BANNER MODE - Handle banner image upload or update without re-upload
            if submit_mode == "banner":
                # Try to get an uploaded file (may be absent when editing)
                file = request.files.get('banner_image')

                # Read banner title/company from form
                banner_title = request.form.get("banner_title", "").strip()
                banner_company = request.form.get("banner_company", "").strip()

                # Require title/company in all cases
                if not banner_title or not banner_company:
                    error_msg = "Please enter both job title and company name."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("alumni.edit_job", job_id=job_id))

                # If a new file was uploaded, validate and save it
                if file and getattr(file, 'filename', ''):
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        error_msg = "Please upload a valid image file (PNG, JPG, JPEG, GIF)."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.edit_job", job_id=job_id))

                    # Save the file
                    upload_folder = 'static/uploads/jobs'
                    os.makedirs(upload_folder, exist_ok=True)

                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)

                    # Update job with the new banner
                    job.banner_image = filename

                else:
                    # No new file uploaded — require that an existing banner is present
                    if not job.banner_image:
                        error_msg = "No image file provided. Please upload a banner image."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.edit_job", job_id=job_id))

                # Update job title/company and mark for review
                job.title = banner_title
                job.company = banner_company
                job.description = job.description or "[Pending Review - Banner image uploaded]"
                job.job_type = job.job_type or "Job"
                job.is_from_banner = True
                job.is_active = False  # Inactive until admin reviews
                job.is_verified = False

                db.session.commit()

                success_msg = "Banner updated successfully! Admin will review it and update the job details."

                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("alumni.jobs_list")
                    })

                flash(success_msg, "success")
                return redirect(url_for("alumni.jobs_list"))
            
            # FORM MODE - Handle form submission
            else:
                title = request.form.get("title", "").strip()
                company = request.form.get("company", "").strip()
                description = request.form.get("description", "").strip()
                job_type = request.form.get("job_type", "").strip()
                location = request.form.get("location", "").strip() or None
                salary_range = request.form.get("salary_range", "").strip() or None
                eligibility = request.form.get("eligibility", "").strip() or None
                department = request.form.get("department", "").strip() or None
                contact_email = request.form.get("contact_email", "").strip() or None
                contact_phone = request.form.get("contact_phone", "").strip() or None
                apply_link = request.form.get("apply_link", "").strip() or None
                
                if not all([title, company, description, job_type]):
                    error_msg = "Please fill in all required fields."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("alumni.edit_job", job_id=job_id))
                
                # Parse deadline
                deadline_str = request.form.get("application_deadline", "").strip()
                application_deadline = None
                if deadline_str:
                    try:
                        application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                    except ValueError:
                        error_msg = "Invalid date format for application deadline."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("alumni.edit_job", job_id=job_id))
                
                job.title = title
                job.company = company
                job.description = description
                job.job_type = job_type
                job.location = location
                job.salary_range = salary_range
                job.eligibility = eligibility
                job.department = department
                job.contact_email = contact_email
                job.contact_phone = contact_phone
                job.apply_link = apply_link
                job.application_deadline = application_deadline
                
                db.session.commit()
                
                success_msg = f"Job/Internship '{title}' updated successfully!"
                
                # Check if request expects JSON (AJAX)
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("alumni.jobs_list")
                    })
                
                flash(success_msg, "success")
                return redirect(url_for("alumni.jobs_list"))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_msg = f"An error occurred: {str(e)}"
            traceback.print_exc()
            
            # Always return JSON if Accept header indicates it or it's a POST request
            if request.headers.get('Accept') == 'application/json' or request.method == 'POST':
                try:
                    return jsonify({
                        "success": False,
                        "message": error_msg
                    }), 400
                except Exception as json_error:
                    return '{"success": false, "message": "An unexpected server error occurred"}', 500, {'Content-Type': 'application/json'}
            
            flash(error_msg, "error")
            return redirect(url_for("alumni.edit_job", job_id=job_id))
    
    return render_template("alumni/jobs/job_form.html", job=job)


@alumni.route("/jobs/<int:job_id>/delete", methods=["POST"])
@alumni_required
def delete_job(job_id):
    """Delete a job/internship posting"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        flash("You don't have permission to delete this job posting.", "error")
        return redirect(url_for("alumni.jobs_list"))
    
    try:
        job_title = job.title
        db.session.delete(job)
        db.session.commit()
        
        success_msg = f"Job/Internship '{job_title}' deleted successfully!"
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": True,
                "message": success_msg,
                "redirect_url": url_for("alumni.jobs_list")
            })
        
        flash(success_msg, "success")
        return redirect(url_for("alumni.jobs_list"))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"An error occurred: {str(e)}"
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400
        
        flash(error_msg, "error")
        return redirect(url_for("alumni.jobs_list"))


@alumni.route("/jobs/<int:job_id>/toggle-status", methods=["POST"])
@alumni_required
def toggle_job_status(job_id):
    """Toggle a job posting status (active/inactive)"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        return jsonify({
            "success": False,
            "message": "You don't have permission to toggle this job status."
        }), 403
    
    try:
        job.is_active = not job.is_active
        db.session.commit()
        
        status_text = "activated" if job.is_active else "deactivated"
        return jsonify({
            "success": True,
            "message": f"Job/Internship '{job.title}' has been {status_text}."
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 400


# =========================
# STUDENT GUIDANCE
# =========================
@alumni.route("/guidance")
@alumni_required
def guidance():
    """List all guidances created by current alumni"""
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    if not alumni_profile:
        flash("Alumni profile not found.", "error")
        return redirect(url_for("alumni.dashboard"))
    
    page = request.args.get("page", 1, type=int)
    guidances = Guidance.query.filter_by(alumni_id=alumni_profile.id).paginate(
        page=page, per_page=10
    )
    
    return render_template("alumni/guidance/list.html", guidances=guidances, alumni_profile=alumni_profile)


@alumni.route("/guidance/create", methods=["GET", "POST"])
@alumni_required
def create_guidance():
    """Create a new guidance session"""
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    if not alumni_profile:
        flash("Alumni profile not found.", "error")
        return redirect(url_for("alumni.dashboard"))
    
    # Get all students to select from
    students = Student.query.all()
    
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            category = request.form.get("category", "Career").strip()
            duration_weeks = request.form.get("duration_weeks", 4, type=int)
            meeting_frequency = request.form.get("meeting_frequency", "Weekly").strip()
            preferred_method = request.form.get("preferred_method", "Virtual").strip()
            
            # Validation
            if not all([title, description, category]):
                return jsonify({
                    "success": False,
                    "message": "Please fill all required fields."
                }), 400
            
            if len(title) < 5 or len(title) > 200:
                return jsonify({
                    "success": False,
                    "message": "Title must be between 5 and 200 characters."
                }), 400
            
            if len(description) < 20:
                return jsonify({
                    "success": False,
                    "message": "Description must be at least 20 characters."
                }), 400
            
            # Create new guidance
            guidance = Guidance(
                alumni_id=alumni_profile.id,
                student_id=None,  # Available to all students
                title=title,
                description=description,
                category=category,
                duration_weeks=duration_weeks,
                meeting_frequency=meeting_frequency,
                preferred_method=preferred_method
            )
            
            db.session.add(guidance)
            db.session.commit()
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Guidance created successfully!",
                    "redirect_url": url_for("alumni.guidance")
                })
            
            flash("Guidance created successfully!", "success")
            return redirect(url_for("alumni.guidance"))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"An error occurred while creating guidance: {str(e)}"
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("alumni.create_guidance"))
    
    return render_template(
        "alumni/guidance/form.html",
        alumni_profile=alumni_profile,
        guidance=None,
        action="create"
    )


@alumni.route("/guidance/<int:guidance_id>", methods=["GET"])
@alumni_required
def view_guidance(guidance_id):
    """View guidance details"""
    guidance = Guidance.query.get_or_404(guidance_id)
    
    # Check authorization
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    if guidance.alumni_id != alumni_profile.id:
        flash("You don't have permission to view this guidance.", "error")
        return redirect(url_for("alumni.guidance"))
    
    sessions = guidance.guidance_sessions.order_by(GuidanceSession.session_date.desc()).all()
    
    return render_template(
        "alumni/guidance/detail.html",
        guidance=guidance,
        sessions=sessions,
        alumni_profile=alumni_profile
    )


@alumni.route("/guidance/<int:guidance_id>/enrolled-students")
@alumni_required
def view_enrolled_students(guidance_id):
    """View students enrolled in a guidance"""
    guidance = Guidance.query.get_or_404(guidance_id)
    
    # Check authorization
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    if guidance.alumni_id != alumni_profile.id:
        flash("You don't have permission to view this guidance.", "error")
        return redirect(url_for("alumni.guidance"))
    
    page = request.args.get("page", 1, type=int)
    
    # Get enrolled students - import GuidanceEnrollment for column reference
    from models.guidance import GuidanceEnrollment
    
    enrollments = guidance.enrollments.filter_by(status="active").order_by(
        GuidanceEnrollment.enrolled_at.desc()
    ).paginate(page=page, per_page=15)
    
    return render_template(
        "alumni/guidance/enrolled_students.html",
        guidance=guidance,
        enrollments=enrollments,
        alumni_profile=alumni_profile
    )


@alumni.route("/guidance/<int:guidance_id>/edit", methods=["GET", "POST"])
@alumni_required
def edit_guidance(guidance_id):
    """Edit a guidance"""
    guidance = Guidance.query.get_or_404(guidance_id)
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    # Check authorization
    if guidance.alumni_id != alumni_profile.id:
        flash("You don't have permission to edit this guidance.", "error")
        return redirect(url_for("alumni.guidance"))
    
    if request.method == "POST":
        try:
            guidance.title = request.form.get("title", "").strip()
            guidance.description = request.form.get("description", "").strip()
            guidance.category = request.form.get("category", "Career").strip()
            guidance.duration_weeks = request.form.get("duration_weeks", 4, type=int)
            guidance.meeting_frequency = request.form.get("meeting_frequency", "Weekly").strip()
            guidance.preferred_method = request.form.get("preferred_method", "Virtual").strip()
            guidance.status = request.form.get("status", "active").strip()
            
            # Validation
            if not all([guidance.title, guidance.description, guidance.category]):
                return jsonify({
                    "success": False,
                    "message": "Please fill all required fields."
                }), 400
            
            if len(guidance.title) < 5 or len(guidance.title) > 200:
                return jsonify({
                    "success": False,
                    "message": "Title must be between 5 and 200 characters."
                }), 400
            
            if len(guidance.description) < 20:
                return jsonify({
                    "success": False,
                    "message": "Description must be at least 20 characters."
                }), 400
            
            db.session.commit()
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Guidance updated successfully!",
                    "redirect_url": url_for("alumni.view_guidance", guidance_id=guidance.id)
                })
            
            flash("Guidance updated successfully!", "success")
            return redirect(url_for("alumni.view_guidance", guidance_id=guidance.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"An error occurred while updating guidance: {str(e)}"
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("alumni.edit_guidance", guidance_id=guidance_id))
    
    return render_template(
        "alumni/guidance/form.html",
        alumni_profile=alumni_profile,
        guidance=guidance,
        action="edit"
    )


@alumni.route("/guidance/<int:guidance_id>/delete", methods=["POST"])
@alumni_required
def delete_guidance(guidance_id):
    """Delete a guidance"""
    guidance = Guidance.query.get_or_404(guidance_id)
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    # Check authorization
    if guidance.alumni_id != alumni_profile.id:
        return jsonify({
            "success": False,
            "message": "You don't have permission to delete this guidance."
        }), 403
    
    try:
        db.session.delete(guidance)
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": True,
                "message": "Guidance deleted successfully!",
                "redirect_url": url_for("alumni.guidance")
            })
        
        flash("Guidance deleted successfully!", "success")
        return redirect(url_for("alumni.guidance"))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"An error occurred while deleting guidance: {str(e)}"
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": False,
                "message": error_msg
            }), 400
        
        flash(error_msg, "error")
        return redirect(url_for("alumni.view_guidance", guidance_id=guidance_id))


@alumni.route("/guidance/<int:guidance_id>/session/add", methods=["POST"])
@alumni_required
def add_guidance_session(guidance_id):
    """Add a new guidance session"""
    guidance = Guidance.query.get_or_404(guidance_id)
    alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
    
    # Check authorization
    if guidance.alumni_id != alumni_profile.id:
        return jsonify({
            "success": False,
            "message": "You don't have permission to add sessions to this guidance."
        }), 403
    
    try:
        session_date_str = request.form.get("session_date")
        notes = request.form.get("notes", "").strip()
        meeting_link = request.form.get("meeting_link", "").strip()
        location = request.form.get("location", "").strip()
        duration_minutes = request.form.get("duration_minutes", 60, type=int)
        
        # Parse datetime
        session_date = datetime.fromisoformat(session_date_str)
        
        if not session_date_str or not notes:
            return jsonify({
                "success": False,
                "message": "Please fill all required fields."
            }), 400
        
        # Validate that session date is not in the past
        if session_date < datetime.now():
            return jsonify({
                "success": False,
                "message": "Session date and time cannot be in the past. Please select a future date."
            }), 400
        
        # Create session
        guidance_session = GuidanceSession(
            guidance_id=guidance.id,
            session_date=session_date,
            notes=notes,
            meeting_link=meeting_link,
            location=location,
            duration_minutes=duration_minutes,
            status="scheduled"
        )
        
        db.session.add(guidance_session)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Session added successfully!",
            "session_id": guidance_session.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 400


@alumni.route("/enrollments/<int:enrollment_id>/remove", methods=["POST"])
@alumni_required
def remove_enrollment(enrollment_id):
    """Remove a student from guidance enrollment"""
    from models.guidance import GuidanceEnrollment
    
    try:
        enrollment = GuidanceEnrollment.query.get(enrollment_id)
        if not enrollment:
            return jsonify({"success": False, "message": "Enrollment not found."}), 404
        
        # Check authorization - verify the guidance belongs to the current alumni
        alumni_profile = Alumni.query.filter_by(user_id=current_user.id).first()
        if enrollment.guidance.alumni_id != alumni_profile.id:
            return jsonify({
                "success": False,
                "message": "You don't have permission to remove this enrollment."
            }), 403
        
        # Mark as withdrew instead of deleting
        enrollment.status = "withdrew"
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Student removed from this guidance program."
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 400


# =========================
# STUDENTS LIST
# =========================
@alumni.route("/students")
@alumni_required
def students_list():
    """View list of all students in the portal"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    
    query = Student.query
    
    # Search functionality
    if search:
        from models.user import User
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%"),
                Student.department.ilike(f"%{search}%")
            )
        )
    
    students = query.paginate(page=page, per_page=20)
    
    return render_template("alumni/students_list.html", students=students, search=search)


# =========================
# FACULTY LIST
# =========================
@alumni.route("/faculty")
@alumni_required
def faculty_list():
    """View list of all faculty members in the portal"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    
    from models.faculty import Faculty
    
    query = Faculty.query
    
    # Search functionality
    if search:
        from models.user import User
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                Faculty.faculty_id.ilike(f"%{search}%"),
                Faculty.designation.ilike(f"%{search}%")
            )
        )
    
    faculty = query.paginate(page=page, per_page=20)
    
    return render_template("alumni/faculty_list.html", faculty=faculty, search=search)


# =========================
# ALUMNI LIST
# =========================
@alumni.route("/alumni")
@alumni_required
def alumni_list():
    """View list of all alumni in the portal"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    
    query = Alumni.query.filter(Alumni.user_id != current_user.id)
    
    # Search functionality
    if search:
        from models.user import User
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                Alumni.alumni_id.ilike(f"%{search}%"),
                Alumni.department.ilike(f"%{search}%"),
                Alumni.current_company.ilike(f"%{search}%")
            )
        )
    
    alumni_list_data = query.paginate(page=page, per_page=20)
    
    return render_template("alumni/alumni_list.html", alumni=alumni_list_data, search=search)


# =========================
# EVENTS
# =========================
@alumni.route("/events")
@alumni_required
def events():
    return render_template("alumni/events.html")


# =========================
# EXPERIENCE SHARING
# =========================
@alumni.route("/experience")
@alumni_required
def experience():
    return render_template("alumni/experience.html")
