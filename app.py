from flask import Flask, render_template
from flask_migrate import Migrate
from config import Config
from extensions import db, login_manager
from flask import redirect, url_for, has_request_context
from flask_login import current_user
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

migrate = Migrate(app, db)

# Import models AFTER db init
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints AFTER everything
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

@app.template_filter("datetime")
def format_datetime(value, format="%d %b %Y, %I:%M %p"):
    if value is None:
        return ""
    return value.strftime(format)

# Context processor for sidebar counts
@app.context_processor
def sidebar_counts():
    from models.announcement import Announcement
    from models.student import Student
    from models.faculty import Faculty
    from models.job import Job
    from models.event import Event
    from models.seminar import Seminar
    from models.alumni import Alumni
    from models.guidance import Guidance
    from utils.user_role_enum import UserRole
    from datetime import datetime
    from sqlalchemy import and_
    
    try:
        # Get current time for filtering upcoming seminars
        current_time = datetime.utcnow()
        
        counts = {
            'total_announcements': Announcement.query.count(),
            'total_students': Student.query.count(),
            'total_faculty': Faculty.query.count(),
            'total_jobs': Job.query.filter(Job.is_verified == True).count(),
            'total_events': Event.query.count(),
            'total_seminars': Seminar.query.filter(Seminar.date >= current_time).count(),
            'total_alumni': Alumni.query.count(),
            'total_guidance': Guidance.query.count(),
            'faculty_students': 0,
            'faculty_alumni': 0,
        }
        
        # If current user is authenticated, add user-specific counts
        if has_request_context() and current_user and current_user.is_authenticated:
            role_value = (
                current_user.role.value
                if hasattr(current_user.role, "value")
                else str(current_user.role)
            )
            
            # For students, filter seminars by their department
            if role_value == UserRole.STUDENT.value:
                student_profile = Student.query.filter_by(user_id=current_user.id).first()
                if student_profile:
                    counts['total_seminars'] = Seminar.query.filter(
                        and_(
                            Seminar.department == student_profile.department,
                            Seminar.date >= current_time
                        )
                    ).count()
            
            # For faculty, add department-specific counts
            elif role_value == UserRole.FACULTY.value:
                faculty_profile = Faculty.query.filter_by(user_id=current_user.id).first()
                if faculty_profile:
                    # Get faculty department display name
                    # Faculty.department is an Enum, so we need to use display_name
                    faculty_dept = faculty_profile.department.display_name
                    counts['faculty_students'] = Student.query.filter_by(department=faculty_dept).count()
                    counts['faculty_alumni'] = Alumni.query.filter_by(department=faculty_dept).count()
                    # Filter seminars by faculty department as well
                    counts['total_seminars'] = Seminar.query.filter(
                        and_(
                            Seminar.department == faculty_dept,
                            Seminar.date >= current_time
                        )
                    ).count()
        
        return counts
    except Exception as e:
        # In case of database errors, return 0 for all
        print(f"Error in sidebar_counts: {str(e)}")
        return {
            'total_announcements': 0,
            'total_students': 0,
            'total_faculty': 0,
            'total_jobs': 0,
            'total_events': 0,
            'total_seminars': 0,
            'total_alumni': 0,
            'total_guidance': 0,
            'faculty_students': 0,
            'faculty_alumni': 0,
        }

@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/login-page")
def login_page():
    return redirect(url_for("auth.login"))
