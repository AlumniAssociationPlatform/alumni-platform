"""
Timezone helper utilities for handling UTC datetime conversion to local timezone.
All timestamps are stored in UTC in the database, but can be displayed in local timezone when needed.
"""

from datetime import datetime
import pytz
from flask import current_app


def get_local_timezone():
    """Get the local timezone configured in the application."""
    # You can configure this in config.py as TIMEZONE_LOCAL
    # Default to UTC
    tz_name = getattr(current_app.config, 'TIMEZONE_LOCAL', 'Asia/Kolkata')  # Change to your timezone
    return pytz.timezone(tz_name)


def convert_utc_to_local(utc_datetime):
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_datetime: A datetime object in UTC (as stored in the database)
        
    Returns:
        A datetime object in the local timezone, or the original if it's None
    """
    if utc_datetime is None:
        return None
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.UTC.localize(utc_datetime)
    
    # Convert to local timezone
    local_tz = get_local_timezone()
    local_datetime = utc_datetime.astimezone(local_tz)
    
    return local_datetime


def convert_local_to_utc(local_datetime):
    """
    Convert local datetime to UTC for storage in the database.
    
    Args:
        local_datetime: A datetime object in local timezone
        
    Returns:
        A datetime object in UTC
    """
    if local_datetime is None:
        return None
    
    local_tz = get_local_timezone()
    
    # If naive, assume it's in local timezone
    if local_datetime.tzinfo is None:
        local_datetime = local_tz.localize(local_datetime)
    
    # Convert to UTC
    utc_datetime = local_datetime.astimezone(pytz.UTC)
    
    return utc_datetime


def format_datetime_local(datetime_obj, format_string="%d %b %Y, %I:%M %p"):
    """
    Format a UTC datetime object to a string in local timezone.
    
    Args:
        datetime_obj: A datetime object (assumed to be UTC if naive)
        format_string: The format string for strftime
        
    Returns:
        Formatted datetime string in local timezone
    """
    if datetime_obj is None:
        return ""
    
    local_datetime = convert_utc_to_local(datetime_obj)
    return local_datetime.strftime(format_string)
