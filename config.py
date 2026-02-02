import os
from datetime import timezone

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "alumni-portal-secret-key")

    DB_USER = os.getenv("MYSQLUSER")
    DB_PASSWORD = os.getenv("MYSQLPASSWORD")
    DB_HOST = os.getenv("MYSQLHOST")
    DB_NAME = os.getenv("MYSQLDATABASE")
    DB_PORT = os.getenv("MYSQLPORT", 3306)

    SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Timezone configuration for consistent handling across local and deployed instances
    # Use UTC for all database operations
    TIMEZONE = "UTC"
    SQLALCHEMY_ECHO = False
    
    # MySQL connection timezone configuration
    # This ensures MySQL interprets all times in UTC
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sql_mode": "STRICT_TRANS_TABLES",
        }
    }

    # File upload configuration
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')