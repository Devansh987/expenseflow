"""
Import Router for handling CSV file uploads.
"""

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.import_session import ImportSessionResponse
from app.services import import_session as import_service
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Import"])


@router.post("/{group_id}/import", response_model=ImportSessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    group_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CSV file for import.
    Returns HTTP 202 Accepted because the processing happens asynchronously 
    (or as part of the anomaly detection engine in Phase 10).
    """
    return await import_service.start_import(db, group_id, file, current_user)


@router.get("/{group_id}/imports", response_model=list[ImportSessionResponse])
async def list_imports(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all import sessions for a specific group."""
    return await import_service.get_import_sessions(db, group_id)
