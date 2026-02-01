from extensions import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)

    # Report type: 'user_statistics', 'job_analytics', 'event_summary', 'alumni_network', 'placement_stats'
    report_type = db.Column(db.String(100), nullable=False)

    # Title of the report
    title = db.Column(db.String(255), nullable=False)

    # Description/summary of report
    description = db.Column(db.Text)

    # Admin who generated the report
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Report metadata (filters, parameters used)
    filters = db.Column(db.Text)  # JSON string

    # Report data (in JSON or summary format)
    data = db.Column(db.Text)  # JSON

    # Status: draft, completed, archived
    status = db.Column(db.String(50), default='completed')

    # Date range for the report
    report_from = db.Column(db.DateTime)
    report_to = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    generator = db.relationship("User", backref="generated_reports")

    def __repr__(self):
        return f"<Report {self.title} ({self.report_type})>"
