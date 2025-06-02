#!/usr/bin/env python3
"""
Script to check the status of all background jobs.

Usage:
    python check_jobs_status.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.dependencies import get_dependencies


def check_jobs_status():
    """Check the status of all background jobs"""

    print("📋 Checking background jobs status...")

    with get_dependencies() as (external, internal):
        # Get all jobs
        all_jobs = internal.background_job_repository.get_all()

        if not all_jobs:
            print("✅ No background jobs found in database.")
            return

        print(f"📊 Found {len(all_jobs)} total jobs:")
        print()

        # Group by status
        status_counts = {}
        for job in all_jobs:
            status = job.status.value if hasattr(job.status, "value") else str(job.status)
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        # Show summary
        print("📈 Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count} jobs")
        print()

        # Show recent jobs in detail
        print("🔍 Recent jobs (last 10):")
        recent_jobs = sorted(all_jobs, key=lambda x: x.created_at, reverse=True)[:10]

        for job in recent_jobs:
            status = job.status.value if hasattr(job.status, "value") else str(job.status)
            job_type = job.job_type.value if hasattr(job.job_type, "value") else str(job.job_type)

            created = job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            started = job.started_at.strftime("%Y-%m-%d %H:%M:%S") if job.started_at else "Not started"
            completed = job.completed_at.strftime("%Y-%m-%d %H:%M:%S") if job.completed_at else "Not completed"

            print(f"  📄 Job {job.id}")
            print(f"     Type: {job_type}")
            print(f"     Status: {status}")
            print(f"     Created: {created}")
            print(f"     Started: {started}")
            print(f"     Completed: {completed}")
            if job.error_message:
                print(f"     Error: {job.error_message}")
            print()


if __name__ == "__main__":
    check_jobs_status()
