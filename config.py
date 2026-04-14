import os
from datetime import timezone

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "alumni-portal-secret-key")

    DB_USER = os.getenv("MYSQLUSER", "root")
    DB_PASSWORD = os.getenv("MYSQLPASSWORD", "12345")
    DB_HOST = os.getenv("MYSQLHOST", "localhost")
    DB_NAME = os.getenv("MYSQLDATABASE", "alumni_portal_db")
    DB_PORT = os.getenv("MYSQLPORT", 3306)

    SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Timezone configuration for consistent handling across local and deployed instances
    # All timestamps are stored in UTC in the database
    TIMEZONE = "UTC"
    # Local timezone for displaying timestamps to users
    # Change this to match your local timezone (e.g., 'Asia/Kolkata', 'America/New_York')
    TIMEZONE_LOCAL = os.getenv("TIMEZONE_LOCAL", "Asia/Kolkata")
    SQLALCHEMY_ECHO = False
    
    # MySQL connection timezone configuration
    # This ensures MySQL interprets all times in UTC
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sql_mode": "STRICT_TRANS_TABLES",
            "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES', time_zone='+00:00'",
        },
        "pool_pre_ping": True,
    }

    # File upload configuration
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
