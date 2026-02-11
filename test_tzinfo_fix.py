"""
Test script to verify the tzinfo fix works correctly.
This tests that date objects can be handled properly in timezone conversion.
"""

from datetime import datetime, date
import pytz
from app import app
from utils.timezone_helper import convert_utc_to_local, format_datetime_local

def test_tzinfo_fixes():
    """Test the tzinfo fixes for date and datetime objects"""
    
    with app.app_context():
        print("Testing tzinfo fixes...\n")
        
        # Test 1: datetime object (should work as before)
        dt = datetime(2024, 2, 11, 10, 30, 0)
        print(f"Test 1 - Naive datetime: {dt}")
        try:
            result = convert_utc_to_local(dt)
            print(f"✓ convert_utc_to_local works: {result}\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # Test 2: date object (the fix addresses this)
        d = date(2024, 2, 11)
        print(f"Test 2 - Date object: {d}")
        try:
            result = convert_utc_to_local(d)
            print(f"✓ convert_utc_to_local works with date: {result}\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # Test 3: format_datetime_local with date (the actual error case)
        print(f"Test 3 - format_datetime_local with date:")
        try:
            result = format_datetime_local(d, "%d %b %Y")
            print(f"✓ format_datetime_local works with date: {result}\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # Test 4: format_datetime_local with datetime
        print(f"Test 4 - format_datetime_local with datetime:")
        try:
            result = format_datetime_local(dt, "%d %b %Y, %I:%M %p")
            print(f"✓ format_datetime_local works with datetime: {result}\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        # Test 5: None values
        print(f"Test 5 - None value:")
        try:
            result = format_datetime_local(None)
            print(f"✓ format_datetime_local handles None: '{result}'\n")
        except Exception as e:
            print(f"✗ Error: {e}\n")
        
        print("All tests completed!")

if __name__ == "__main__":
    test_tzinfo_fixes()
