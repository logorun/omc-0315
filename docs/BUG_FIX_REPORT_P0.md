# Bug Fix Report - P0 Fixes

## Summary

Fixed 4 P0 bugs related to agent state machine incomplete error handling.

**Core Principle**: Any exception path must restore agent state to prevent stuck states.

---

## Bug 1: with_computed_status 状态卡住

**File**: `backend/app/services/openclaw/provisioning_db.py:868-884`

**Problem**: When agent status is "updating" or "deleting", `with_computed_status` returns immediately without checking for timeout, causing permanent stuck states.

**Fix**: Added 5-minute timeout detection for stale updating/deleting states:

```python
@classmethod
def with_computed_status(cls, agent: Agent) -> Agent:
    now = utcnow()
    # Bug 1 Fix: Check for stale updating/deleting states
    PROVISION_TIMEOUT = timedelta(minutes=5)
    if agent.status in {"deleting", "updating"}:
        if agent.provision_requested_at is not None:
            if now - agent.provision_requested_at > PROVISION_TIMEOUT:
                # Provision has timed out, reset to offline
                agent.status = "offline"
                agent.provision_action = None
                agent.provision_requested_at = None
                agent.last_provision_error = "Provisioning timed out after 5 minutes"
        return agent
    if agent.last_seen_at is None:
        agent.status = "provisioning"
    elif now - agent.last_seen_at > OFFLINE_AFTER:
        agent.status = "offline"
    return agent
```

**Import Added**: `timedelta` to `from datetime import UTC, datetime, timedelta`

---

## Bug 2: run_lifecycle 错误处理不完整

**File**: `backend/app/services/openclaw/lifecycle_orchestrator.py:90-145`

**Problem**: When Gateway errors occur, only `last_provision_error` is logged without calling `mark_provision_complete`, leaving agent stuck in "updating" state.

**Fix**: Added `mark_provision_complete(locked, status="offline")` in both exception handlers:

```python
except OpenClawGatewayError as exc:
    # Bug 2 Fix: Mark provision complete to prevent stuck state
    mark_provision_complete(locked, status="offline")
    locked.last_provision_error = str(exc)
    # ... rest of handler

except (OSError, RuntimeError, ValueError) as exc:
    # Bug 2 Fix: Mark provision complete to prevent stuck state
    mark_provision_complete(locked, status="offline")
    locked.last_provision_error = str(exc)
    # ... rest of handler
```

---

## Bug 2.5: Reconcile max_attempts 状态不一致

**File**: `backend/app/services/openclaw/lifecycle_reconcile.py:82-98`

**Problem**: When max wake attempts reached, status is set to "offline" but `provision_action` and `provision_requested_at` are not cleared, causing inconsistent state.

**Fix**: Added cleanup of provision fields:

```python
if agent.wake_attempts >= MAX_WAKE_ATTEMPTS_WITHOUT_CHECKIN:
    agent.status = "offline"
    # Bug 2.5 Fix: Clear provision fields to prevent stuck state
    agent.provision_action = None
    agent.provision_requested_at = None
    agent.checkin_deadline_at = None
    # ... rest of handler
```

---

## Bug 2.6: Gateway/Board 缺失时状态卡住

**File**: `backend/app/services/openclaw/lifecycle_reconcile.py:99-116`

**Problem**: When Gateway or Board is deleted/missing, only logs a warning and returns without updating agent state, leaving agent stuck.

**Fix**: Mark agent as offline and set error message:

```python
gateway = await Gateway.objects.by_id(agent.gateway_id).first(session)
if gateway is None:
    # Bug 2.6 Fix: Mark agent offline when gateway is deleted
    agent.status = "offline"
    agent.provision_action = None
    agent.provision_requested_at = None
    agent.checkin_deadline_at = None
    agent.last_provision_error = "Gateway deleted or not found"
    agent.updated_at = utcnow()
    session.add(agent)
    await session.commit()
    logger.warning(
        "lifecycle.reconcile.gateway_missing_marked_offline",
        extra={"agent_id": str(agent.id), "gateway_id": str(agent.gateway_id)},
    )
    return

# Same pattern for missing Board
if board is None:
    # Bug 2.6 Fix: Mark agent offline when board is deleted
    agent.status = "offline"
    agent.provision_action = None
    agent.provision_requested_at = None
    agent.checkin_deadline_at = None
    agent.last_provision_error = "Board deleted or not found"
    # ...
```

---

## Test Coverage

Added new test file: `backend/tests/test_provisioning_state_recovery.py`

Tests cover:
- Bug 1: Timeout detection for updating/deleting states
- Normal status transitions (online → offline, provisioning, etc.)

---

## Files Modified

| File | Lines Changed | Bug Fixed |
|------|---------------|-----------|
| `backend/app/services/openclaw/provisioning_db.py` | 868-884 | Bug 1 |
| `backend/app/services/openclaw/lifecycle_orchestrator.py` | 90-145 | Bug 2 |
| `backend/app/services/openclaw/lifecycle_reconcile.py` | 82-116 | Bug 2.5, 2.6 |
| `backend/tests/test_provisioning_state_recovery.py` | NEW | Test coverage |

---

## Verification Commands

```bash
# Run tests
make test

# Type check
make typecheck

# Lint
make lint
```

---

## Next Steps

1. Deploy to staging environment
2. Monitor agent state transitions
3. Verify no agents stuck in "updating" state
4. Process P1 bugs if P0 fixes are stable
