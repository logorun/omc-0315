"""Provision the gateway main agent with token."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

GATEWAY_ID = UUID("8443e0b1-a1bf-455d-adc0-16e90d1c5b70")
AGENT_TOKEN = "ACIH5o8y4DJWDvNVgzi1deYn88Xqg5SiURUXU5Xe6SM"
AGENT_ID = UUID("fb3fb072-e640-4f23-a141-bacdc9637ddb")


async def run() -> None:
    from app.db.session import async_session_maker, init_db
    from app.models.agents import Agent
    from app.models.gateways import Gateway
    from app.core.agent_tokens import hash_agent_token
    from sqlmodel import select

    await init_db()
    async with async_session_maker() as session:
        # Get gateway
        gateway = await session.get(Gateway, GATEWAY_ID)
        if not gateway:
            print(f"Gateway {GATEWAY_ID} not found")
            return

        # Check if agent exists
        existing = await session.get(Agent, AGENT_ID)
        if existing:
            print(f"Agent {AGENT_ID} already exists, updating token...")
            existing.agent_token_hash = hash_agent_token(AGENT_TOKEN)
            existing.status = "online"
            session.add(existing)
        else:
            # Create agent
            agent = Agent(
                id=AGENT_ID,
                gateway_id=GATEWAY_ID,
                name="Main Gateway Agent",
                status="online",
                agent_token_hash=hash_agent_token(AGENT_TOKEN),
            )
            session.add(agent)
        
        await session.commit()
        print(f"✅ Gateway agent provisioned successfully!")
        print(f"   Agent ID: {AGENT_ID}")
        print(f"   Gateway ID: {GATEWAY_ID}")


if __name__ == "__main__":
    asyncio.run(run())
