"""
Sample Report Generation Script
This script demonstrates how to use the ReportGenerator utility
"""

from app import app
from models.report import Report
from utils.report_generator import ReportGenerator
from extensions import db
from models.user import User

def demonstrate_report_generation():
    """Demonstrate all available report types"""
    
    with app.app_context():
        # Get or create an admin user for testing
        admin_user = User.query.filter_by(role='INSTITUTE').first()
        if not admin_user:
            print("No admin user found. Please create one first.")
            return
        
        print("=" * 60)
        print("ALUMNI PORTAL - REPORT GENERATION DEMO")
        print("=" * 60)
        
        # Get all available report types
        report_types = ReportGenerator.get_all_report_types()
        print(f"\nAvailable Report Types ({len(report_types)}):")
        for report_key, report_name in report_types:
            print(f"  • {report_key}: {report_name}")
        
        print("\n" + "=" * 60)
        
        # Example 1: Generate User Statistics Report
        print("\n[1] Generating User Statistics Report...")
        try:
            user_stats_data = ReportGenerator.generate_user_statistics_report(days=30)
            print("✓ User Statistics Report Generated")
            print(f"  Summary: {user_stats_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Example 2: Generate Alumni Network Report
        print("\n[2] Generating Alumni Network Report...")
        try:
            alumni_data = ReportGenerator.generate_alumni_network_report()
            print("✓ Alumni Network Report Generated")
            print(f"  Summary: {alumni_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Example 3: Generate Job Analytics Report
        print("\n[3] Generating Job Analytics Report...")
        try:
            job_data = ReportGenerator.generate_job_analytics_report(days=30)
            print("✓ Job Analytics Report Generated")
            print(f"  Summary: {job_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Example 4: Generate Event Summary Report
        print("\n[4] Generating Event Summary Report...")
        try:
            event_data = ReportGenerator.generate_event_summary_report(days=90)
            print("✓ Event Summary Report Generated")
            print(f"  Summary: {event_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Example 5: Generate Placement Statistics Report
        print("\n[5] Generating Placement Statistics Report...")
        try:
            placement_data = ReportGenerator.generate_placement_statistics_report()
            print("✓ Placement Statistics Report Generated")
            print(f"  Summary: {placement_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        # Example 6: Generate Announcements Report
        print("\n[6] Generating Announcements Report...")
        try:
            announcement_data = ReportGenerator.generate_announcement_report(days=30)
            print("✓ Announcements Report Generated")
            print(f"  Summary: {announcement_data['summary']}")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        print("\n" + "=" * 60)
        print("All sample reports generated successfully!")
        print("=" * 60)
        
        # Show how to save a report to database
        print("\nSaving a report to database...")
        try:
            report_data = ReportGenerator.generate_user_statistics_report(days=30)
            
            report = Report(
                report_type='user_statistics',
                title='Monthly User Statistics Report',
                description='Sample report showing user statistics for the last 30 days',
                generated_by=admin_user.id,
                data=__import__('json').dumps(report_data),
                filters=__import__('json').dumps({'days': 30}),
                status='completed'
            )
            
            db.session.add(report)
            db.session.commit()
            
            print(f"✓ Report saved with ID: {report.id}")
            print(f"  Title: {report.title}")
            print(f"  Type: {report.report_type}")
            print(f"  Generated: {report.created_at}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error saving report: {e}")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    demonstrate_report_generation()
