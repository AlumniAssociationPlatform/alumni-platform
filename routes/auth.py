from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Alumni, Student, Faculty
from models.faculty import Department
from utils.user_role_enum import UserRole
from utils.alumni_id_generator import generate_alumni_id
import os
from datetime import datetime
import uuid

auth = Blueprint("auth", __name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_photo(file):
    """Save profile photo and return the relative path"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError("Invalid file format. Only PNG, JPG, JPEG, and WEBP allowed")
    
    if file.content_length and file.content_length > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 1 MB limit")
    
    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Generate unique filename
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"profile_{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Save file
    file.save(filepath)
    
    # Return relative path for database storage
    return f"uploads/{unique_filename}"

# =========================
# REGISTER
# =========================
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            role_value = request.form.get("role")

            if not email or not password or not role_value:
                return {"status": "error", "message": "Required fields missing"}, 400

            # Validate role
            try:
                role = UserRole(role_value)
            except ValueError:
                return {"status": "error", "message": "Invalid role"}, 400

            if User.query.filter_by(email=email).first():
                return {"status": "error", "message": "Email already registered"}, 400

            first = request.form.get("first_name", "")
            last = request.form.get("last_name", "")
            name = (first + " " + last).strip() or email

            # Handle profile photo
            profile_photo_path = None
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename != '':
                    try:
                        profile_photo_path = save_profile_photo(file)
                    except ValueError as e:
                        return {"status": "error", "message": str(e)}, 400

            user = User(
                name=name,
                email=email,
                role=role,
                password_hash=generate_password_hash(password),
                is_approved=False,
                profile_photo=profile_photo_path
            )

            db.session.add(user)
            db.session.flush()  # get user.id

            # Role-based profile table
            if role == UserRole.STUDENT:
                db.session.add(Student(
                    user_id=user.id,
                    student_id=request.form.get("gr_no"),
                    department=request.form.get("department"),
                    batch_year=request.form.get("batch_year"),
                    skills=request.form.get("skills"),
                    phone_number=request.form.get("phone_number"),
                    linkedin_profile=request.form.get("student_linkedin_profile"),
                ))

            elif role == UserRole.ALUMNI:
                alumni_id = generate_alumni_id()
                db.session.add(Alumni(
                    user_id=user.id,
                    alumni_id=alumni_id,
                    department=request.form.get("alumni_department"),
                    batch_year=request.form.get("passout_year"),
                    current_company=request.form.get("current_company"),
                    current_role=request.form.get("designation"),
                    linkedin_profile=request.form.get("alumni_linkedin_profile"),
                    phone_number=request.form.get("alumni_phone_number"),
                ))

            elif role == UserRole.FACULTY:
                faculty_dept_str = request.form.get("faculty_department", "").strip()
                # Department display names to enum mapping
                dept_mapping = {
                    "Computer Engineering": "COMPUTER_ENGINEERING",
                    "IT Engineering": "IT_ENGINEERING",
                    "Electrical Engineering": "ELECTRICAL_ENGINEERING",
                    "Civil Engineering": "CIVIL_ENGINEERING",
                    "Mechanical Engineering": "MECHANICAL_ENGINEERING",
                }
                
                if faculty_dept_str not in dept_mapping:
                    db.session.rollback()
                    return {"status": "error", "message": "Invalid department selected"}, 400
                
                enum_key = dept_mapping[faculty_dept_str]
                faculty_dept = Department[enum_key]
                
                db.session.add(Faculty(
                    user_id=user.id,
                    faculty_id=request.form.get("faculty_id"),
                    department=faculty_dept,
                    designation=request.form.get("faculty_designation"),
                    phone_number=request.form.get("faculty_phone_number"),
                    linkedin_profile=request.form.get("faculty_linkedin_profile"),
                ))

            db.session.commit()

            return {
                "status": "success",
                "message": "Registration successful. Await admin approval."
            }

        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": str(e)}, 500

    return render_template("auth/register.html")

# =========================
# LOGIN
# =========================
@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login"))

    if request.method == "GET":
        return render_template("auth/login.html")

    data = request.get_json(silent=True) if request.is_json else request.form

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid email or password"}), 401

    if not user.is_approved:
        return jsonify({"message": "Account pending admin approval"}), 403

    if user.is_blocked:
        return jsonify({"message": "Account is blocked, please contact administrator"}), 403

    login_user(user)
    session["user_id"] = user.id
    session["role"] = user.role.value

    return jsonify({
        "status": "success",
        "message": "Logged In Successfully",
        "redirect": url_for("auth.post_login")
    })

# =========================
# UPDATE PROFILE PHOTO
# =========================
@auth.route("/update-profile-photo", methods=["POST"])
@login_required
def update_profile_photo():
    """Update user's profile photo"""
    try:
        if 'profile_photo' not in request.files:
            return {"status": "error", "message": "No file provided"}, 400
        
        file = request.files['profile_photo']
        
        if not file or file.filename == '':
            return {"status": "error", "message": "No file selected"}, 400
        
        # Validate and save the file
        try:
            profile_photo_path = save_profile_photo(file)
        except ValueError as e:
            return {"status": "error", "message": str(e)}, 400
        
        # Update user's profile photo in database
        old_photo = current_user.profile_photo
        current_user.profile_photo = profile_photo_path
        db.session.commit()
        
        # Delete old photo if it exists
        if old_photo:
            try:
                old_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', old_photo)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except Exception as e:
                # Log error but don't fail the request
                print(f"Error deleting old photo: {e}")
        
        return {
            "status": "success",
            "message": "Profile photo updated successfully",
            "profile_photo_url": url_for('static', filename=profile_photo_path)
        }
    
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 500

# =========================
# ROLE BASED REDIRECT
# =========================
@auth.route("/post-login")
@login_required
def post_login():
    role = current_user.role.value

    if role == UserRole.INSTITUTE.value:
        return redirect(url_for("admin.dashboard"))
    elif role == UserRole.STUDENT.value:
        return redirect(url_for("student.dashboard"))
    elif role == UserRole.ALUMNI.value:
        return redirect(url_for("alumni.dashboard"))
    elif role == UserRole.FACULTY.value:
        return redirect(url_for("faculty.dashboard"))
    elif role == UserRole.PLACEMENT.value:
        # Placement cell users go to the placement cell dashboard
        return redirect(url_for("placement.dashboard"))
    else:
        return redirect(url_for("auth.login"))

# =========================
# LOGOUT
# =========================
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.login"))
