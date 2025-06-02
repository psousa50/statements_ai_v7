#!/usr/bin/env python3
"""
Script to reset stuck background jobs.

This script finds jobs that are stuck in IN_PROGRESS status for too long
and resets them back to PENDING so they can be processed again.

Usage:
    python reset_stuck_jobs.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.dependencies import get_dependencies
from app.domain.models.background_job import JobStatus


def reset_stuck_jobs():
    """Reset jobs that have been IN_PROGRESS for more than 30 minutes"""

    print("🔄 Checking for stuck background jobs...")

    with get_dependencies() as (external, internal):
        # Get all IN_PROGRESS jobs
        all_jobs = internal.background_job_repository.get_all()
        in_progress_jobs = [job for job in all_jobs if job.status == JobStatus.IN_PROGRESS]

        if not in_progress_jobs:
            print("✅ No IN_PROGRESS jobs found.")
            return

        print(f"📋 Found {len(in_progress_jobs)} IN_PROGRESS jobs:")

        now = datetime.now(timezone.utc)
        stuck_threshold = timedelta(minutes=30)  # Consider stuck if running for more than 30 minutes
        reset_count = 0

        for job in in_progress_jobs:
            # Calculate how long the job has been running
            if job.started_at:
                running_time = now - job.started_at
                status = "STUCK" if running_time > stuck_threshold else "RUNNING"
            else:
                # No started_at means it was never properly started
                running_time = now - job.created_at
                status = "STUCK (never started)"

            print(f"  🔍 Job {job.id[:8]}... ({job.job_type}) - {status} (running for {running_time})")

            # Reset stuck jobs
            if running_time > stuck_threshold:
                print(f"    🔄 Resetting job {job.id[:8]}... back to PENDING")

                # Reset job status
                job.status = JobStatus.PENDING
                job.started_at = None
                job.error_message = f"Reset from stuck IN_PROGRESS state after {running_time}"

                # Update in database
                internal.background_job_repository.update(job)
                reset_count += 1

        if reset_count > 0:
            print(f"✅ Reset {reset_count} stuck jobs back to PENDING status.")
            print("💡 Run the job processor again to process these jobs:")
            print("   python scripts/process_background_jobs.py")
        else:
            print("✅ No stuck jobs found to reset.")


if __name__ == "__main__":
    reset_stuck_jobs()
