from extensions import db
from utils.datetime_defaults import utc_now

class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    status = db.Column(db.String(50), default="applied")
    # applied, shortlisted, rejected, selected

    applied_at = db.Column(db.DateTime, default=utc_now)

    job = db.relationship("Job", backref="applications")
    student = db.relationship("User", backref="applications")
