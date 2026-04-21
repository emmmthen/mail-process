from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EmailMessageResponse(BaseModel):
    id: int
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[datetime] = None
    source_file_path: Optional[str] = None
    source_file_hash: Optional[str] = None
    source_type: Optional[str] = None
    message_id: Optional[str] = None
    raw_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailArtifactResponse(BaseModel):
    id: int
    email_message_id: int
    cleaned_text: Optional[str] = None
    rebuilt_text: Optional[str] = None
    rebuilt_blocks_json: Optional[Any] = None
    extractable_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractionRunResponse(BaseModel):
    id: int
    email_message_id: int
    email_artifact_id: Optional[int] = None
    extract_mode: str
    llm_input_snapshot: Optional[str] = None
    llm_output_json: Optional[Any] = None
    validation_result_json: Optional[Any] = None
    confidence_score: Optional[float] = None
    run_status: str
    committed_quote_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewActionResponse(BaseModel):
    id: int
    extraction_run_id: int
    review_status: str
    review_reason: Optional[str] = None
    reviewed_fields_json: Optional[Any] = None
    final_values_json: Optional[Any] = None
    can_reuse_as_pattern: bool
    reviewer: Optional[str] = None
    reviewed_at: datetime

    class Config:
        from_attributes = True


class ReviewPendingItem(BaseModel):
    extraction_run_id: int
    email_message_id: int
    subject: Optional[str] = None
    sender: Optional[str] = None
    confidence_score: Optional[float] = None
    run_status: str
    created_at: datetime
    quote_status: Optional[str] = None
    supplier_name: Optional[str] = None
    part_number: Optional[str] = None


class ReviewDetailResponse(BaseModel):
    email_message: EmailMessageResponse
    email_artifact: Optional[EmailArtifactResponse] = None
    extraction_run: ExtractionRunResponse
    review_actions: list[ReviewActionResponse] = Field(default_factory=list)


class ReviewApproveRequest(BaseModel):
    reviewer: Optional[str] = None
    review_reason: Optional[str] = None
    final_values: Optional[dict[str, Any]] = None
    can_reuse_as_pattern: bool = False


class ReviewCorrectRequest(BaseModel):
    reviewer: Optional[str] = None
    review_reason: Optional[str] = None
    reviewed_fields: Optional[dict[str, Any]] = None
    final_values: dict[str, Any] = Field(default_factory=dict)
    can_reuse_as_pattern: bool = False


class ReviewRejectRequest(BaseModel):
    reviewer: Optional[str] = None
    review_reason: str
    reviewed_fields: Optional[dict[str, Any]] = None
    can_reuse_as_pattern: bool = False
