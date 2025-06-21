from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    AI_CATEGORIZATION = "AI_CATEGORIZATION"
    AI_COUNTERPARTY_IDENTIFICATION = "AI_COUNTERPARTY_IDENTIFICATION"


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(SQLAlchemyEnum(JobType), nullable=False)
    status = Column(SQLAlchemyEnum(JobStatus), default=JobStatus.PENDING, nullable=False)

    # Related entities
    uploaded_file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True)
    uploaded_file = relationship("UploadedFile")

    # Job execution data
    progress = Column(JSONB, default=dict, nullable=False)
    result = Column(JSONB, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Retry mechanism
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    def __repr__(self):
        return f"<BackgroundJob(id={self.id}, type={self.job_type}, status={self.status})>"

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (completed, failed, or cancelled)"""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries

    def mark_started(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, result: dict = None) -> None:
        """Mark job as completed with optional result"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if result:
            self.result = result

    def mark_failed(self, error_message: str = None) -> None:
        """Mark job as failed with optional error message"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if error_message:
            self.error_message = error_message

    def increment_retry(self) -> None:
        """Increment retry count and reset status to pending"""
        if self.can_retry:
            self.retry_count += 1
            self.status = JobStatus.PENDING
            self.started_at = None
            self.completed_at = None
