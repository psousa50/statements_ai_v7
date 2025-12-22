from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(Text, nullable=False)
    content = Column(LargeBinary, nullable=False)
    file_type = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class FileAnalysisMetadata(Base):
    __tablename__ = "file_analysis_metadata"
    __table_args__ = (UniqueConstraint("file_hash", "account_id", name="file_analysis_metadata_file_hash_account_id_key"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_hash = Column(Text, nullable=False, index=True)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
    )
    column_mapping = Column(JSONB, nullable=False)
    header_row_index = Column(Integer, nullable=False)
    data_start_row_index = Column(Integer, nullable=False)
    row_filters = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account = relationship("Account")
