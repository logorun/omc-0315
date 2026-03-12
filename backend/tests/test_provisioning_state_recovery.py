# ruff: noqa: S101
"""Unit tests for provisioning state recovery (Bug 1, 2, 2.5, 2.6 fixes)."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import agent_auth
from app.core.time import utcnow
from app.models.agents import Agent
from app.services.openclaw.provisioning_db import AgentLifecycleService


def _make_agent(
    *,
    status: str = "online",
    last_seen_at_offset: timedelta | None = None,
    provision_requested_at_offset: timedelta | None = None,
    provision_action: str | None = None,
) -> Agent:
    now = utcnow()
    return Agent(
        id=uuid4(),
        name="test-agent",
        gateway_id=uuid4(),
        status=status,
        last_seen_at=(now + last_seen_at_offset) if last_seen_at_offset is not None else None,
        provision_requested_at=(
            now + provision_requested_at_offset
        ) if provision_requested_at_offset is not None else None,
        provision_action=provision_action,
    )


class TestWithComputedStatusTimeout:
    """Bug 1 Fix: with_computed_status should timeout stale updating/deleting states."""

    def test_updating_without_timeout_returns_unchanged(self) -> None:
        """Agent in 'updating' state for less than 5 minutes should remain updating."""
        agent = _make_agent(
            status="updating",
            provision_requested_at_offset=timedelta(minutes=-2),
            provision_action="update",
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "updating"

    def test_updating_with_timeout_resets_to_offline(self) -> None:
        """Agent in 'updating' state for more than 5 minutes should be reset to offline."""
        agent = _make_agent(
            status="updating",
            provision_requested_at_offset=timedelta(minutes=-6),
            provision_action="update",
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "offline"
        assert result.provision_action is None
        assert result.provision_requested_at is None
        assert "timed out" in (result.last_provision_error or "").lower()

    def test_deleting_with_timeout_resets_to_offline(self) -> None:
        """Agent in 'deleting' state for more than 5 minutes should be reset to offline."""
        agent = _make_agent(
            status="deleting",
            provision_requested_at_offset=timedelta(minutes=-10),
            provision_action="delete",
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "offline"
        assert result.provision_action is None

    def test_updating_without_provision_time_returns_unchanged(self) -> None:
        """Agent in 'updating' state without provision_requested_at should remain updating."""
        agent = _make_agent(
            status="updating",
            provision_requested_at_offset=None,
            provision_action="update",
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "updating"

    def test_online_agent_becomes_offline_after_timeout(self) -> None:
        """Agent that hasn't been seen for 10+ minutes should become offline."""
        agent = _make_agent(
            status="online",
            last_seen_at_offset=timedelta(minutes=-15),
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "offline"

    def test_online_agent_stays_online_within_timeout(self) -> None:
        """Agent seen within 10 minutes should remain online."""
        agent = _make_agent(
            status="online",
            last_seen_at_offset=timedelta(minutes=-5),
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "online"

    def test_agent_without_last_seen_becomes_provisioning(self) -> None:
        """Agent that has never been seen should be provisioning."""
        agent = _make_agent(
            status="online",
            last_seen_at_offset=None,
        )
        result = AgentLifecycleService.with_computed_status(agent)
        assert result.status == "provisioning"


class TestTouchAgentPresenceClearsProvisioningError:
    """Test that _touch_agent_presence clears stale provisioning error state."""

    @pytest.mark.asyncio
    async def test_touch_clears_last_provision_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When agent recovers via API calls, last_provision_error should be cleared."""
        now = utcnow()
        agent = Agent(
            id=uuid4(),
            name="test-agent",
            gateway_id=uuid4(),
            status="offline",
            last_seen_at=now - timedelta(minutes=5),
            last_provision_error="Agent did not check in after wake; max wake attempts reached",
            wake_attempts=3,
            checkin_deadline_at=now - timedelta(minutes=1),
        )

        request = SimpleNamespace(method="GET")
        session = SimpleNamespace()

        async def _fake_commit(*_: object, **__: object) -> None:
            return None

        monkeypatch.setattr(session, "commit", _fake_commit)

        await agent_auth._touch_agent_presence(request, session, agent)  # type: ignore[arg-type]

        assert agent.last_provision_error is None
        assert agent.wake_attempts == 0
        assert agent.checkin_deadline_at is None
        assert agent.status == "online"

    @pytest.mark.asyncio
    async def test_touch_preserves_updating_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Agent in 'updating' status should not be changed to 'online'."""
        now = utcnow()
        agent = Agent(
            id=uuid4(),
            name="test-agent",
            gateway_id=uuid4(),
            status="updating",
            last_seen_at=now - timedelta(minutes=5),
            last_provision_error="Previous error",
            wake_attempts=2,
        )

        request = SimpleNamespace(method="GET")
        session = SimpleNamespace()

        async def _fake_commit(*_: object, **__: object) -> None:
            return None

        monkeypatch.setattr(session, "commit", _fake_commit)

        await agent_auth._touch_agent_presence(request, session, agent)  # type: ignore[arg-type]

        assert agent.status == "updating"
        assert agent.last_provision_error is None
        assert agent.wake_attempts == 0
