import os

class Config:
    SECRET_KEY = "alumni-portal-secret-key"

    DB_USER = "root"
    DB_PASSWORD = "12345"
    DB_HOST = "localhost"
    DB_NAME = "alumni_portal_db"

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # File upload configuration
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')