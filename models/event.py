from extensions import db
from utils.datetime_defaults import utc_now

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date)
    department = db.Column(db.Text)  # Store as comma-separated values
    banner_image = db.Column(db.String(255), nullable=False)  # Compulsory
    pdf_file = db.Column(db.String(255))  # Optional

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=utc_now)

    creator = db.relationship("User", backref="events")
    participants = db.relationship("EventParticipant", backref="event", cascade="all, delete-orphan")
