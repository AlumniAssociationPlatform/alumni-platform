from extensions import db
from utils.datetime_defaults import utc_now

class Seminar(db.Model):
    __tablename__ = "seminars"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    speaker_name = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    
    # Faculty who created the seminar
    faculty_id = db.Column(
        db.Integer,
        db.ForeignKey("faculty.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Department for filtering (from faculty)
    department = db.Column(db.String(100), nullable=False)
    
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    faculty = db.relationship("Faculty", backref=db.backref("seminars", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date else None,
            'location': self.location,
            'speaker_name': self.speaker_name,
            'topic': self.topic,
            'faculty_name': self.faculty.user.name if self.faculty else None,
            'department': self.department,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
