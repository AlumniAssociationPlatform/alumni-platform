from flask import Flask, render_template, redirect, url_for, has_request_context
from flask_migrate import Migrate
from flask_login import current_user
from config import Config
from extensions import db, login_manager

import os
import logging

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------
# Flask App Initialization
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)

# Set timezone
os.environ["TZ"] = "UTC"

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)

migrate = Migrate(app, db)

# ---------------------------
# Import Models AFTER db init
# ---------------------------
from models import User
from utils.timezone_helper import format_datetime_local

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Register Blueprints
# ---------------------------
from routes.auth import auth
app.register_blueprint(auth, url_prefix="/auth")

from routes.admin import admin
app.register_blueprint(admin)

from routes.alumni import alumni
app.register_blueprint(alumni)

from routes.placement import placement
app.register_blueprint(placement)

from routes.student import student
app.register_blueprint(student)

from routes.faculty import faculty
app.register_blueprint(faculty)

# ---------------------------
# Template Filter
# ---------------------------
@app.template_filter("datetime")
def format_datetime(value, format="%d %b %Y, %I:%M %p"):
    return format_datetime_local(value, format)

# ---------------------------
# Sidebar Context Processor
# ---------------------------
@app.context_processor
def sidebar_counts():
    try:
        from models.announcement import Announcement
        from models.student import Student
        from models.faculty import Faculty
        from models.job import Job
        from models.event import Event
        from models.seminar import Seminar
        from models.alumni import Alumni
        from models.guidance import Guidance

        from utils.user_role_enum import UserRole
        from utils.timezone_helper import get_utc_now
        from sqlalchemy import and_

        current_time = get_utc_now()

        counts = {
            "total_announcements": Announcement.query.count(),
            "total_students": Student.query.count(),
            "total_faculty": Faculty.query.count(),
            "total_jobs": Job.query.filter(Job.is_verified == True).count(),
            "total_events": Event.query.count(),
            "total_seminars": Seminar.query.filter(Seminar.date >= current_time).count(),
            "total_alumni": Alumni.query.count(),
            "total_guidance": Guidance.query.count(),
            "faculty_students": 0,
            "faculty_alumni": 0,
        }

        if has_request_context() and current_user.is_authenticated:

            role_value = (
                current_user.role.value
                if hasattr(current_user.role, "value")
                else str(current_user.role)
            )

            # Student-specific seminars
            if role_value == UserRole.STUDENT.value:
                student_profile = Student.query.filter_by(user_id=current_user.id).first()
                if student_profile:
                    counts["total_seminars"] = Seminar.query.filter(
                        and_(
                            Seminar.department == student_profile.department,
                            Seminar.date >= current_time
                        )
                    ).count()

            # Faculty-specific counts
            elif role_value == UserRole.FACULTY.value:
                faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
                if faculty_profile:
                    faculty_dept = faculty_profile.department.display_name

                    counts["faculty_students"] = Student.query.filter_by(
                        department=faculty_dept
                    ).count()

                    counts["faculty_alumni"] = Alumni.query.filter_by(
                        department=faculty_dept
                    ).count()

                    counts["total_seminars"] = Seminar.query.filter(
                        and_(
                            Seminar.department == faculty_dept,
                            Seminar.date >= current_time
                        )
                    ).count()

        return counts

    except Exception as e:
        print("Sidebar count error:", e)

        return {
            "total_announcements": 0,
            "total_students": 0,
            "total_faculty": 0,
            "total_jobs": 0,
            "total_events": 0,
            "total_seminars": 0,
            "total_alumni": 0,
            "total_guidance": 0,
            "faculty_students": 0,
            "faculty_alumni": 0,
        }

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/login-page")
def login_page():
    return redirect(url_for("auth.login"))


@app.route("/health")
def health():
    return "OK"

# ---------------------------
# Run Locally
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)