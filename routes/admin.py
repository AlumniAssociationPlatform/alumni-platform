from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from utils.user_role_enum import UserRole
from models.user import User
from extensions import db
from models.event import Event
from models.announcement import Announcement
from models.report import Report
from utils.report_generator import ReportGenerator
from datetime import datetime
import json
import csv
from io import StringIO, BytesIO
from datetime import datetime
import pytz
import os
import uuid
from werkzeug.utils import secure_filename

admin = Blueprint("admin", __name__, url_prefix="/admin")

# =========================
# FILE UPLOAD CONFIGURATION
# =========================
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'events')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_pdf_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS

def save_event_file(file, file_type='image'):
    """Save event file (image or PDF) and return the filename"""
    if not file or file.filename == '':
        return None
    
    if file_type == 'image':
        if not allowed_image_file(file.filename):
            raise ValueError("Invalid image format. Only PNG, JPG, JPEG, and WEBP allowed")
    else:  # pdf
        if not allowed_pdf_file(file.filename):
            raise ValueError("Invalid file format. Only PDF allowed")
    
    if file.content_length and file.content_length > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 5 MB limit")
    
    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"event_{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Save file
    file.save(filepath)
    
    # Return filename for database storage
    return unique_filename

# =========================
# ADMIN-ONLY DECORATOR
# =========================
def admin_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        role_value = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if role_value != UserRole.INSTITUTE.value:
            # redirect non-admins to their correct dashboard
            return redirect(url_for("auth.post_login"))

        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper


# =========================
# ADMIN DASHBOARD
# =========================
@admin.route("/dashboard")
@admin_required
def dashboard():
    from models.job import Job
    from sqlalchemy import func
    
    # Get statistics
    total_users = User.query.filter(User.role != "INSTITUTE").count()
    approved_users = User.query.filter(User.role != "INSTITUTE", User.is_approved == True).count()
    pending_approvals = User.query.filter(User.role != "INSTITUTE", User.is_approved == False).count()
    
    # User breakdown by role
    students = User.query.filter(User.role == UserRole.STUDENT).count()
    alumni = User.query.filter(User.role == UserRole.ALUMNI).count()
    faculty = User.query.filter(User.role == UserRole.FACULTY).count()
    
    # Events and Jobs
    active_events = Event.query.count()
    verified_jobs = Job.query.filter(Job.is_verified == True).count()
    open_jobs = verified_jobs
    
    # Recent activities
    recent_users = User.query.filter(User.role != "INSTITUTE").order_by(User.created_at.desc()).limit(5).all()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        approved_users=approved_users,
        pending_approvals=pending_approvals,
        students=students,
        alumni=alumni,
        faculty=faculty,
        active_events=active_events,
        open_jobs=open_jobs,
        verified_jobs=verified_jobs,
        recent_users=recent_users,
        recent_events=recent_events,
        recent_jobs=recent_jobs,
        recent_announcements=recent_announcements
    )

# =========================
# USER MANAGEMENT
# =========================
@admin.route("/approvals")
@admin_required
def approvals():
    pending_users = User.query.filter(
        User.is_approved.is_(False),
        User.role.in_([
            UserRole.ALUMNI,
            UserRole.STUDENT,
            UserRole.FACULTY
        ])
    ).all()
    return render_template("admin/approvals.html", pending_users=pending_users)

@admin.route("/approvals/view/<int:user_id>")
@admin_required
def view_approval_user(user_id):
    user = User.query.get_or_404(user_id)
    student_profile = None
    faculty_profile = None
    alumni_profile = None
    if user.role.value == UserRole.STUDENT.value:
        student_profile = user.student_profile
    elif user.role.value == UserRole.FACULTY.value:
        faculty_profile = user.faculty_profile
    elif user.role.value == UserRole.ALUMNI.value:
        alumni_profile = user.alumni_profile
    return render_template("admin/approval_user_view.html", user=user, student_profile=student_profile, faculty_profile=faculty_profile, alumni_profile=alumni_profile)

@admin.route("/approvals/approve/<int:user_id>", methods=["POST"])
@admin_required
def approve_user(user_id):
    user = User.query.get(user_id)
    if not user:
        if request.is_json:
            return jsonify({"status": "error", "message": "User not found"}), 404
        flash("User not found", "danger")
        return redirect(url_for("admin.approvals"))

    try:
        user.is_approved = True
        db.session.commit()
        if request.is_json:
            return jsonify({"status": "success"})
        flash("User approved", "success")
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"status": "error", "message": str(e)}), 500
        flash(f"Error approving user: {e}", "danger")

    return redirect(url_for("admin.approvals"))


@admin.route("/approvals/reject/<int:user_id>", methods=["POST"])
@admin_required
def reject_user(user_id):
    user = User.query.get(user_id)
    if not user:
        if request.is_json:
            return jsonify({"status": "error", "message": "User not found"}), 404
        flash("User not found", "danger")
        return redirect(url_for("admin.approvals"))

    try:
        # Mark as blocked so account cannot be used; keep record
        user.is_blocked = True
        db.session.commit()
        if request.is_json:
            return jsonify({"status": "success"})
        flash("User rejected and blocked", "warning")
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"status": "error", "message": str(e)}), 500
        flash(f"Error rejecting user: {e}", "danger")

    return redirect(url_for("admin.approvals"))


@admin.route("/users")
@admin_required
def users():
    users = User.query.filter(
        User.role != UserRole.INSTITUTE
    ).order_by(User.created_at.desc()).all()

    return render_template("admin/users.html", users=users)

@admin.route("/users/view/<int:user_id>")
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    student_profile = None
    faculty_profile = None
    alumni_profile = None
    if user.role.value == UserRole.STUDENT.value:
        student_profile = user.student_profile
    elif user.role.value == UserRole.FACULTY.value:
        faculty_profile = user.faculty_profile
    elif user.role.value == UserRole.ALUMNI.value:
        alumni_profile = user.alumni_profile
    return render_template("admin/user_view.html", user=user, student_profile=student_profile, faculty_profile=faculty_profile, alumni_profile=alumni_profile)

@admin.route("/users/block/<int:user_id>", methods=["POST"])
@admin_required
def toggle_block_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        user.is_blocked = not user.is_blocked
        db.session.commit()

        flash(
            "User blocked" if user.is_blocked else "User unblocked",
            "warning"
        )
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin.users"))

@admin.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully", "danger")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin.users"))

# =========================
# EVENTS & JOBS
# =========================
@admin.route("/events")
@admin_required
def events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template("admin/events/list.html", events=events)

@admin.route("/events/create", methods=["GET", "POST"])
@admin_required
def create_event():
    if request.method == "POST":
        try:
            # Validate banner image (compulsory)
            banner_image_file = request.files.get('banner_image')
            if not banner_image_file or banner_image_file.filename == '':
                flash("Banner image is required", "error")
                return redirect(url_for("admin.create_event"))
            
            # Save banner image
            banner_image = save_event_file(banner_image_file, 'image')
            
            # Handle optional PDF file
            pdf_file = None
            pdf_file_upload = request.files.get('pdf_file')
            if pdf_file_upload and pdf_file_upload.filename != '':
                pdf_file = save_event_file(pdf_file_upload, 'pdf')
            
            # Get multiple department selections
            departments = request.form.getlist("department")
            department_str = ",".join(departments) if departments else ""
            
            event = Event(
                title=request.form.get("title"),
                description=request.form.get("description"),
                event_date=datetime.strptime(
                    request.form.get("event_date"), "%Y-%m-%d"
                ),
                department=department_str,
                banner_image=banner_image,
                pdf_file=pdf_file,
                created_by=current_user.id
            )

            db.session.add(event)
            db.session.commit()
            flash("Event created successfully", "success")

            return redirect(url_for("admin.events"))
        
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("admin.create_event"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("admin.create_event"))

    return render_template("admin/events/form.html", event=None)

@admin.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == "POST":
        try:
            event.title = request.form.get("title")
            event.description = request.form.get("description")
            event.event_date = datetime.strptime(
                request.form.get("event_date"), "%Y-%m-%d"
            )
            # Get multiple department selections
            departments = request.form.getlist("department")
            event.department = ",".join(departments) if departments else ""
            
            # Handle banner image update (if provided)
            banner_image_file = request.files.get('banner_image')
            if banner_image_file and banner_image_file.filename != '':
                # Delete old banner image if exists
                if event.banner_image:
                    old_image_path = os.path.join(UPLOAD_FOLDER, event.banner_image)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except:
                            pass
                
                # Save new banner image
                event.banner_image = save_event_file(banner_image_file, 'image')
            
            # Handle PDF file update (if provided)
            pdf_file_upload = request.files.get('pdf_file')
            if pdf_file_upload and pdf_file_upload.filename != '':
                # Delete old PDF file if exists
                if event.pdf_file:
                    old_pdf_path = os.path.join(UPLOAD_FOLDER, event.pdf_file)
                    if os.path.exists(old_pdf_path):
                        try:
                            os.remove(old_pdf_path)
                        except:
                            pass
                
                # Save new PDF file
                event.pdf_file = save_event_file(pdf_file_upload, 'pdf')

            db.session.commit()
            flash("Event updated successfully", "success")
            return redirect(url_for("admin.events"))
        
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("admin.edit_event", event_id=event_id))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("admin.edit_event", event_id=event_id))

    return render_template("admin/events/form.html", event=event)

@admin.route("/events/delete/<int:event_id>", methods=["POST"])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    db.session.delete(event)
    db.session.commit()

    flash("Event deleted successfully", "danger")
    return redirect(url_for("admin.events"))

@admin.route("/events/<int:event_id>/participants")
@admin_required
def event_participants(event_id):
    """View all students registered for an event"""
    from models.event_participant import EventParticipant
    from models.student import Student
    
    event = Event.query.get_or_404(event_id)
    
    # Get all participants for this event
    participants = EventParticipant.query.filter_by(event_id=event_id).all()
    
    # Get student details for each participant
    participant_details = []
    for participant in participants:
        student = Student.query.filter_by(user_id=participant.user_id).first()
        participant_details.append({
            'user': participant.user,
            'student': student,
            'registered_at': participant.registered_at
        })
    
    return render_template(
        "admin/events/participants.html",
        event=event,
        participant_details=participant_details,
        total_participants=len(participant_details)
    )

@admin.route("/jobs")
@admin_required
def jobs():
    """View and manage all job posts uploaded by alumni"""
    from models.job import Job
    
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "all")  # all, verified, pending, inactive
    
    query = Job.query
    
    # Apply status filter
    if status_filter == "verified":
        query = query.filter(Job.is_verified == True)
    elif status_filter == "pending":
        query = query.filter(Job.is_verified == False)
    elif status_filter == "inactive":
        query = query.filter(Job.is_active == False)
    
    # Get all jobs posted by alumni, ordered by creation date (newest first)
    jobs_list = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=15
    )
    
    # Count statistics
    total_jobs = Job.query.count()
    verified_jobs = Job.query.filter(Job.is_verified == True).count()
    pending_jobs = Job.query.filter(Job.is_verified == False).count()
    inactive_jobs = Job.query.filter(Job.is_active == False).count()
    
    return render_template(
        "admin/jobs.html",
        jobs=jobs_list,
        status_filter=status_filter,
        total_jobs=total_jobs,
        verified_jobs=verified_jobs,
        pending_jobs=pending_jobs,
        inactive_jobs=inactive_jobs
    )


@admin.route("/jobs/<int:job_id>/verify", methods=["POST"])
@admin_required
def verify_job(job_id):
    """Verify/Approve a job posting"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    
    try:
        job.is_verified = True
        job.is_active = True  # Activate the job when verified
        db.session.commit()
        flash(f"Job '{job.title}' has been verified and activated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error verifying job: {str(e)}", "danger")
    
    return redirect(url_for("admin.jobs", status=request.args.get("status", "all")))


@admin.route("/jobs/<int:job_id>/reject", methods=["POST"])
@admin_required
def reject_job(job_id):
    """Reject/Delete a job posting"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    
    try:
        job.is_active = False
        job.is_verified = False
        db.session.commit()
        flash(f"Job '{job.title}' has been rejected and deactivated.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error rejecting job: {str(e)}", "danger")
    
    return redirect(url_for("admin.jobs", status=request.args.get("status", "all")))


@admin.route("/jobs/<int:job_id>/delete", methods=["POST"])
@admin_required
def delete_job(job_id):
    """Permanently delete a job posting"""
    from models.job import Job
    
    job = Job.query.get_or_404(job_id)
    job_title = job.title
    
    try:
        db.session.delete(job)
        db.session.commit()
        flash(f"Job '{job_title}' has been permanently deleted.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting job: {str(e)}", "danger")
    
    return redirect(url_for("admin.jobs", status=request.args.get("status", "all")))


# =========================
# REPORTS & SYSTEM
# =========================
@admin.route("/reports")
@admin_required
def reports():
    """View all generated reports"""
    page = request.args.get("page", 1, type=int)
    reports_list = Report.query.order_by(Report.created_at.desc()).paginate(
        page=page, per_page=10
    )
    report_types = ReportGenerator.get_all_report_types()
    return render_template(
        "admin/reports.html", reports=reports_list, report_types=report_types
    )


@admin.route("/reports/generate", methods=["GET", "POST"])
@admin_required
def generate_report():
    """Generate a new report"""
    report_types = ReportGenerator.get_all_report_types()
    ist = pytz.timezone("Asia/Kolkata")
    created_at_ist = datetime.now(ist)

    if request.method == "POST":
        try:
            report_type = request.form.get("report_type")
            if not report_type:
                flash("Report type is required", "danger")
                return redirect(url_for("admin.generate_report"))

            # Prepare filters
            filters = {}
            if report_type == "user_statistics":
                filters["days"] = int(request.form.get("days", 30))
            elif report_type == "alumni_network":
                department = request.form.get("department")
                if department:
                    filters["department"] = department
            elif report_type == "job_analytics":
                filters["days"] = int(request.form.get("days", 30))
            elif report_type == "event_summary":
                filters["days"] = int(request.form.get("days", 90))
            elif report_type == "announcements":
                filters["days"] = int(request.form.get("days", 30))

            # Generate report data
            report_data = ReportGenerator.generate_report(report_type, **filters)

            # Get report title
            report_title = dict(report_types).get(
                report_type, f"Report - {report_type}"
            )

            # Save report to database
            report = Report(
                report_type=report_type,
                title=report_title,
                description=request.form.get("description", ""),
                generated_by=current_user.id,
                data=json.dumps(report_data),
                filters=json.dumps(filters),
                status="completed",
                created_at=created_at_ist
            )

            db.session.add(report)
            db.session.commit()

            flash(f"Report '{report_title}' generated successfully", "success")
            return redirect(url_for("admin.view_report", report_id=report.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Error generating report: {str(e)}", "danger")
            return redirect(url_for("admin.generate_report"))

    return render_template("admin/reports/form.html", report_types=report_types)


@admin.route("/reports/<int:report_id>")
@admin_required
def view_report(report_id):
    """View a specific report"""
    report = Report.query.get_or_404(report_id)
    report_data = json.loads(report.data) if report.data else {}
    return render_template("admin/reports/view.html", report=report, report_data=report_data)


@admin.route("/reports/<int:report_id>/download")
@admin_required
def download_report(report_id):
    """Download report as CSV"""
    report = Report.query.get_or_404(report_id)

    try:
        report_data = json.loads(report.data) if report.data else {}

        # Create CSV file
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([f"{report.title} - Generated on {report.created_at}"])
        writer.writerow([])

        # Write summary section
        if "summary" in report_data:
            writer.writerow(["Summary"])
            summary = report_data["summary"]
            for key, value in summary.items():
                writer.writerow([key, value])
            writer.writerow([])

        # Write other sections
        for section, data in report_data.items():
            if section != "summary" and isinstance(data, dict):
                writer.writerow([section.replace("_", " ").title()])
                for key, value in data.items():
                    if isinstance(value, dict):
                        writer.writerow([key])
                        for sub_key, sub_value in value.items():
                            writer.writerow([f"  {sub_key}", sub_value])
                    else:
                        writer.writerow([key, value])
                writer.writerow([])

        # Create response
        output.seek(0)
        mem = BytesIO()
        mem.write(output.getvalue().encode("utf-8"))
        mem.seek(0)

        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{report.report_type}_{report.id}.csv",
        )

    except Exception as e:
        flash(f"Error downloading report: {str(e)}", "danger")
        return redirect(url_for("admin.view_report", report_id=report_id))


@admin.route("/reports/<int:report_id>/delete", methods=["POST"])
@admin_required
def delete_report(report_id):
    """Delete a report"""
    report = Report.query.get_or_404(report_id)

    try:
        db.session.delete(report)
        db.session.commit()
        flash("Report deleted successfully", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting report: {str(e)}", "danger")

    return redirect(url_for("admin.reports"))


@admin.route("/announcements")
@admin_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("admin/announcements/list.html", announcements=announcements)

@admin.route("/announcements/create", methods=["GET", "POST"])
@admin_required
def create_announcement():
    if request.method == "POST":
        announcement = Announcement(
            title=request.form.get("title"),
            description=request.form.get("description"),
            created_by=current_user.id
        )

        db.session.add(announcement)
        db.session.commit()
        flash("Announcement created successfully", "success")

        return redirect(url_for("admin.announcements"))

    return render_template("admin/announcements/form.html", announcement=None)

@admin.route("/announcements/edit/<int:announcement_id>", methods=["GET", "POST"])
@admin_required
def edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    if request.method == "POST":
        announcement.title = request.form.get("title")
        announcement.description = request.form.get("description")

        db.session.commit()
        flash("Announcement updated successfully", "success")
        return redirect(url_for("admin.announcements"))

    return render_template("admin/announcements/form.html", announcement=announcement)

@admin.route("/announcements/delete/<int:announcement_id>", methods=["POST"])
@admin_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted successfully", "danger")
    return redirect(url_for("admin.announcements"))


@admin.route("/security")
@admin_required
def security():
    return render_template("admin/security.html")
