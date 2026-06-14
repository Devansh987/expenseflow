"""
Import Report service.

Provides detailed audit reports for a given import session, 
including all detected anomalies and their statuses.
"""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.import_session import ImportSession
from app.models.import_issue import ImportIssue


async def get_import_report(db: AsyncSession, group_id: uuid.UUID, session_id: uuid.UUID) -> ImportSession:
    """
    Fetch an import session along with all of its detected issues.
    """
    query = (
        select(ImportSession)
        .options(selectinload(ImportSession.issues))
        .where(
            (ImportSession.id == session_id) & 
            (ImportSession.group_id == group_id)
        )
    )
    result = await db.execute(query)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Import session not found or does not belong to this group."
        )
        
    return session
