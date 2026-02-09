from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from utils.user_role_enum import UserRole
from extensions import db
from models.job import Job
from models.student import Student
from models.alumni import Alumni
from models.faculty import Faculty
from models.recommendation import Recommendation
from models.job_application import JobApplication
from models.user import User

placement = Blueprint("placement", __name__, url_prefix="/placement")


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
# PLACEMENT CELL REQUIRED DECORATOR
# =========================
def placement_cell_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        role_value = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if role_value != UserRole.PLACEMENT.value:
            return redirect(url_for("auth.post_login"))

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


# =========================
# PLACEMENT CELL - DASHBOARD
# =========================
@placement.route("/cell/dashboard")
@placement_cell_required
def dashboard():
    """Placement cell dashboard summarizing key counts and quick links"""
    # Counts
    total_students = Student.query.count()
    total_alumni = Alumni.query.count()
    total_faculty = Faculty.query.count()
    total_jobs = Job.query.filter_by(is_active=True).count()
    total_recommendations = Recommendation.query.count()
    total_applications = JobApplication.query.count()

    # Recent items (simple lists)
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_recommendations = Recommendation.query.order_by(Recommendation.created_at.desc()).limit(5).all()
    recent_applications = JobApplication.query.order_by(JobApplication.applied_at.desc()).limit(5).all()

    return render_template(
        "placement/dashboard.html",
        total_students=total_students,
        total_alumni=total_alumni,
        total_faculty=total_faculty,
        total_jobs=total_jobs,
        total_recommendations=total_recommendations,
        total_applications=total_applications,
        recent_jobs=recent_jobs,
        recent_recommendations=recent_recommendations,
        recent_applications=recent_applications,
    )


# =========================
# PLACEMENT CELL - ACTIVE JOBS LIST
# =========================
@placement.route("/cell/jobs")
@placement_cell_required
def jobs_list_cell():
    """Show active jobs and jobs posted by current placement cell user to placement cell users"""
    from sqlalchemy import or_
    page = request.args.get("page", 1, type=int)
    # Show active jobs OR jobs posted by the current placement cell user
    jobs = Job.query.filter(
        or_(
            Job.is_active == True,
            Job.posted_by == current_user.id
        )
    ).order_by(Job.created_at.desc()).paginate(page=page, per_page=10)

    return render_template("placement/jobs_list.html", jobs=jobs)


@placement.route("/cell/jobs/<int:job_id>")
@placement_cell_required
def view_job_cell(job_id):
    """Placement view of a single job detail"""
    job = Job.query.get_or_404(job_id)
    return render_template("placement/job_detail.html", job=job)


# =========================
# JOB LISTING - ALUMNI'S POSTINGS
# =========================
@placement.route("/jobs")
@alumni_required
def jobs_list():
    """Display all jobs posted by the current alumni"""
    page = request.args.get("page", 1, type=int)
    jobs = Job.query.filter_by(posted_by=current_user.id).order_by(
        Job.created_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template("alumni/jobs/jobs.html", jobs=jobs)


# =========================
# VIEW ALL JOBS (FOR BROWSING)
# =========================
@placement.route("/jobs/browse")
@alumni_required
def browse_jobs():
    """Browse all available jobs posted by alumni"""
    page = request.args.get("page", 1, type=int)
    job_type = request.args.get("job_type", "")
    
    query = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc())
    
    # Filter by job type if specified
    if job_type and job_type in ["Job", "Internship", "Both"]:
        query = query.filter(Job.job_type == job_type)
    
    jobs = query.paginate(page=page, per_page=10)
    
    return render_template("alumni/jobs/jobs_browse.html", jobs=jobs, job_type=job_type)


# =========================
# VIEW SINGLE JOB
# =========================
@placement.route("/jobs/<int:job_id>", methods=["GET"])
@alumni_required
def view_job(job_id):
    """View a single job posting"""
    job = Job.query.get_or_404(job_id)
    
    return render_template("alumni/jobs/job_detail.html", job=job)


# =========================
# CREATE NEW JOB/INTERNSHIP
# =========================
@placement.route("/jobs/create", methods=["GET", "POST"])
@alumni_required
def create_job():
    """Create a new job/internship posting"""
    if request.method == "POST":
        try:
            submit_mode = request.form.get("submit_mode", "form").strip()
            
            # BANNER MODE - Handle banner image upload
            if submit_mode == "banner":
                if 'banner_image' not in request.files:
                    error_msg = "No image file provided."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.create_job"))
                
                file = request.files['banner_image']
                
                if file.filename == '':
                    error_msg = "No image file selected."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.create_job"))
                
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                    error_msg = "Please upload a valid image file (PNG, JPG, JPEG, GIF)."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.create_job"))
                
                # Save the file
                import os
                from werkzeug.utils import secure_filename
                
                upload_folder = 'static/uploads/jobs'
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Get banner title and company from the form
                banner_title = request.form.get("banner_title", "").strip()
                banner_company = request.form.get("banner_company", "").strip()
                
                if not banner_title or not banner_company:
                    # Delete the uploaded file if validation fails
                    os.remove(file_path)
                    error_msg = "Please enter both job title and company name."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.create_job"))
                
                # Create job entry with banner and provided details
                new_job = Job(
                    title=banner_title,
                    company=banner_company,
                    description="",  # Will be filled by admin during approval
                    job_type="Job",
                    job_poster=filename,
                    posted_by=current_user.id,
                    is_active=False,  # Inactive until admin reviews
                    is_verified=False
                )
                
                db.session.add(new_job)
                db.session.commit()
                
                success_msg = "Banner uploaded successfully! Admin will review it and post the job details."
                
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("placement.jobs_list")
                    })
                
                flash(success_msg, "success")
                return redirect(url_for("placement.jobs_list"))
            
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
                    return redirect(url_for("placement.create_job"))
                
                if job_type not in ["Job", "Internship", "Both"]:
                    error_msg = "Invalid job type selected."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.create_job"))
                
                # Parse optional fields
                location = request.form.get("location", "").strip() or None
                salary_range = request.form.get("salary_range", "").strip() or None
                eligibility = request.form.get("eligibility", "").strip() or None
                department = request.form.get("department", "").strip() or None
                contact_email = request.form.get("contact_email", "").strip() or None
                contact_phone = request.form.get("contact_phone", "").strip() or None
                apply_link = request.form.get("apply_link", "").strip() or None
                company_website = request.form.get("company_website", "").strip() or None
                company_linkedin_url = request.form.get("company_linkedin_url", "").strip() or None
                
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
                        return redirect(url_for("placement.create_job"))
                
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
                    company_website=company_website,
                    company_linkedin_url=company_linkedin_url,
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
                        "redirect_url": url_for("placement.jobs_list")
                    })
                
                flash(success_msg, "success")
                return redirect(url_for("placement.jobs_list"))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"An error occurred: {str(e)}"
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("placement.create_job"))
    
    return render_template("placement/job_form.html", job=None)


# =========================
# EDIT JOB/INTERNSHIP
# =========================
@placement.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@alumni_required
def edit_job(job_id):
    """Edit an existing job/internship posting"""
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        flash("You don't have permission to edit this job posting.", "error")
        return redirect(url_for("placement.jobs_list"))
    
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
                    return redirect(url_for("placement.edit_job", job_id=job_id))

                # If a new file was uploaded, validate and save it
                if file and getattr(file, 'filename', ''):
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        error_msg = "Please upload a valid image file (PNG, JPG, JPEG, GIF)."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("placement.edit_job", job_id=job_id))

                    # Save the file
                    import os
                    from werkzeug.utils import secure_filename
                    upload_folder = 'static/uploads/jobs'
                    os.makedirs(upload_folder, exist_ok=True)

                    filename = secure_filename(file.filename)
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)

                    # Update job with the new banner (use job_poster column)
                    job.job_poster = filename

                else:
                    # No new file uploaded — require that an existing banner/poster is present
                    if not job.job_poster:
                        error_msg = "No image file provided. Please upload a banner image."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("placement.edit_job", job_id=job_id))

                # Update job title/company and mark for review
                job.title = banner_title
                job.company = banner_company
                job.description = job.description or "[Pending Review - Banner image uploaded]"
                job.job_type = job.job_type or "Job"
                job.is_active = False  # Inactive until admin reviews
                job.is_verified = False

                db.session.commit()

                success_msg = "Banner updated successfully! Admin will review it and update the job details."

                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("placement.jobs_list")
                    })

                flash(success_msg, "success")
                return redirect(url_for("placement.jobs_list"))
            
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
                    return redirect(url_for("placement.edit_job", job_id=job_id))
                
                if job_type not in ["Job", "Internship", "Both"]:
                    error_msg = "Invalid job type selected."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.edit_job", job_id=job_id))
                
                # Update job
                job.title = title
                job.company = company
                job.description = description
                job.job_type = job_type
                job.location = request.form.get("location", "").strip() or None
                job.salary_range = request.form.get("salary_range", "").strip() or None
                job.eligibility = request.form.get("eligibility", "").strip() or None
                job.department = request.form.get("department", "").strip() or None
                job.contact_email = request.form.get("contact_email", "").strip() or None
                job.contact_phone = request.form.get("contact_phone", "").strip() or None
                job.apply_link = request.form.get("apply_link", "").strip() or None
                job.company_website = request.form.get("company_website", "").strip() or None
                job.company_linkedin_url = request.form.get("company_linkedin_url", "").strip() or None
                # Ensure this is treated as a regular job posting
                
                # Parse deadline
                deadline_str = request.form.get("application_deadline", "").strip()
                if deadline_str:
                    try:
                        job.application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                    except ValueError:
                        error_msg = "Invalid date format for application deadline."
                        if request.headers.get('Accept') == 'application/json':
                            return jsonify({"success": False, "message": error_msg}), 400
                        flash(error_msg, "error")
                        return redirect(url_for("placement.edit_job", job_id=job_id))
                else:
                    job.application_deadline = None
                
                db.session.commit()
                
                success_msg = f"Job/Internship '{title}' updated successfully!"
                
                # Check if request expects JSON (AJAX)
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        "success": True,
                        "message": success_msg,
                        "redirect_url": url_for("placement.view_job", job_id=job_id)
                    })
                
                flash(success_msg, "success")
                return redirect(url_for("placement.view_job", job_id=job_id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"An error occurred: {str(e)}"
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("placement.edit_job", job_id=job_id))
    
    return render_template("placement/job_form.html", job=job)


# =========================
# DELETE JOB/INTERNSHIP
# =========================
@placement.route("/jobs/<int:job_id>/delete", methods=["POST"])
@alumni_required
def delete_job(job_id):
    """Delete a job/internship posting"""
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        flash("You don't have permission to delete this job posting.", "error")
        return redirect(url_for("placement.jobs_list"))
    
    try:
        job_title = job.title
        db.session.delete(job)
        db.session.commit()
        flash(f"Job/Internship '{job_title}' deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting: {str(e)}", "error")
    
    return redirect(url_for("placement.jobs_list"))


# =========================
# TOGGLE JOB ACTIVE STATUS
# =========================
@placement.route("/jobs/<int:job_id>/toggle-status", methods=["POST"])
@alumni_required
def toggle_job_status(job_id):
    """Toggle job active status (soft delete)"""
    job = Job.query.get_or_404(job_id)
    
    # Check if current user is the one who posted this job
    if job.posted_by != current_user.id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    try:
        job.is_active = not job.is_active
        db.session.commit()
        status = "activated" if job.is_active else "deactivated"
        return jsonify({
            "success": True,
            "message": f"Job/Internship {status} successfully",
            "is_active": job.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# PLACEMENT CELL - CREATE NEW JOB/INTERNSHIP (AS PLACEMENT CELL USER)
# =========================
@placement.route("/cell/jobs/create", methods=["GET", "POST"])
@placement_cell_required
def create_job_cell():
    """Placement cell user creating a new job/internship posting."""
    if request.method == "POST":
        try:
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
                return redirect(url_for("placement.create_job_cell"))
            
            if job_type not in ["Job", "Internship", "Both"]:
                error_msg = "Invalid job type selected."
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({"success": False, "message": error_msg}), 400
                flash(error_msg, "error")
                return redirect(url_for("placement.create_job_cell"))
            
            # Parse optional fields
            location = request.form.get("location", "").strip() or None
            salary_range = request.form.get("salary_range", "").strip() or None
            eligibility = request.form.get("eligibility", "").strip() or None
            department = request.form.get("department", "").strip() or None
            contact_email = request.form.get("contact_email", "").strip() or None
            contact_phone = request.form.get("contact_phone", "").strip() or None
            apply_link = request.form.get("apply_link", "").strip() or None
            company_website = request.form.get("company_website", "").strip() or None
            
            # Handle optional job poster image upload
            job_poster = None
            if 'job_poster' in request.files:
                file = request.files['job_poster']
                if file and file.filename != '':
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        try:
                            import os
                            from werkzeug.utils import secure_filename
                            import time
                            
                            upload_folder = 'static/uploads/jobs'
                            os.makedirs(upload_folder, exist_ok=True)
                            
                            filename = secure_filename(file.filename)
                            # Add timestamp to avoid filename conflicts
                            filename = f"{int(time.time())}_{filename}"
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            job_poster = filename
                        except Exception as file_error:
                            # Log error but continue without poster
                            print(f"Error saving job poster: {str(file_error)}")
            
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
                    return redirect(url_for("placement.create_job_cell"))
            
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
                company_website=company_website,
                job_poster=job_poster,
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
                    "redirect_url": url_for("placement.jobs_list_cell")
                })
            
            flash(success_msg, "success")
            return redirect(url_for("placement.jobs_list_cell"))
            
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
            return redirect(url_for("placement.create_job_cell"))
    
    return render_template("placement/job_form.html", job=None)


# =========================
# PLACEMENT CELL - EDIT JOB/INTERNSHIP (AS PLACEMENT CELL USER)
# =========================
@placement.route("/cell/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@placement_cell_required
def edit_job_cell(job_id):
    """Edit an existing job/internship posting"""
    job = Job.query.get_or_404(job_id)

    if request.method == "POST":
        try:
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
                return redirect(url_for("placement.edit_job_cell", job_id=job_id))
            
            if job_type not in ["Job", "Internship", "Both"]:
                error_msg = "Invalid job type selected."
                if request.headers.get('Accept') == 'application/json':
                    return jsonify({"success": False, "message": error_msg}), 400
                flash(error_msg, "error")
                return redirect(url_for("placement.edit_job_cell", job_id=job_id))
            
            # Update basic job information
            job.title = title
            job.company = company
            job.description = description
            job.job_type = job_type
            job.location = request.form.get("location", "").strip() or None
            job.salary_range = request.form.get("salary_range", "").strip() or None
            job.eligibility = request.form.get("eligibility", "").strip() or None
            job.department = request.form.get("department", "").strip() or None
            job.contact_email = request.form.get("contact_email", "").strip() or None
            job.contact_phone = request.form.get("contact_phone", "").strip() or None
            job.apply_link = request.form.get("apply_link", "").strip() or None
            job.company_website = request.form.get("company_website", "").strip() or None
            
            # Handle optional job poster image upload
            if 'job_poster' in request.files:
                file = request.files['job_poster']
                if file and file.filename != '':
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        try:
                            import os
                            from werkzeug.utils import secure_filename
                            import time
                            
                            upload_folder = 'static/uploads/jobs'
                            os.makedirs(upload_folder, exist_ok=True)
                            
                            filename = secure_filename(file.filename)
                            # Add timestamp to avoid filename conflicts
                            filename = f"{int(time.time())}_{filename}"
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            job.job_poster = filename
                        except Exception as file_error:
                            # Log error but continue without poster
                            print(f"Error saving job poster: {str(file_error)}")
            
            # Parse deadline
            deadline_str = request.form.get("application_deadline", "").strip()
            if deadline_str:
                try:
                    job.application_deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                except ValueError:
                    error_msg = "Invalid date format for application deadline."
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({"success": False, "message": error_msg}), 400
                    flash(error_msg, "error")
                    return redirect(url_for("placement.edit_job_cell", job_id=job_id))
            else:
                job.application_deadline = None
            
            db.session.commit()
            
            success_msg = f"Job/Internship '{title}' updated successfully!"
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": success_msg,
                    "redirect_url": url_for("placement.view_job_cell", job_id=job_id)
                })
            
            flash(success_msg, "success")
            return redirect(url_for("placement.view_job_cell", job_id=job_id))
            
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
            return redirect(url_for("placement.edit_job_cell", job_id=job_id))
    
    return render_template("placement/job_form.html", job=job)


# =========================
# PLACEMENT CELL - DELETE JOB/INTERNSHIP
# =========================
@placement.route("/cell/jobs/<int:job_id>/delete", methods=["POST"])
@placement_cell_required
def delete_job_cell(job_id):
    job = Job.query.get_or_404(job_id)

    try:
        job_title = job.title
        db.session.delete(job)
        db.session.commit()
        flash(f"Job/Internship '{job_title}' deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting: {str(e)}", "error")

    return redirect(url_for("placement.jobs_list_cell"))


# =========================
# PLACEMENT CELL - TOGGLE JOB ACTIVE STATUS
# =========================
@placement.route("/cell/jobs/<int:job_id>/toggle-status", methods=["POST"])
@placement_cell_required
def toggle_job_status_cell(job_id):
    job = Job.query.get_or_404(job_id)

    try:
        job.is_active = not job.is_active
        db.session.commit()
        status = "activated" if job.is_active else "deactivated"
        return jsonify({
            "success": True,
            "message": f"Job/Internship {status} successfully",
            "is_active": job.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# PLACEMENT CELL - VIEW ALL STUDENTS
# =========================
@placement.route("/cell/students")
@placement_cell_required
def view_students():
    """Display all students with their details"""
    page = request.args.get("page", 1, type=int)
    department = request.args.get("department", "")
    batch_year = request.args.get("batch_year", "")
    
    query = db.session.query(Student, User).join(User, Student.user_id == User.id)
    
    # Filter by department if specified
    if department:
        query = query.filter(Student.department == department)
    
    # Filter by batch year if specified
    if batch_year:
        query = query.filter(Student.batch_year == batch_year)
    
    students = query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    # Get unique departments and batch years for filter dropdowns
    all_departments = db.session.query(Student.department).distinct().all()
    all_batch_years = db.session.query(Student.batch_year).distinct().all()
    
    departments = [d[0] for d in all_departments if d[0]]
    batch_years = [b[0] for b in all_batch_years if b[0]]
    
    return render_template(
        "placement/students_list.html",
        students=students,
        departments=departments,
        batch_years=batch_years,
        selected_department=department,
        selected_batch_year=batch_year
    )


@placement.route("/cell/students/<int:student_id>")
@placement_cell_required
def view_student(student_id):
    """Show full student details to placement cell users"""
    student = Student.query.get_or_404(student_id)
    user = student.user

    # related data
    recommendations = getattr(student, 'recommendations', [])
    applications = []
    # Try to get job applications via user.id if available
    try:
        applications = user.applications if user else []
    except Exception:
        applications = []

    return render_template(
        "placement/student_detail.html",
        student=student,
        user=user,
        recommendations=recommendations,
        applications=applications,
    )


# =========================
# PLACEMENT CELL - VIEW ALL ALUMNI
# =========================
@placement.route("/cell/alumni")
@placement_cell_required
def view_alumni():
    """Display all alumni with their details"""
    page = request.args.get("page", 1, type=int)
    department = request.args.get("department", "")
    batch_year = request.args.get("batch_year", "")
    
    query = db.session.query(Alumni, User).join(User, Alumni.user_id == User.id)
    
    # Filter by department if specified
    if department:
        query = query.filter(Alumni.department == department)
    
    # Filter by batch year if specified
    if batch_year:
        query = query.filter(Alumni.batch_year == batch_year)
    
    alumni = query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    # Get unique departments and batch years for filter dropdowns
    all_departments = db.session.query(Alumni.department).distinct().all()
    all_batch_years = db.session.query(Alumni.batch_year).distinct().all()
    
    departments = [d[0] for d in all_departments if d[0]]
    batch_years = [b[0] for b in all_batch_years if b[0]]
    
    return render_template(
        "placement/alumni_list.html",
        alumni=alumni,
        departments=departments,
        batch_years=batch_years,
        selected_department=department,
        selected_batch_year=batch_year
    )


# =========================
# PLACEMENT CELL - VIEW ALL FACULTIES
# =========================
@placement.route("/cell/faculties")
@placement_cell_required
def view_faculties():
    """Display all faculties with their details"""
    page = request.args.get("page", 1, type=int)
    department = request.args.get("department", "")
    
    query = db.session.query(Faculty, User).join(User, Faculty.user_id == User.id)
    
    # Filter by department if specified
    if department:
        query = query.filter(Faculty.department == department)
    
    faculties = query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    # Get unique departments for filter dropdown
    all_departments = db.session.query(Faculty.department).distinct().all()
    departments = [d[0] for d in all_departments if d[0]]
    
    return render_template(
        "placement/faculties_list.html",
        faculties=faculties,
        departments=departments,
        selected_department=department
    )


# =========================
# PLACEMENT CELL - VIEW SINGLE ALUMNI
# =========================
@placement.route("/cell/alumni/<int:alumni_id>")
@placement_cell_required
def view_alumni_detail(alumni_id):
    """Show full alumni details to placement cell users"""
    alumni = Alumni.query.get_or_404(alumni_id)
    user = alumni.user

    # related data placeholders (if needed later)
    return render_template(
        "placement/alumni_detail.html",
        alumni=alumni,
        user=user,
    )


# =========================
# PLACEMENT CELL - VIEW SINGLE FACULTY
# =========================
@placement.route("/cell/faculties/<int:faculty_id>")
@placement_cell_required
def view_faculty_detail(faculty_id):
    """Show full faculty details to placement cell users"""
    faculty = Faculty.query.get_or_404(faculty_id)
    user = faculty.user

    # related data placeholders (if needed later)
    return render_template(
        "placement/faculty_detail.html",
        faculty=faculty,
        user=user,
    )


# =========================
# PLACEMENT CELL - VIEW STUDENT RECOMMENDATIONS
# =========================
@placement.route("/cell/recommendations")
@placement_cell_required
def view_recommendations():
    """Display all student recommendations made by faculties"""
    page = request.args.get("page", 1, type=int)
    student_id = request.args.get("student_id", "")
    faculty_id = request.args.get("faculty_id", "")
    
    query = db.session.query(Recommendation).join(Student, Recommendation.student_id == Student.id).join(
        Faculty, Recommendation.faculty_id == Faculty.id
    ).join(Job, Recommendation.job_id == Job.id)
    
    # Filter by student if specified
    if student_id:
        try:
            student_id_int = int(student_id)
            query = query.filter(Recommendation.student_id == student_id_int)
        except ValueError:
            pass
    
    # Filter by faculty if specified
    if faculty_id:
        try:
            faculty_id_int = int(faculty_id)
            query = query.filter(Recommendation.faculty_id == faculty_id_int)
        except ValueError:
            pass
    
    recommendations = query.order_by(Recommendation.created_at.desc()).paginate(page=page, per_page=10)
    
    # Get unique students and faculties for filter dropdowns
    all_students = db.session.query(Student.id, User.name).join(
        User, Student.user_id == User.id
    ).distinct().all()
    all_faculties = db.session.query(Faculty.id, User.name).join(
        User, Faculty.user_id == User.id
    ).distinct().all()
    
    students = [(s[0], s[1]) for s in all_students]
    faculties = [(f[0], f[1]) for f in all_faculties]
    
    return render_template(
        "placement/recommendations_list.html",
        recommendations=recommendations,
        students=students,
        faculties=faculties,
        selected_student_id=student_id,
        selected_faculty_id=faculty_id
    )


# =========================
# PLACEMENT CELL - VIEW JOB APPLICATIONS
# =========================
@placement.route("/cell/job-applications")
@placement_cell_required
def view_job_applications():
    """Display all job applications submitted by students"""
    page = request.args.get("page", 1, type=int)
    job_id = request.args.get("job_id", "")
    student_id = request.args.get("student_id", "")
    status = request.args.get("status", "")
    
    query = db.session.query(JobApplication).join(
        User, JobApplication.student_id == User.id
    ).join(Job, JobApplication.job_id == Job.id)
    
    # Filter by job if specified
    if job_id:
        try:
            job_id_int = int(job_id)
            query = query.filter(JobApplication.job_id == job_id_int)
        except ValueError:
            pass
    
    # Filter by student if specified
    if student_id:
        try:
            student_id_int = int(student_id)
            query = query.filter(JobApplication.student_id == student_id_int)
        except ValueError:
            pass
    
    # Filter by status if specified
    if status and status in ["applied", "shortlisted", "rejected", "selected"]:
        query = query.filter(JobApplication.status == status)
    
    applications = query.order_by(JobApplication.applied_at.desc()).paginate(page=page, per_page=10)
    
    # Get unique jobs and students for filter dropdowns
    all_jobs = db.session.query(Job.id, Job.title).distinct().all()
    all_students = db.session.query(User.id, User.name).filter(
        User.id.in_(db.session.query(JobApplication.student_id).distinct())
    ).all()
    
    jobs = [(j[0], j[1]) for j in all_jobs]
    students = [(s[0], s[1]) for s in all_students]
    statuses = ["applied", "shortlisted", "rejected", "selected"]
    
    return render_template(
        "placement/job_applications_list.html",
        applications=applications,
        jobs=jobs,
        students=students,
        statuses=statuses,
        selected_job_id=job_id,
        selected_student_id=student_id,
        selected_status=status
    )


# =========================
# PLACEMENT CELL - UPDATE JOB APPLICATION STATUS
# =========================
@placement.route("/cell/job-applications/<int:application_id>/update-status", methods=["POST"])
@placement_cell_required
def update_application_status(application_id):
    """Update the status of a job application (shortlist, reject, select)"""
    try:
        application = JobApplication.query.get_or_404(application_id)
        new_status = request.form.get("status", "").strip()
        
        # Validate status
        valid_statuses = ["applied", "shortlisted", "rejected", "selected"]
        if new_status not in valid_statuses:
            flash("Invalid status selected.", "error")
            return redirect(url_for("placement.view_job_applications"))
        
        # Update the application status
        old_status = application.status
        application.status = new_status
        db.session.commit()
        
        flash(f"Application status updated from '{old_status}' to '{new_status}'.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(url_for("placement.view_job_applications"))


@placement.route("/cell/job-applications/<int:application_id>/shortlist", methods=["POST"])
@placement_cell_required
def shortlist_application(application_id):
    """Shortlist a job application"""
    try:
        application = JobApplication.query.get_or_404(application_id)
        application.status = "shortlisted"
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": True,
                "message": "Application shortlisted successfully!",
                "status": "shortlisted"
            })
        
        flash("Application shortlisted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": str(e)}), 400
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("placement.view_job_applications"))


@placement.route("/cell/job-applications/<int:application_id>/reject", methods=["POST"])
@placement_cell_required
def reject_application(application_id):
    """Reject a job application"""
    try:
        application = JobApplication.query.get_or_404(application_id)
        application.status = "rejected"
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": True,
                "message": "Application rejected successfully!",
                "status": "rejected"
            })
        
        flash("Application rejected successfully!", "success")
    except Exception as e:
        db.session.rollback()
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": str(e)}), 400
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("placement.view_job_applications"))


@placement.route("/cell/job-applications/<int:application_id>/select", methods=["POST"])
@placement_cell_required
def select_application(application_id):
    """Select/Accept a job application"""
    try:
        application = JobApplication.query.get_or_404(application_id)
        application.status = "selected"
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "success": True,
                "message": "Application selected successfully!",
                "status": "selected"
            })
        
        flash("Application selected successfully!", "success")
    except Exception as e:
        db.session.rollback()
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": str(e)}), 400
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("placement.view_job_applications"))
