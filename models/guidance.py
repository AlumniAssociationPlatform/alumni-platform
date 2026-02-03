from extensions import db
from utils.datetime_defaults import utc_now

class Guidance(db.Model):
    __tablename__ = "guidances"

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    alumni_id = db.Column(
        db.Integer,
        db.ForeignKey("alumni.id", ondelete="CASCADE"),
        nullable=False
    )
    
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=True  # Optional - guidance is for all students
    )
    
    # Guidance Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(
        db.String(50), 
        nullable=False,
        default="Career"
    )  # Career, Technical, Personal, Academic, Placement
    
    # Status & Timestamps
    status = db.Column(
        db.String(20), 
        nullable=False, 
        default="active"
    )  # active, completed, archived
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Additional fields
    duration_weeks = db.Column(db.Integer, default=4)  # Expected duration in weeks
    meeting_frequency = db.Column(db.String(50))  # Weekly, Bi-weekly, Monthly
    preferred_method = db.Column(db.String(50), default="Virtual")  # Virtual, In-person, Both
    
    # Relationships
    alumni = db.relationship(
        "Alumni", 
        backref=db.backref("guidances_given", cascade="all, delete")
    )
    
    student = db.relationship(
        "Student",
        backref=db.backref("guidances_received", cascade="all, delete")
    )
    
    guidance_sessions = db.relationship(
        "GuidanceSession",
        backref=db.backref("guidance", cascade="all, delete"),
        lazy="dynamic"
    )

    guidance_questions = db.relationship(
        "GuidanceQuestion",
        backref=db.backref("guidance", cascade="all, delete"),
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Guidance {self.title} - {self.id}>"


class GuidanceSession(db.Model):
    __tablename__ = "guidance_sessions"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key
    guidance_id = db.Column(
        db.Integer,
        db.ForeignKey("guidances.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Session Details
    session_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    feedback = db.Column(db.Text)
    
    # Meeting Details
    meeting_link = db.Column(db.String(500))  # For virtual meetings
    location = db.Column(db.String(200))  # For in-person meetings
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Status
    status = db.Column(
        db.String(20),
        nullable=False,
        default="scheduled"
    )  # scheduled, completed, cancelled, rescheduled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GuidanceSession {self.id} - {self.session_date}>"


class GuidanceQuestion(db.Model):
    __tablename__ = "guidance_questions"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    guidance_id = db.Column(
        db.Integer,
        db.ForeignKey("guidances.id", ondelete="CASCADE"),
        nullable=False
    )
    
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Question Details
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    
    # Status
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )  # pending, answered, resolved
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship(
        "User",
        backref=db.backref("guidance_questions", cascade="all, delete")
    )
    
    def __repr__(self):
        return f"<GuidanceQuestion {self.id} - {self.status}>"


class GuidanceEnrollment(db.Model):
    __tablename__ = "guidance_enrollments"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    guidance_id = db.Column(
        db.Integer,
        db.ForeignKey("guidances.id", ondelete="CASCADE"),
        nullable=False
    )
    
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Status & Timestamps
    status = db.Column(
        db.String(20),
        nullable=False,
        default="active"
    )  # active, completed, withdrew
    
    enrolled_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (
        db.UniqueConstraint('guidance_id', 'student_id', name='unique_guidance_enrollment'),
    )
    
    # Relationships
    guidance = db.relationship(
        "Guidance",
        backref=db.backref("enrollments", cascade="all, delete", lazy="dynamic")
    )
    
    student = db.relationship(
        "Student",
        backref=db.backref("guidance_enrollments", cascade="all, delete")
    )
    
    def __repr__(self):
        return f"<GuidanceEnrollment {self.guidance_id} - {self.student_id}>"
