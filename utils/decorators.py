from extensions import db

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    student_id = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    skills = db.Column(db.Text)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # relationship
    user = db.relationship("User", backref=db.backref(
        "student_profile",
        uselist=False,
        cascade="all, delete"
    ))
