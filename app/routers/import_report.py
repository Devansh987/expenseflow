"""
Import Report router.
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.import_session import ImportSessionResponse
from app.schemas.import_issue import ImportIssueResponse
from app.services import import_report as report_service
from app.utils.dependencies import get_current_user

# We need a new schema that extends ImportSessionResponse to include issues
class ImportReportResponse(ImportSessionResponse):
    issues: list[ImportIssueResponse]


router = APIRouter(prefix="/groups", tags=["Import Reports"])


@router.get("/{group_id}/imports/{session_id}/report", response_model=ImportReportResponse)
async def get_import_audit_report(
    group_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete audit report for a specific import session.
    This includes metadata about the file and a full list of detected anomalies (issues).
    """
    return await report_service.get_import_report(db, group_id, session_id)
