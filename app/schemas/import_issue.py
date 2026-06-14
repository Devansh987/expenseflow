"""
Pydantic schemas for Import Issues (anomalies detected during import).
"""

import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueType, IssueStatus


class ImportIssueResponse(BaseModel):
    """Schema representing an anomaly detected during import."""
    id: uuid.UUID
    import_session_id: uuid.UUID
    row_number: int
    issue_type: IssueType
    description: str
    suggested_action: str
    status: IssueStatus
    
    # Optional fields for deeper context
    original_value: Optional[str] = None
    raw_data: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
