from extensions import db
from utils.datetime_defaults import utc_now

class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    # Basic Information
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Job Details
    job_type = db.Column(db.String(50), nullable=False)  # 'Job', 'Internship', 'Both'
    eligibility = db.Column(db.String(255))
    department = db.Column(db.String(100))
    
    # Additional Fields
    location = db.Column(db.String(150))
    salary_range = db.Column(db.String(100))
    application_deadline = db.Column(db.Date)
    apply_link = db.Column(db.String(500))
    
    # Contact Information
    contact_email = db.Column(db.String(150))
    contact_phone = db.Column(db.String(20))
    company_website = db.Column(db.String(500))  # Company website URL
    
    # Job Poster Image (Optional)
    job_poster = db.Column(db.String(500))  # Store filename/path for optional job poster image

    # Tracking Information
    posted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    poster = db.relationship("User", backref="posted_jobs")
