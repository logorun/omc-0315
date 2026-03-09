"""Seed real Gateway configuration for production Mission Control."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Real Gateway configuration
GATEWAY_ID = UUID("8443e0b1-a1bf-455d-adc0-16e90d1c5b70")
GATEWAY_URL = "ws://127.0.0.1:18789"
GATEWAY_TOKEN = "84478ae2c35ace55e2e3e43faded8e2584bb9c3ad8410810"
WORKSPACE_ROOT = "/root/.openclaw/workspace/workspace-gateway-8443e0b1-a1bf-455d-adc0-16e90d1c5b70"


async def run() -> None:
    from app.db.session import async_session_maker, init_db
    from app.models.agents import Agent
    from app.models.boards import Board
    from app.models.gateways import Gateway
    from app.models.organizations import Organization
    from app.models.users import User
    from sqlmodel import select

    await init_db()
    async with async_session_maker() as session:
        # Check if gateway already exists
        existing = (await session.execute(select(Gateway).where(Gateway.id == GATEWAY_ID))).scalar_one_or_none()
        if existing:
            print(f"Gateway {GATEWAY_ID} already exists")
            return

        # Create organization
        org = Organization(name="Default Organization")
        session.add(org)
        await session.commit()
        await session.refresh(org)
        print(f"Created organization: {org.id}")

        # Create gateway
        gateway = Gateway(
            id=GATEWAY_ID,
            organization_id=org.id,
            name="Main Gateway",
            url=GATEWAY_URL,
            token=GATEWAY_TOKEN,
            workspace_root=WORKSPACE_ROOT,
            disable_device_pairing=False,
        )
        session.add(gateway)
        await session.commit()
        await session.refresh(gateway)
        print(f"Created gateway: {gateway.id}")

        # Create board
        board = Board(
            name="Onboarding Test",
            slug="onboarding-test",
            organization_id=org.id,
            gateway_id=gateway.id,
            board_type="goal",
            objective="Test onboarding workflow",
            success_metrics={"test": True},
        )
        session.add(board)
        await session.commit()
        await session.refresh(board)
        print(f"Created board: {board.id}")

        # Create super admin user
        user = User(
            clerk_user_id="boss-jack",
            email="boss@jack.local",
            name="Boss Jack",
            is_super_admin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Created user: {user.id}")

        # Create lead agent
        lead = Agent(
            board_id=board.id,
            name="Lead Agent",
            status="online",
            is_board_lead=True,
        )
        session.add(lead)
        await session.commit()
        print(f"Created lead agent: {lead.id}")

        print("\n✅ Seed completed successfully!")


if __name__ == "__main__":
    asyncio.run(run())
