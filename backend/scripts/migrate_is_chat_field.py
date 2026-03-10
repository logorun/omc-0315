#!/usr/bin/env python3
"""
One-time migration script to fix is_chat field for board_group_memory records.

This script updates all records where:
- tags contains "chat" (tags @> '["chat"]')
- is_chat is FALSE

This fixes records created before the is_chat field was automatically set from tags.

Usage:
    cd backend
    python scripts/migrate_is_chat_field.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import async_session_maker


async def migrate_is_chat_field() -> int:
    """Update is_chat field for all legacy records."""
    
    async with async_session_maker() as session:
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
        
        return updated_count


async def main():
    print("Starting is_chat field migration...")
    print("This will update all board_group_memory records where:")
    print("  - tags contains 'chat'")
    print("  - is_chat is FALSE")
    print()
    
    try:
        updated_count = await migrate_is_chat_field()
        print(f"✓ Migration complete!")
        print(f"  Updated {updated_count} record(s)")
        return 0
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
