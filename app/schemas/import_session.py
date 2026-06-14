"""
Pydantic schemas for tracking CSV imports.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus


class ImportSessionResponse(BaseModel):
    """Schema for returning details about an import session."""
    id: uuid.UUID
    group_id: uuid.UUID
    uploaded_by: uuid.UUID
    file_name: str
    status: ImportStatus
    total_rows: Optional[int] = None
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    uploaded_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
