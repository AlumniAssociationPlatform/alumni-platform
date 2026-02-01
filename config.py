import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "alumni-portal-secret-key")

    DB_USER = os.getenv("MYSQL_USER")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
    DB_HOST = os.getenv("MYSQL_HOST")
    DB_NAME = os.getenv("MYSQL_DB")
    DB_PORT = os.getenv("MYSQL_PORT", 3306)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # File upload configuration
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')