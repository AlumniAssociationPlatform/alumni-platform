from models.job import Job
from config import Config
from extensions import db
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    cols = [c.name for c in Job.__table__.columns]
    print("Job table columns:")
    for col in cols:
        print(f"  - {col}")
    print(f"\nis_verified exists: {'is_verified' in cols}")
    print(f"is_active exists: {'is_active' in cols}")
    
    # Also check actual data
    total_jobs = Job.query.count()
    verified_jobs = Job.query.filter(Job.is_verified == True).count()
    active_jobs = Job.query.filter(Job.is_active == True).count()
    verified_active_jobs = Job.query.filter(Job.is_verified == True, Job.is_active == True).count()
    
    print(f"\nDatabase Statistics:")
    print(f"Total jobs: {total_jobs}")
    print(f"Verified jobs: {verified_jobs}")
    print(f"Active jobs: {active_jobs}")
    print(f"Verified AND Active jobs: {verified_active_jobs}")
