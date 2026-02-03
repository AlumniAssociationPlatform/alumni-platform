"""
Timezone helper utilities for handling UTC datetime conversion to local timezone.
All timestamps are stored in UTC in the database, but can be displayed in local timezone when needed.
"""

from datetime import datetime
import pytz
from flask import current_app


def get_local_timezone():
    """
    Get the local timezone configured in the application.
    
    Returns:
        pytz timezone object for the configured local timezone
    """
    tz_name = getattr(current_app.config, 'TIMEZONE_LOCAL', 'Asia/Kolkata')
    try:
        return pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone name is invalid
        return pytz.UTC


def get_utc_timezone():
    """
    Get the UTC timezone.
    
    Returns:
        pytz UTC timezone object
    """
    return pytz.UTC


def convert_utc_to_local(utc_datetime):
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_datetime: A datetime object in UTC (as stored in the database)
        
    Returns:
        A datetime object in the local timezone, or None if input is None
    """
    if utc_datetime is None:
        return None
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.UTC.localize(utc_datetime)
    elif utc_datetime.tzinfo != pytz.UTC:
        # If it has a timezone but it's not UTC, convert it to UTC first
        utc_datetime = utc_datetime.astimezone(pytz.UTC)
    
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


def get_utc_now():
    """
    Get current UTC time as a timezone-aware datetime.
    
    Returns:
        Current UTC datetime with UTC timezone info
    """
    return datetime.now(tz=pytz.UTC)


def get_local_now():
    """
    Get current time in the configured local timezone.
    
    Returns:
        Current datetime in local timezone with timezone info
    """
    local_tz = get_local_timezone()
    return datetime.now(tz=local_tz)


def format_datetime_local(datetime_obj, format_string="%d %b %Y, %I:%M %p"):
    """
    Format a UTC datetime object to a string in local timezone.
    
    Args:
        datetime_obj: A datetime object (assumed to be UTC if naive)
        format_string: The format string for strftime (default: "01 Jan 2024, 01:30 PM")
        
    Returns:
        Formatted datetime string in local timezone, or empty string if None
    """
    if datetime_obj is None:
        return ""
    
    local_datetime = convert_utc_to_local(datetime_obj)
    return local_datetime.strftime(format_string)


def get_datetime_for_display(datetime_obj):
    """
    Get a datetime object converted to local timezone for display purposes.
    This is a simple wrapper around convert_utc_to_local.
    
    Args:
        datetime_obj: A datetime object in UTC (as stored in the database)
        
    Returns:
        A datetime object in the local timezone for display
    """
    return convert_utc_to_local(datetime_obj)
