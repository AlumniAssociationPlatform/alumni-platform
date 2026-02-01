from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from utils.user_role_enum import UserRole
from models.guidance import Guidance
from models.announcement import Announcement
from models.user import User
from extensions import db
from datetime import datetime

student = Blueprint("student", __name__, url_prefix="/student")

# =========================
# STUDENT-ONLY DECORATOR
# =========================
def student_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        role_value = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if role_value != UserRole.STUDENT.value:
            return redirect(url_for("auth.post_login"))

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


# =========================
# DASHBOARD
# =========================
@student.route("/dashboard")
@student_required
def dashboard():
    from models.student import Student
    from models.seminar import Seminar
    from sqlalchemy import and_
    
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    # Get student profile to filter seminars by department
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get upcoming seminars for student's department
    upcoming_seminars = []
    if student_profile:
        current_time = datetime.utcnow()
        upcoming_seminars = Seminar.query.filter(
            and_(
                Seminar.department == student_profile.department,
                Seminar.date >= current_time
            )
        ).order_by(Seminar.date.asc()).limit(3).all()
    
    return render_template(
        "student/dashboard.html", 
        recent_announcements=recent_announcements,
        upcoming_seminars=upcoming_seminars
    )


# =========================
# PROFILE
# =========================
@student.route("/profile")
@student_required
def profile():
    from models.student import Student
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    return render_template("student/profile.html", student=student_profile)


@student.route("/profile/edit", methods=["GET", "POST"])
@student_required
def edit_profile():
    from models.student import Student
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        if request.method == "POST" and request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": "Student profile not found."}), 404
        flash("Student profile not found.", "error")
        return redirect(url_for("student.profile"))
    
    if request.method == "POST":
        try:
            # Update basic user information
            current_user.name = request.form.get("name", "").strip()
            
            # Update student-specific information
            student_profile.department = request.form.get("department", "").strip()
            student_profile.batch_year = request.form.get("batch_year", "").strip()
            student_profile.skills = request.form.get("skills", "").strip() or None
            student_profile.phone_number = request.form.get("phone_number", "").strip() or None
            student_profile.linkedin_profile = request.form.get("linkedin_profile", "").strip() or None
            
            db.session.commit()
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Profile updated successfully!",
                    "redirect_url": url_for("student.profile")
                })
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for("student.profile"))
            
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
            return redirect(url_for("student.edit_profile"))

    return render_template("student/edit_profile.html", student=student_profile)


# =========================
# ALUMNI DIRECTORY
# =========================
@student.route("/alumni")
@student_required
def alumni_list():
    from models.student import Student
    from models.alumni import Alumni
    
    # Get current student's profile and department
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))
    
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    department_code = request.args.get("department", "").strip()
    show_same_dept = request.args.get("show_same_dept", "false").lower() == "true"
    
    # Department mapping from abbreviations to full names
    dept_mapping = {
        "CSE": "Computer Engineering",
        "ECE": "Electronics Engineering",
        "ME": "Mechanical Engineering",
        "CE": "Civil Engineering",
        "IT": "IT Engineering"
    }
    
    # Convert department code to full name
    department_filter = dept_mapping.get(department_code, "") if department_code else ""
    
    # Start with all alumni
    query = Alumni.query.join(Alumni.user).filter(Alumni.user.has(is_approved=True))
    
    # Filter by same department if checkbox is checked
    if show_same_dept and student_profile.department:
        query = query.filter(Alumni.department == student_profile.department)
    elif department_filter:
        query = query.filter(Alumni.department == department_filter)
    
    # Search by name or company (case-insensitive)
    if search:
        query = query.filter(
            (Alumni.user.has(db.func.lower(User.name).contains(search.lower()))) |
            (db.func.lower(Alumni.current_company).contains(search.lower())) |
            (db.func.lower(Alumni.current_role).contains(search.lower()))
        )
    
    # Order by most recent first
    query = query.order_by(Alumni.created_at.desc())
    
    alumni_list = query.paginate(page=page, per_page=12)
    
    return render_template(
        "student/alumni.html",
        alumni=alumni_list,
        student=student_profile,
        search=search,
        department_filter=department_code,
        show_same_dept=show_same_dept
    )


# =========================
# JOBS & INTERNSHIPS
# =========================
@student.route("/jobs")
@student_required
def jobs():
    """Browse verified job postings from alumni"""
    from models.job import Job
    
    page = request.args.get("page", 1, type=int)
    job_type = request.args.get("job_type", "")
    search = request.args.get("search", "").strip()
    
    # Show only verified and approved jobs to students
    # Must be BOTH verified by admin AND active
    query = Job.query.filter(Job.is_verified == True, Job.is_active == True).order_by(Job.created_at.desc())
    
    # Filter by job type if specified
    if job_type and job_type in ["Job", "Internship", "Both"]:
        query = query.filter(Job.job_type == job_type)
    
    # Search by title, company, or description
    if search:
        query = query.filter(
            (Job.title.ilike(f"%{search}%")) |
            (Job.company.ilike(f"%{search}%")) |
            (Job.description.ilike(f"%{search}%"))
        )
    
    jobs_list = query.paginate(page=page, per_page=15)
    
    return render_template(
        "student/jobs.html",
        jobs=jobs_list,
        job_type=job_type,
        search=search
    )


# =========================
# ANNOUNCEMENTS
# =========================
@student.route("/announcements")
@student_required
def announcements():
    """View all announcements"""
    page = request.args.get("page", 1, type=int)
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("student/announcements.html", announcements=announcements)


# =========================
# EVENTS
# =========================
@student.route("/events")
@student_required
def events():
    """Browse and view events"""
    from models.event import Event
    from models.event_participant import EventParticipant
    
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    
    # Query all events ordered by date
    query = Event.query.order_by(Event.event_date.desc())
    
    if search:
        query = query.filter(
            (Event.title.ilike(f"%{search}%")) |
            (Event.description.ilike(f"%{search}%"))
        )
    
    events_list = query.paginate(page=page, per_page=12)
    
    # Get student's registered events
    student_events = EventParticipant.query.filter_by(user_id=current_user.id).all()
    registered_event_ids = [e.event_id for e in student_events]
    
    return render_template(
        "student/events.html",
        events=events_list,
        registered_event_ids=registered_event_ids,
        search=search
    )


@student.route("/events/<int:event_id>/register", methods=["POST"])
@student_required
def register_event(event_id):
    """Register for an event"""
    from models.event import Event
    from models.event_participant import EventParticipant
    
    try:
        event = Event.query.get(event_id)
        if not event:
            return jsonify({"success": False, "message": "Event not found."}), 404
        
        # Check if event date is in the past
        if event.event_date and event.event_date < datetime.now().date():
            return jsonify({"success": False, "message": "Cannot register for past events."}), 400
        
        # Check if already registered
        existing = EventParticipant.query.filter_by(
            user_id=current_user.id,
            event_id=event_id
        ).first()
        
        if existing:
            return jsonify({"success": False, "message": "You are already registered for this event."}), 400
        
        # Create registration
        participant = EventParticipant(
            user_id=current_user.id,
            event_id=event_id
        )
        db.session.add(participant)
        db.session.commit()
        
        flash(f"Successfully registered for {event.title}!", "success")
        return jsonify({"success": True, "message": f"Registered for {event.title}!"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error registering for event."}), 500


@student.route("/events/<int:event_id>/unregister", methods=["POST"])
@student_required
def unregister_event(event_id):
    """Unregister from an event"""
    from models.event_participant import EventParticipant
    
    try:
        participant = EventParticipant.query.filter_by(
            user_id=current_user.id,
            event_id=event_id
        ).first()
        
        if not participant:
            return jsonify({"success": False, "message": "Registration not found."}), 404
        
        db.session.delete(participant)
        db.session.commit()
        
        flash("Unregistered from event.", "success")
        return jsonify({"success": True, "message": "Unregistered from event."})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error unregistering from event."}), 500


# =========================
# GUIDANCE / MENTORSHIP
# =========================
@student.route("/guidance")
@student_required
def guidance():
    """Browse available guidance from alumni"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    
    query = Guidance.query.filter_by(status="active").order_by(Guidance.created_at.desc())
    
    if search:
        query = query.filter(
            (Guidance.topic.ilike(f"%{search}%")) |
            (Guidance.description.ilike(f"%{search}%"))
        )
    
    guidances = query.paginate(page=page, per_page=12)
    return render_template("student/guidance/browse.html", guidances=guidances, search=search)


@student.route("/guidance/<int:guidance_id>")
@student_required
def guidance_detail(guidance_id):
    """View guidance details and ask questions"""
    guidance = Guidance.query.get_or_404(guidance_id)
    
    if guidance.status != "active":
        flash("This guidance is no longer available.", "warning")
        return redirect(url_for("student.guidance"))
    
    return render_template("student/guidance/detail.html", guidance=guidance)


@student.route("/guidance/<int:guidance_id>/ask", methods=["POST"])
@student_required
def ask_question(guidance_id):
    """Ask a question on guidance"""
    from models.guidance import GuidanceQuestion
    
    try:
        guidance = Guidance.query.get(guidance_id)
        if not guidance:
            return jsonify({"success": False, "message": "Guidance not found."}), 404
        
        question_text = request.form.get("question", "").strip()
        if not question_text:
            return jsonify({"success": False, "message": "Question cannot be empty."}), 400
        
        # Create question
        question = GuidanceQuestion(
            guidance_id=guidance_id,
            user_id=current_user.id,
            question=question_text
        )
        db.session.add(question)
        db.session.commit()
        
        flash("Question posted successfully!", "success")
        return jsonify({
            "success": True,
            "message": "Question posted successfully!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error posting question."}), 500


@student.route("/guidance/<int:guidance_id>/enroll", methods=["POST"])
@student_required
def enroll_guidance(guidance_id):
    """Enroll in a guidance program"""
    from models.guidance import GuidanceEnrollment
    from models.student import Student
    
    try:
        guidance = Guidance.query.get(guidance_id)
        if not guidance:
            return jsonify({"success": False, "message": "Guidance not found."}), 404
        
        if guidance.status != "active":
            return jsonify({"success": False, "message": "This guidance is no longer available."}), 400
        
        # Get student profile
        student_profile = Student.query.filter_by(user_id=current_user.id).first()
        if not student_profile:
            return jsonify({"success": False, "message": "Student profile not found."}), 404
        
        # Check if already enrolled
        existing_enrollment = GuidanceEnrollment.query.filter_by(
            guidance_id=guidance_id,
            student_id=student_profile.id
        ).first()
        
        if existing_enrollment:
            return jsonify({"success": False, "message": "You are already enrolled in this guidance."}), 400
        
        # Create enrollment
        enrollment = GuidanceEnrollment(
            guidance_id=guidance_id,
            student_id=student_profile.id,
            status="active"
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        flash(f"Successfully enrolled in {guidance.title}!", "success")
        return jsonify({
            "success": True,
            "message": f"Successfully enrolled in {guidance.title}!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error enrolling in guidance."}), 500


@student.route("/guidance/<int:guidance_id>/unenroll", methods=["POST"])
@student_required
def unenroll_guidance(guidance_id):
    """Unenroll from a guidance program"""
    from models.guidance import GuidanceEnrollment
    from models.student import Student
    
    try:
        student_profile = Student.query.filter_by(user_id=current_user.id).first()
        if not student_profile:
            return jsonify({"success": False, "message": "Student profile not found."}), 404
        
        enrollment = GuidanceEnrollment.query.filter_by(
            guidance_id=guidance_id,
            student_id=student_profile.id
        ).first()
        
        if not enrollment:
            return jsonify({"success": False, "message": "Enrollment not found."}), 404
        
        # Update status to withdrew instead of deleting
        enrollment.status = "withdrew"
        db.session.commit()
        
        flash("Unenrolled from guidance.", "success")
        return jsonify({
            "success": True,
            "message": "Unenrolled from guidance."
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error unenrolling from guidance."}), 500


@student.route("/my-enrollments")
@student_required
def my_enrollments():
    """View all enrolled guidance programs"""
    from models.student import Student
    from models.guidance import GuidanceEnrollment
    
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if not student_profile:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))
    
    page = request.args.get("page", 1, type=int)
    
    enrollments = GuidanceEnrollment.query.filter_by(
        student_id=student_profile.id,
        status="active"
    ).order_by(GuidanceEnrollment.enrolled_at.desc()).paginate(page=page, per_page=12)
    
    return render_template("student/guidance/my_enrollments.html", enrollments=enrollments)




@student.route("/jobs/<int:job_id>")
@student_required
def view_job(job_id):
    """View job/internship details"""
    from models.job import Job
    from models.job_application import JobApplication
    
    # Only allow viewing verified and active jobs
    job = Job.query.filter(
        Job.id == job_id,
        Job.is_verified == True,
        Job.is_active == True
    ).first_or_404()
    
    # Check if student has already applied
    application = JobApplication.query.filter_by(
        job_id=job_id,
        student_id=current_user.id
    ).first()
    
    return render_template(
        "student/jobs/detail.html",
        job=job,
        application=application
    )


@student.route("/jobs/<int:job_id>/apply", methods=["POST"])
@student_required
def apply_job(job_id):
    """Apply for a job/internship"""
    from models.job import Job
    from models.job_application import JobApplication
    from datetime import datetime
    
    job = Job.query.get_or_404(job_id)
    
    # Check if job is still active
    if not job.is_active or not job.is_verified:
        return jsonify({"success": False, "message": "This job is no longer available"}), 400
    
    # Check if deadline has passed
    if job.application_deadline and job.application_deadline < datetime.now().date():
        return jsonify({"success": False, "message": "Application deadline has passed"}), 400
    
    # Check if already applied
    existing_application = JobApplication.query.filter_by(
        job_id=job_id,
        student_id=current_user.id
    ).first()
    
    if existing_application:
        return jsonify({"success": False, "message": "You have already applied for this job"}), 400
    
    try:
        # Create new application
        application = JobApplication(
            job_id=job_id,
            student_id=current_user.id,
            status="applied"
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Application submitted successfully!",
            "redirect_url": url_for("student.view_job", job_id=job_id)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@student.route("/applications")
@student_required
def my_applications():
    """View all job applications submitted by student"""
    from models.job_application import JobApplication
    
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    
    query = JobApplication.query.filter_by(student_id=current_user.id).order_by(
        JobApplication.applied_at.desc()
    )
    
    # Filter by status if specified
    if status and status in ["applied", "shortlisted", "rejected", "selected"]:
        query = query.filter(JobApplication.status == status)
    
    applications = query.paginate(page=page, per_page=10)
    
    return render_template(
        "student/jobs/applications.html",
        applications=applications,
        status=status
    )


# =========================
# SEMINARS & LECTURES
# =========================
@student.route("/seminars")
@student_required
def seminars():
    """View all available seminars and lectures for student's department (only upcoming seminars)"""
    from models.student import Student
    from models.seminar import Seminar
    from sqlalchemy import and_
    
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash("Student profile not found.", "error")
        return redirect(url_for("student.dashboard"))
    
    # Get only upcoming seminars for student's department (date >= now)
    from datetime import datetime
    current_time = datetime.utcnow()
    
    seminars_list = Seminar.query.filter(
        and_(
            Seminar.department == student_profile.department,
            Seminar.date >= current_time
        )
    ).order_by(Seminar.date.asc()).all()
    
    return render_template(
        "student/seminars.html",
        seminars=seminars_list,
        department=student_profile.department
    )


@student.route("/seminars/<int:seminar_id>")
@student_required
def view_seminar(seminar_id):
    """View detailed information about a specific seminar (only if it's upcoming)"""
    from models.student import Student
    from models.seminar import Seminar
    from datetime import datetime
    
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    seminar = Seminar.query.get_or_404(seminar_id)
    
    # Verify seminar is for student's department
    if seminar.department != student_profile.department:
        flash("This seminar is not available for your department.", "error")
        return redirect(url_for("student.seminars"))
    
    # Check if seminar date is not in the past
    current_time = datetime.utcnow()
    if seminar.date < current_time:
        flash("This seminar has already occurred.", "warning")
        return redirect(url_for("student.seminars"))
    
    return render_template(
        "student/seminar_detail.html",
        seminar=seminar
    )


# =========================
# STUDENTS LIST
# =========================
@student.route("/students")
@student_required
def students_list():
    """View list of all students in the portal"""
    from models.student import Student
    
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    
    query = Student.query
    
    # Search functionality
    if search:
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%"),
                Student.department.ilike(f"%{search}%")
            )
        )
    
    students = query.paginate(page=page, per_page=20)
    
    return render_template("student/students_list.html", students=students, search=search)


# =========================
# FACULTY LIST
# =========================
@student.route("/faculty")
@student_required
def faculty_list():
    """View list of all faculty members in the portal"""
    from models.faculty import Faculty
    
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str).strip()
    
    query = Faculty.query
    
    # Search functionality
    if search:
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                Faculty.faculty_id.ilike(f"%{search}%"),
                Faculty.designation.ilike(f"%{search}%")
            )
        )
    
    faculty = query.paginate(page=page, per_page=20)
    
    return render_template("student/faculty_list.html", faculty=faculty, search=search)

