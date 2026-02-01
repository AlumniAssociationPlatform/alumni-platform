import json
from datetime import datetime, timedelta
from models.user import User
from models.alumni import Alumni
from models.job import Job
from models.job_application import JobApplication
from models.event import Event
from models.event_participant import EventParticipant
from models.announcement import Announcement
from utils.user_role_enum import UserRole
from extensions import db


class ReportGenerator:
    """Utility class for generating various reports"""

    @staticmethod
    def generate_user_statistics_report(days=30):
        """Generate user statistics report for the last N days"""
        from_date = datetime.utcnow() - timedelta(days=days)

        total_users = User.query.count()
        alumni_count = User.query.filter_by(role=UserRole.ALUMNI).count()
        student_count = User.query.filter_by(role=UserRole.STUDENT).count()
        faculty_count = User.query.filter_by(role=UserRole.FACULTY).count()
        admin_count = User.query.filter_by(role=UserRole.INSTITUTE).count()

        new_users = User.query.filter(User.created_at >= from_date).count()
        approved_users = User.query.filter_by(is_approved=True).count()
        pending_approvals = User.query.filter_by(is_approved=False).count()
        blocked_users = User.query.filter_by(is_blocked=True).count()

        data = {
            "summary": {
                "total_users": total_users,
                "approved_users": approved_users,
                "pending_approvals": pending_approvals,
                "blocked_users": blocked_users,
                "new_users_last_days": new_users,
            },
            "breakdown_by_role": {
                "alumni": alumni_count,
                "students": student_count,
                "faculty": faculty_count,
                "administrators": admin_count,
            },
            "approval_status": {
                "approved": approved_users,
                "pending": pending_approvals,
                "blocked": blocked_users,
            },
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def generate_alumni_network_report(department=None):
        """Generate alumni network report with statistics"""
        query = Alumni.query

        if department:
            query = query.filter_by(department=department)

        alumni_list = query.all()
        total_alumni = len(alumni_list)

        # Batch year statistics
        batch_stats = {}
        employed_count = 0
        company_stats = {}

        for alumni in alumni_list:
            # Batch year count
            batch_year = alumni.batch_year
            batch_stats[batch_year] = batch_stats.get(batch_year, 0) + 1

            # Employment status
            if alumni.current_company:
                employed_count += 1
                company = alumni.current_company
                company_stats[company] = company_stats.get(company, 0) + 1

        # Get department statistics
        dept_stats = db.session.query(
            Alumni.department, db.func.count(Alumni.id)
        ).group_by(Alumni.department).all()

        department_breakdown = {dept: count for dept, count in dept_stats}

        # Top companies
        top_companies = sorted(
            company_stats.items(), key=lambda x: x[1], reverse=True
        )[:10]

        data = {
            "summary": {
                "total_alumni": total_alumni,
                "employed_alumni": employed_count,
                "employment_rate": round(
                    (employed_count / total_alumni * 100) if total_alumni > 0 else 0, 2
                ),
                "departments": len(department_breakdown),
            },
            "batch_year_statistics": batch_stats,
            "department_breakdown": department_breakdown,
            "top_companies": dict(top_companies),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def generate_job_analytics_report(days=30):
        """Generate job posting and application analytics"""
        from_date = datetime.utcnow() - timedelta(days=days)

        total_jobs = Job.query.count()
        active_jobs = Job.query.filter_by(is_verified=True).count()
        pending_jobs = Job.query.filter_by(is_verified=False).count()

        recent_jobs = Job.query.filter(Job.created_at >= from_date).count()
        total_applications = JobApplication.query.count()
        recent_applications = JobApplication.query.filter(
            JobApplication.created_at >= from_date
        ).count()

        # Company statistics
        company_stats = db.session.query(
            Job.company, db.func.count(Job.id)
        ).group_by(Job.company).all()

        # Top companies by job postings
        top_companies = sorted(
            [(comp, count) for comp, count in company_stats if comp],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Job type statistics
        job_type_stats = db.session.query(
            Job.job_type, db.func.count(Job.id)
        ).filter(Job.job_type.isnot(None)).group_by(Job.job_type).all()

        # Department-wise job statistics
        dept_stats = db.session.query(
            Job.department, db.func.count(Job.id)
        ).filter(Job.department.isnot(None)).group_by(Job.department).all()

        data = {
            "summary": {
                "total_job_postings": total_jobs,
                "verified_jobs": active_jobs,
                "pending_verification": pending_jobs,
                "new_jobs_last_days": recent_jobs,
                "total_applications": total_applications,
                "applications_last_days": recent_applications,
                "avg_applications_per_job": round(
                    (total_applications / total_jobs) if total_jobs > 0 else 0, 2
                ),
            },
            "top_companies": dict(top_companies),
            "job_type_breakdown": dict(job_type_stats),
            "department_job_postings": dict(dept_stats),
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def generate_event_summary_report(days=90):
        """Generate event and participation summary"""
        from_date = datetime.utcnow() - timedelta(days=days)

        total_events = Event.query.count()
        recent_events = Event.query.filter(Event.created_at >= from_date).count()

        # Events by department
        dept_events = db.session.query(
            Event.department, db.func.count(Event.id)
        ).group_by(Event.department).all()

        # Total participants
        total_participants = EventParticipant.query.count()

        # Participants by event
        event_participants = db.session.query(
            Event.title, db.func.count(EventParticipant.id)
        ).join(EventParticipant, Event.id == EventParticipant.event_id).group_by(Event.id, Event.title).all()

        # Top events by participation
        top_events = sorted(
            [(title, count) for title, count in event_participants if count],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        data = {
            "summary": {
                "total_events": total_events,
                "events_last_days": recent_events,
                "total_participants": total_participants,
                "avg_participants_per_event": round(
                    (total_participants / total_events) if total_events > 0 else 0, 2
                ),
            },
            "department_events": dict(dept_events),
            "top_events_by_participation": dict(top_events),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def generate_placement_statistics_report():
        """Generate placement and career statistics"""
        # Get all alumni profiles
        alumni_profiles = Alumni.query.all()

        employed = [a for a in alumni_profiles if a.current_company]
        unemployed = [a for a in alumni_profiles if not a.current_company]

        # Company distribution
        company_dist = {}
        for alumni in employed:
            company = alumni.current_company
            company_dist[company] = company_dist.get(company, 0) + 1

        # Role distribution
        role_dist = {}
        for alumni in employed:
            role = alumni.current_role or "Not Specified"
            role_dist[role] = role_dist.get(role, 0) + 1

        # Department statistics
        dept_stats = {}
        for alumni in alumni_profiles:
            dept = alumni.department
            if dept not in dept_stats:
                dept_stats[dept] = {"total": 0, "employed": 0, "rate": 0}
            dept_stats[dept]["total"] += 1
            if alumni in employed:
                dept_stats[dept]["employed"] += 1

        # Calculate employment rates
        for dept in dept_stats:
            total = dept_stats[dept]["total"]
            employed_count = dept_stats[dept]["employed"]
            dept_stats[dept]["rate"] = round(
                (employed_count / total * 100) if total > 0 else 0, 2
            )

        total_alumni = len(alumni_profiles)
        employed_count = len(employed)

        data = {
            "summary": {
                "total_alumni": total_alumni,
                "employed": employed_count,
                "unemployed": len(unemployed),
                "employment_rate": round(
                    (employed_count / total_alumni * 100) if total_alumni > 0 else 0, 2
                ),
            },
            "top_companies": dict(
                sorted(company_dist.items(), key=lambda x: x[1], reverse=True)[:15]
            ),
            "role_distribution": role_dist,
            "department_employment_stats": dept_stats,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def generate_announcement_report(days=30):
        """Generate announcement activity report"""
        from_date = datetime.utcnow() - timedelta(days=days)

        total_announcements = Announcement.query.count()
        recent_announcements = Announcement.query.filter(
            Announcement.created_at >= from_date
        ).count()

        # Announcements by creator
        creator_stats = db.session.query(
            User.name, db.func.count(Announcement.id)
        ).outerjoin(Announcement).group_by(Announcement.created_by).all()

        data = {
            "summary": {
                "total_announcements": total_announcements,
                "announcements_last_days": recent_announcements,
                "avg_announcements_per_day": round(
                    (recent_announcements / days) if days > 0 else 0, 2
                ),
            },
            "announcements_by_creator": dict(creator_stats),
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return data

    @staticmethod
    def get_all_report_types():
        """Return available report types"""
        return [
            ("user_statistics", "User Statistics Report"),
            ("alumni_network", "Alumni Network Report"),
            ("job_analytics", "Job Analytics Report"),
            ("event_summary", "Event Summary Report"),
            ("placement_stats", "Placement Statistics Report"),
            ("announcements", "Announcements Report"),
        ]

    @staticmethod
    def generate_report(report_type, **filters):
        """Main method to generate reports based on type"""
        if report_type == "user_statistics":
            days = filters.get("days", 30)
            return ReportGenerator.generate_user_statistics_report(days)
        elif report_type == "alumni_network":
            department = filters.get("department")
            return ReportGenerator.generate_alumni_network_report(department)
        elif report_type == "job_analytics":
            days = filters.get("days", 30)
            return ReportGenerator.generate_job_analytics_report(days)
        elif report_type == "event_summary":
            days = filters.get("days", 90)
            return ReportGenerator.generate_event_summary_report(days)
        elif report_type == "placement_stats":
            return ReportGenerator.generate_placement_statistics_report()
        elif report_type == "announcements":
            days = filters.get("days", 30)
            return ReportGenerator.generate_announcement_report(days)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
