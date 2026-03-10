"""State machine constants and validation for Mission Control entities.

This module centralizes state definitions and valid transitions to prevent
invalid state changes and improve debugging of state-related issues.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


class TaskStatus(str, Enum):
    """Valid task status values with explicit state machine."""

    INBOX = "inbox"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

    @classmethod
    def all(cls) -> set[str]:
        return {s.value for s in cls}


class AgentStatus(str, Enum):
    """Valid agent status values with explicit state machine."""

    PROVISIONING = "provisioning"
    UPDATING = "updating"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DELETING = "deleting"

    @classmethod
    def all(cls) -> set[str]:
        return {s.value for s in cls}


class OnboardingStatus(str, Enum):
    """Valid onboarding session status values."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def all(cls) -> set[str]:
        return {s.value for s in cls}


VALID_TASK_TRANSITIONS: Final[dict[str, set[str]]] = {
    TaskStatus.INBOX.value: {TaskStatus.IN_PROGRESS.value, TaskStatus.DONE.value},
    TaskStatus.IN_PROGRESS.value: {
        TaskStatus.INBOX.value,
        TaskStatus.REVIEW.value,
        TaskStatus.DONE.value,
    },
    TaskStatus.REVIEW.value: {
        TaskStatus.INBOX.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.DONE.value,
    },
    TaskStatus.DONE.value: {
        TaskStatus.INBOX.value,
        TaskStatus.IN_PROGRESS.value,
        TaskStatus.REVIEW.value,
    },
}

VALID_AGENT_TRANSITIONS: Final[dict[str, set[str]]] = {
    AgentStatus.PROVISIONING.value: {
        AgentStatus.ONLINE.value,
        AgentStatus.ERROR.value,
    },
    AgentStatus.UPDATING.value: {
        AgentStatus.ONLINE.value,
        AgentStatus.ERROR.value,
    },
    AgentStatus.ONLINE.value: {
        AgentStatus.OFFLINE.value,
        AgentStatus.UPDATING.value,
        AgentStatus.ERROR.value,
        AgentStatus.DELETING.value,
    },
    AgentStatus.OFFLINE.value: {
        AgentStatus.ONLINE.value,
        AgentStatus.UPDATING.value,
        AgentStatus.PROVISIONING.value,
        AgentStatus.ERROR.value,
        AgentStatus.DELETING.value,
    },
    AgentStatus.ERROR.value: {
        AgentStatus.PROVISIONING.value,
        AgentStatus.UPDATING.value,
        AgentStatus.ONLINE.value,
        AgentStatus.DELETING.value,
    },
    AgentStatus.DELETING.value: set(),
}

VALID_ONBOARDING_TRANSITIONS: Final[dict[str, set[str]]] = {
    OnboardingStatus.ACTIVE.value: {
        OnboardingStatus.COMPLETED.value,
        OnboardingStatus.CANCELLED.value,
    },
    OnboardingStatus.COMPLETED.value: set(),
    OnboardingStatus.CANCELLED.value: {OnboardingStatus.ACTIVE.value},
}


def is_valid_task_transition(current: str, target: str) -> bool:
    if current not in VALID_TASK_TRANSITIONS:
        return False
    return target in VALID_TASK_TRANSITIONS[current]


def is_valid_agent_transition(current: str, target: str) -> bool:
    if current not in VALID_AGENT_TRANSITIONS:
        return False
    return target in VALID_AGENT_TRANSITIONS[current]


def is_valid_onboarding_transition(current: str, target: str) -> bool:
    if current not in VALID_ONBOARDING_TRANSITIONS:
        return False
    return target in VALID_ONBOARDING_TRANSITIONS[current]


def validate_task_transition(current: str, target: str) -> None:
    if not is_valid_task_transition(current, target):
        raise InvalidStateTransitionError(
            entity_type="task",
            current=current,
            target=target,
            valid_targets=VALID_TASK_TRANSITIONS.get(current, set()),
        )


def validate_agent_transition(current: str, target: str) -> None:
    if not is_valid_agent_transition(current, target):
        raise InvalidStateTransitionError(
            entity_type="agent",
            current=current,
            target=target,
            valid_targets=VALID_AGENT_TRANSITIONS.get(current, set()),
        )


class InvalidStateTransitionError(Exception):
    def __init__(
        self,
        entity_type: str,
        current: str,
        target: str,
        valid_targets: set[str],
    ) -> None:
        self.entity_type = entity_type
        self.current = current
        self.target = target
        self.valid_targets = valid_targets
        message = (
            f"Invalid {entity_type} state transition: "
            f"'{current}' -> '{target}'. "
            f"Valid transitions from '{current}': {sorted(valid_targets) or 'none'}"
        )
        super().__init__(message)
