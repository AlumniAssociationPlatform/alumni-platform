from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from utils.user_role_enum import UserRole
from extensions import db
from models.announcement import Announcement
from sqlalchemy import func
from utils.timezone_helper import get_utc_now, ensure_timezone_aware
from datetime import datetime
import pytz

faculty = Blueprint("faculty", __name__, url_prefix="/faculty")

# Department display names mapping
DEPARTMENT_MAPPING = {
    "Computer Engineering": "COMPUTER_ENGINEERING",
    "IT Engineering": "IT_ENGINEERING",
    "Electrical Engineering": "ELECTRICAL_ENGINEERING",
    "Civil Engineering": "CIVIL_ENGINEERING",
    "Mechanical Engineering": "MECHANICAL_ENGINEERING",
}

REVERSE_DEPARTMENT_MAPPING = {v: k for k, v in DEPARTMENT_MAPPING.items()}

# =========================
# FACULTY-ONLY DECORATOR
# =========================
def faculty_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        role_value = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if role_value != UserRole.FACULTY.value:
            return redirect(url_for("auth.post_login"))

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


# =========================
# DASHBOARD
# =========================
@faculty.route("/dashboard")
@faculty_required
def dashboard():
    from models.faculty import Faculty
    from models.student import Student
    from models.alumni import Alumni
    
    # Get faculty profile
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("auth.login"))
    
    # Get statistics for the dashboard
    # Use display_name for comparison since Student/Alumni still use string departments
    dept_display = faculty_profile.department.display_name
    students_count = Student.query.filter_by(department=dept_display).count()
    alumni_count = Alumni.query.filter_by(department=dept_display).count()
    
    # Get recent announcements
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    context = {
        "faculty": faculty_profile,
        "students_count": students_count,
        "alumni_count": alumni_count,
        "recent_announcements": recent_announcements,
    }
    
    return render_template("faculty/dashboard.html", **context)


# =========================
# PROFILE
# =========================
@faculty.route("/profile", methods=["GET"])
@faculty_required
def profile():
    from models.faculty import Faculty, Department
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    departments = list(DEPARTMENT_MAPPING.keys())
    return render_template("faculty/profile.html", faculty=faculty_profile, departments=departments)


@faculty.route("/profile/edit", methods=["GET", "POST"])
@faculty_required
def edit_profile():
    from models.faculty import Faculty, Department
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        if request.method == "POST" and request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": "Faculty profile not found."}), 404
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.profile"))
    
    if request.method == "POST":
        try:
            # Update basic user information
            current_user.name = request.form.get("name", "").strip()
            current_user.email = request.form.get("email", "").strip()
            
            # Update faculty-specific information
            department_str = request.form.get("department", "").strip()
            # Convert display name to enum value
            if department_str in DEPARTMENT_MAPPING:
                enum_value = DEPARTMENT_MAPPING[department_str]
                faculty_profile.department = Department[enum_value]
            
            faculty_profile.designation = request.form.get("designation", "").strip()
            faculty_profile.phone_number = request.form.get("phone_number", "").strip() or None
            faculty_profile.linkedin_profile = request.form.get("linkedin_profile", "").strip() or None
            
            db.session.commit()
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": True,
                    "message": "Profile updated successfully!",
                    "redirect_url": url_for("faculty.profile")
                })
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for("faculty.profile"))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            error_msg = "An error occurred while updating your profile."
            
            # Check if request expects JSON (AJAX)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    "success": False,
                    "message": error_msg
                }), 400
            
            flash(error_msg, "error")
            return redirect(url_for("faculty.edit_profile"))
    
    departments = list(DEPARTMENT_MAPPING.keys())
    return render_template("faculty/edit_profile.html", faculty=faculty_profile, departments=departments)


# =========================
# VIEW ALUMNI (DEPARTMENT)
# =========================
@faculty.route("/alumni")
@faculty_required
def alumni():
    from models.faculty import Faculty
    from models.alumni import Alumni
    from models.user import User
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    # Get alumni from faculty's department who are approved
    dept_display = faculty_profile.department.display_name
    alumni_list = Alumni.query.join(User, Alumni.user_id == User.id).filter(
        Alumni.department == dept_display,
        User.is_approved == True
    ).all()
    
    return render_template(
        "faculty/alumni.html",
        alumni_list=alumni_list,
        department=dept_display
    )


# =========================
# VIEW FACULTIES
# =========================
@faculty.route("/faculties")
@faculty_required
def faculties():
    from models.faculty import Faculty
    from models.user import User
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    # Get all faculties from all departments (excluding current user)
    faculties_list = Faculty.query.join(User, Faculty.user_id == User.id).filter(
        User.is_approved == True,
        Faculty.user_id != current_user.id  # Exclude current user
    ).all()
    
    return render_template(
        "faculty/faculties.html",
        faculties_list=faculties_list
    )


# =========================
# VIEW FACULTY DETAILS
# =========================
@faculty.route("/faculty/<int:faculty_id>")
@faculty_required
def view_faculty(faculty_id):
    from models.faculty import Faculty
    from models.user import User
    
    faculty_detail = Faculty.query.filter_by(id=faculty_id).first()
    
    if not faculty_detail:
        flash("Faculty not found.", "error")
        return redirect(url_for("faculty.faculties"))
    
    # Verify faculty is approved
    if not faculty_detail.user.is_approved:
        flash("This faculty profile is not approved yet.", "error")
        return redirect(url_for("faculty.faculties"))
    
    return render_template(
        "faculty/faculty_detail.html",
        faculty=faculty_detail
    )


# =========================
# ANNOUNCEMENTS
# =========================
@faculty.route("/announcements")
@faculty_required
def announcements():
    """View all announcements"""
    page = request.args.get("page", 1, type=int)
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("faculty/announcements.html", announcements=announcements)


@faculty.route("/alumni/<int:alumni_id>")
@faculty_required
def view_alumni(alumni_id):
    from models.alumni import Alumni
    from models.faculty import Faculty
    from datetime import datetime
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    alumni = Alumni.query.get(alumni_id)
    
    if not alumni:
        return "Alumni not found", 404
    
    # Verify alumni belongs to faculty's department
    dept_display = faculty_profile.department.display_name
    if alumni.department != dept_display:
        return "Access denied", 403
    
    return render_template(
        "faculty/alumni_detail.html",
        alumni=alumni,
        now=datetime.now()
    )


# =========================
# VIEW STUDENTS (DEPARTMENT)
# =========================
@faculty.route("/students")
@faculty_required
def students():
    from models.faculty import Faculty
    from models.student import Student
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    # Get students from faculty's department
    dept_display = faculty_profile.department.display_name
    students_list = Student.query.filter_by(department=dept_display).all()
    
    return render_template(
        "faculty/students.html",
        students_list=students_list,
        department=dept_display
    )


@faculty.route("/student/<int:student_id>")
@faculty_required
def view_student(student_id):
    from models.student import Student
    from models.faculty import Faculty
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    student = Student.query.get(student_id)
    
    if not student:
        return "Student not found", 404
    
    # Verify student belongs to faculty's department
    dept_display = faculty_profile.department.display_name
    if student.department != dept_display:
        return "Access denied", 403
    
    return render_template(
        "faculty/student_detail.html",
        student=student
    )


# =========================
# RECOMMEND STUDENTS
# =========================
@faculty.route("/recommendations", methods=["GET", "POST"])
@faculty_required
def recommendations():
    from models.faculty import Faculty
    from models.student import Student
    from models.job import Job
    from models.recommendation import Recommendation
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    dept_display = faculty_profile.department.display_name
    students_list = Student.query.filter_by(department=dept_display).all()
    
    if request.method == "POST":
        try:
            student_ids = request.form.getlist("student_ids")
            job_id = request.form.get("job_id", "").strip()
            recommendation_text = request.form.get("recommendation_text", "").strip()
            
            # Validate inputs
            if not student_ids:
                flash("Please select at least one student.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            if not job_id:
                flash("Please select a job opportunity.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            if not recommendation_text:
                flash("Please provide recommendation details.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            # Validate job exists and is verified and active
            job = Job.query.get(job_id)
            if not job or not job.is_verified or not job.is_active:
                flash("Invalid job opportunity selected.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            # Validate all students belong to faculty's department
            invalid_students = []
            valid_students = []
            for student_id in student_ids:
                student = Student.query.get(student_id)
                if not student or student.department != dept_display:
                    invalid_students.append(student_id)
                else:
                    valid_students.append(student)
            
            if invalid_students:
                flash("One or more invalid student selections.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            if not valid_students:
                flash("No valid students selected.", "error")
                return redirect(url_for("faculty.recommendations"))
            
            # Create recommendations for all selected students
            recommendations_created = 0
            for student in valid_students:
                # Check if recommendation already exists
                existing_rec = Recommendation.query.filter_by(
                    student_id=student.id,
                    job_id=job.id,
                    faculty_id=faculty_profile.id
                ).first()
                
                if not existing_rec:
                    new_recommendation = Recommendation(
                        student_id=student.id,
                        job_id=job.id,
                        faculty_id=faculty_profile.id,
                        recommendation_text=recommendation_text
                    )
                    db.session.add(new_recommendation)
                    recommendations_created += 1
            
            if recommendations_created > 0:
                db.session.commit()
                flash(f"Successfully submitted {recommendations_created} recommendation(s)!", "success")
            else:
                flash("Recommendations already exist for selected students.", "warning")
            
            return redirect(url_for("faculty.recommendations"))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            flash("An error occurred while submitting recommendation.", "error")
            return redirect(url_for("faculty.recommendations"))
    
    # Fetch only verified and active jobs (exclude pending banner uploads)
    jobs = Job.query.filter_by(is_verified=True, is_active=True).all()

    
    return render_template(
        "faculty/recommendations.html",
        students_list=students_list,
        jobs=jobs,
        department=dept_display
    )


# =========================
# PLACEMENT CELL COORDINATION
# =========================
@faculty.route("/placement")
@faculty_required
def placement():
    from models.faculty import Faculty
    from models.job import Job
    from models.student import Student
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    # Get jobs and students for coordination
    dept_display = faculty_profile.department.display_name
    jobs = Job.query.all()
    students = Student.query.filter_by(department=dept_display).count()
    
    return render_template(
        "faculty/placement.html",
        jobs=jobs,
        students_count=students,
        department=dept_display
    )


# =========================
# SEMINARS & GUEST LECTURES
# =========================
@faculty.route("/seminars", methods=["GET", "POST"])
@faculty_required
def seminars():
    from models.faculty import Faculty
    from models.seminar import Seminar
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            date_str = request.form.get("date", "").strip()
            time_str = request.form.get("time", "").strip()
            location = request.form.get("location", "").strip()
            speaker_name = request.form.get("speaker_name", "").strip()
            topic = request.form.get("topic", "").strip()
            
            print(f"DEBUG: Received data - title={title}, date={date_str}, time={time_str}, location={location}, speaker={speaker_name}, topic={topic}")
            
            if not all([title, description, date_str, time_str, location, speaker_name, topic]):
                print(f"DEBUG: Missing required fields")
                flash("All fields are required.", "error")
                return redirect(url_for("faculty.seminars"))
            
            # Combine date and time
            try:
                seminar_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                # Convert naive datetime to UTC timezone-aware datetime
                seminar_datetime = ensure_timezone_aware(seminar_datetime, assume_utc=True)
                print(f"DEBUG: Parsed datetime: {seminar_datetime}")
            except ValueError as ve:
                print(f"DEBUG: DateTime parsing error: {str(ve)}")
                flash("Invalid date or time format.", "error")
                return redirect(url_for("faculty.seminars"))
            
            # Validate that seminar date is not in the past
            current_time = get_utc_now()
            print(f"DEBUG: Current time: {current_time}, Seminar datetime: {seminar_datetime}")
            
            if seminar_datetime < current_time:
                print(f"DEBUG: Seminar date is in the past")
                flash("Seminar date and time must be in the future. Please select today or a later date.", "error")
                return redirect(url_for("faculty.seminars"))
            
            print(f"DEBUG: Faculty profile - id={faculty_profile.id}, department={faculty_profile.department}")
            
            # Create seminar
            seminar = Seminar(
                title=title,
                description=description,
                date=seminar_datetime,
                location=location,
                speaker_name=speaker_name,
                topic=topic,
                faculty_id=faculty_profile.id,
                department=faculty_profile.department.display_name if hasattr(faculty_profile.department, 'display_name') else str(faculty_profile.department)
            )
            
            print(f"DEBUG: Seminar object created: {seminar}")
            
            db.session.add(seminar)
            db.session.commit()
            print(f"DEBUG: Seminar committed successfully with id={seminar.id}")
            
            flash(f"Seminar '{title}' scheduled successfully!", "success")
            return redirect(url_for("faculty.seminars"))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            flash(f"An error occurred while scheduling seminar: {str(e)}", "error")
            return redirect(url_for("faculty.seminars"))
    
    # Get all seminars created by this faculty
    my_seminars = Seminar.query.filter_by(faculty_id=faculty_profile.id).order_by(Seminar.date.desc()).all()
    
    return render_template(
        "faculty/seminar.html",
        department=faculty_profile.department.display_name if hasattr(faculty_profile.department, 'display_name') else str(faculty_profile.department),
        seminars=my_seminars
    )


@faculty.route("/seminars/<int:seminar_id>/delete", methods=["POST"])
@faculty_required
def delete_seminar(seminar_id):
    from models.faculty import Faculty
    from models.seminar import Seminar
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    seminar = Seminar.query.get(seminar_id)
    
    if not seminar or seminar.faculty_id != faculty_profile.id:
        flash("Seminar not found or you don't have permission to delete it.", "error")
        return redirect(url_for("faculty.seminars"))
    
    try:
        db.session.delete(seminar)
        db.session.commit()
        flash("Seminar deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the seminar.", "error")
    
    return redirect(url_for("faculty.seminars"))


# =========================
# GUIDANCE & SUPPORT
# =========================
@faculty.route("/guidance", methods=["GET", "POST"])
@faculty_required
def guidance():
    from models.faculty import Faculty
    from models.student import Student
    
    faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
    
    if not faculty_profile:
        flash("Faculty profile not found.", "error")
        return redirect(url_for("faculty.dashboard"))
    
    dept_display = faculty_profile.department.display_name
    students_list = Student.query.filter_by(department=dept_display).all()
    
    if request.method == "POST":
        try:
            student_id = request.form.get("student_id")
            guidance_type = request.form.get("guidance_type", "").strip()
            guidance_notes = request.form.get("guidance_notes", "").strip()
            
            if not all([student_id, guidance_type, guidance_notes]):
                flash("All fields are required.", "error")
                return redirect(url_for("faculty.guidance"))
            
            # Validate student
            student = Student.query.get(student_id)
            if not student or student.department != dept_display:
                flash("Invalid student selection.", "error")
                return redirect(url_for("faculty.guidance"))
            
            # Store guidance information
            flash(f"Guidance provided to {student.user.name}!", "success")
            return redirect(url_for("faculty.guidance"))
            
        except Exception as e:
            print(f"Error: {str(e)}")
            flash("An error occurred while providing guidance.", "error")
            return redirect(url_for("faculty.guidance"))
    
    return render_template(
        "faculty/guidence.html",
        students_list=students_list,
        department=dept_display
    )
