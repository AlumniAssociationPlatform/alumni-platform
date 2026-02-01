from extensions import db

class EventParticipant(db.Model):
    __tablename__ = "event_participants"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    registered_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", backref="event_registrations")
