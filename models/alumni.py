from extensions import db
from datetime import datetime

class Alumni(db.Model):
    __tablename__ = "alumni"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    alumni_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)

    current_company = db.Column(db.String(150))
    current_role = db.Column(db.String(100))
    linkedin_profile = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref(
        "alumni_profile",
        uselist=False,
        cascade="all, delete"
    ))
