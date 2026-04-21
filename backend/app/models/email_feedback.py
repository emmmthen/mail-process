from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmailMessage(Base):
    """邮件原始消息"""

    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(500), nullable=True, index=True)
    sender = Column(String(200), nullable=True, index=True)
    received_at = Column(DateTime, nullable=True, index=True)

    source_file_path = Column(String(500), nullable=True)
    source_file_hash = Column(String(128), nullable=True, index=True)
    source_type = Column(String(50), nullable=True, default="email")
    message_id = Column(String(200), nullable=True, index=True)

    raw_status = Column(String(50), nullable=False, default="received")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    artifacts = relationship(
        "EmailArtifact",
        back_populates="email_message",
        cascade="all, delete-orphan",
    )
    extraction_runs = relationship(
        "ExtractionRun",
        back_populates="email_message",
        cascade="all, delete-orphan",
    )


class EmailArtifact(Base):
    """清洗与重建后的邮件内容"""

    __tablename__ = "email_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False, index=True)

    cleaned_text = Column(Text, nullable=True)
    rebuilt_text = Column(Text, nullable=True)
    rebuilt_blocks_json = Column(JSON, nullable=True)
    extractable_status = Column(String(50), nullable=False, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    email_message = relationship("EmailMessage", back_populates="artifacts")
    extraction_runs = relationship(
        "ExtractionRun",
        back_populates="email_artifact",
        cascade="all, delete-orphan",
    )


class ExtractionRun(Base):
    """一次抽取运行记录"""

    __tablename__ = "extraction_runs"

    id = Column(Integer, primary_key=True, index=True)
    email_message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False, index=True)
    email_artifact_id = Column(Integer, ForeignKey("email_artifacts.id"), nullable=True, index=True)

    extract_mode = Column(String(50), nullable=False, default="auto")
    llm_input_snapshot = Column(Text, nullable=True)
    llm_output_json = Column(JSON, nullable=True)
    validation_result_json = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)

    run_status = Column(String(50), nullable=False, default="pending_review")
    committed_quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    email_message = relationship("EmailMessage", back_populates="extraction_runs")
    email_artifact = relationship("EmailArtifact", back_populates="extraction_runs")
    review_actions = relationship(
        "ReviewAction",
        back_populates="extraction_run",
        cascade="all, delete-orphan",
    )


class ReviewAction(Base):
    """人工审核动作"""

    __tablename__ = "review_actions"

    id = Column(Integer, primary_key=True, index=True)
    extraction_run_id = Column(Integer, ForeignKey("extraction_runs.id"), nullable=False, index=True)

    review_status = Column(String(50), nullable=False)
    review_reason = Column(Text, nullable=True)
    reviewed_fields_json = Column(JSON, nullable=True)
    final_values_json = Column(JSON, nullable=True)
    can_reuse_as_pattern = Column(Boolean, default=False)
    reviewer = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)

    extraction_run = relationship("ExtractionRun", back_populates="review_actions")
