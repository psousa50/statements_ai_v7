#!/usr/bin/env python3
"""
Background job processor script for cron execution.

This script processes pending background jobs as a backup to the
immediate processing triggered by uploads.

Usage:
    python scripts/process_background_jobs.py

Cron example (every 5 minutes):
    */5 * * * * cd /path/to/project && source .venv/bin/activate && python scripts/process_background_jobs.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.dependencies import get_dependencies
from app.workers.job_processor import process_pending_jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/background_jobs.log"),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the background job processor"""
    try:
        logger.info("Starting background job processor (cron mode)")

        # Get dependencies
        with get_dependencies() as (external, internal):
            # Process pending jobs
            processed_count = await process_pending_jobs(internal)

            if processed_count > 0:
                logger.info(
                    f"Background job processor completed successfully. Processed {processed_count} jobs."
                )
            else:
                logger.info("No pending jobs found.")

    except Exception as e:
        logger.error(f"Background job processor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
