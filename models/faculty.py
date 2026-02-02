from extensions import db
import enum
from datetime import datetime

class Department(enum.Enum):
    """Department enum for faculty and students"""
    COMPUTER_ENGINEERING = "COMPUTER_ENGINEERING"
    IT_ENGINEERING = "IT_ENGINEERING"
    ELECTRICAL_ENGINEERING = "ELECTRICAL_ENGINEERING"
    CIVIL_ENGINEERING = "CIVIL_ENGINEERING"
    MECHANICAL_ENGINEERING = "MECHANICAL_ENGINEERING"
    
    @property
    def display_name(self):
        """Return human-readable department name"""
        names = {
            "COMPUTER_ENGINEERING": "Computer Engineering",
            "IT_ENGINEERING": "IT Engineering",
            "ELECTRICAL_ENGINEERING": "Electrical Engineering",
            "CIVIL_ENGINEERING": "Civil Engineering",
            "MECHANICAL_ENGINEERING": "Mechanical Engineering",
        }
        return names.get(self.value, self.value)

class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    faculty_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(
        db.Enum(Department),
        nullable=False
    )
    designation = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    linkedin_profile = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref(
        "faculty_profile",
        uselist=False,
        cascade="all, delete"
    ))
