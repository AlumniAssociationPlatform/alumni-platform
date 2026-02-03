"""
Script to fix naive datetime objects in existing Seminar records.
This converts any naive datetime objects to timezone-aware UTC datetimes.

Usage:
    python fix_seminar_datetimes.py
"""

import sys
import pytz
from app import app, db
from models.seminar import Seminar

def fix_seminar_datetimes():
    """
    Fix all naive datetime objects in Seminar records by converting them to UTC-aware datetimes.
    """
    with app.app_context():
        # Get all seminars
        seminars = Seminar.query.all()
        
        if not seminars:
            print("No seminars found in the database.")
            return
        
        fixed_count = 0
        
        for seminar in seminars:
            # Check if the date is naive (no timezone info)
            if seminar.date and seminar.date.tzinfo is None:
                # Convert naive datetime to UTC timezone-aware datetime
                seminar.date = pytz.UTC.localize(seminar.date)
                fixed_count += 1
                print(f"Fixed seminar '{seminar.title}' (ID: {seminar.id}) - Date: {seminar.date}")
        
        # Commit changes if any were made
        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"\n✓ Successfully fixed {fixed_count} seminar(s) with naive datetimes.")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error committing changes: {str(e)}")
                return False
        else:
            print("All seminars already have timezone-aware datetimes.")
        
        return True

if __name__ == "__main__":
    success = fix_seminar_datetimes()
    sys.exit(0 if success else 1)
