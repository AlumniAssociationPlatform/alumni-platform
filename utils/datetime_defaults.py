"""
Utility functions to provide consistent UTC datetime defaults for database models.

All timestamps in the database should be stored in UTC.
Use these functions as the default callable for datetime columns.
"""

from datetime import datetime
from utils.timezone_helper import get_utc_now


def utc_now():
    """
    Get current UTC time for use as a default in database models.
    
    This is used instead of datetime.utcnow() to ensure timezone-aware datetimes.
    
    Returns:
        Current UTC datetime with timezone info
        
    Example:
        created_at = db.Column(db.DateTime, default=utc_now)
    """
    return get_utc_now()


def utc_now_func():
    """
    Alternative name for utc_now() for consistency with naming conventions.
    Use this if you prefer explicit function naming.
    """
    return get_utc_now()
