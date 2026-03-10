"""Admin-only migration endpoints for data cleanup and fixes."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.api.deps import require_org_member
from app.db.session import get_session
from app.services.organizations import is_org_admin

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

    from app.services.organizations import OrganizationContext

router = APIRouter(prefix="/admin/migrations", tags=["admin-migrations"])
SESSION_DEP = Depends(get_session)
ORG_MEMBER_DEP = Depends(require_org_member)


@router.post(
    "/fix-group-memory-is-chat",
    response_model=dict,
    summary="Fix is_chat field for all board_group_memory records",
    description="One-time migration to fix is_chat field for legacy records",
)
async def fix_group_memory_is_chat(
    group_id: UUID | None = None,
    session: AsyncSession = SESSION_DEP,
    ctx: OrganizationContext = ORG_MEMBER_DEP,
) -> dict[str, int | str]:
    """Fix is_chat field for board_group_memory records.
    
    This endpoint updates records where:
    - tags contains "chat" (tags @> '["chat"]')
    - is_chat is FALSE
    
    Args:
        group_id: Optional board group ID. If None, fixes all groups.
    
    Returns:
        Number of records updated.
    
    Requires organization admin or owner role.
    """
    if not is_org_admin(ctx.member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can run migrations",
        )
    
    if group_id:
        result = await session.exec(
            text("""
                UPDATE board_group_memory
                SET is_chat = TRUE
                WHERE board_group_id = :group_id
                  AND is_chat = FALSE
                  AND tags::jsonb @> '["chat"]'::jsonb
            """),
            {"group_id": str(group_id)},
        )
    else:
        result = await session.exec(
            text("""
                UPDATE board_group_memory
                SET is_chat = TRUE
                WHERE is_chat = FALSE
                  AND tags::jsonb @> '["chat"]'::jsonb
            """)
        )
    
    updated_count = result.rowcount if hasattr(result, 'rowcount') else 0
    await session.commit()
    
    return {
        "updated_records": updated_count,
        "message": f"Updated {updated_count} record(s) to set is_chat=TRUE"
    }
