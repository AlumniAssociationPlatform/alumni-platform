from extensions import db

class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    
    # Recommendation Content
    recommendation_text = db.Column(db.Text, nullable=False)
    
    # Timestamps
    # Note: db.func.now() uses MySQL's current_timestamp, which is set to UTC in config
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    student = db.relationship("Student", backref="recommendations")
    job = db.relationship("Job", backref="recommendations")
    faculty = db.relationship("Faculty", backref="recommendations")
