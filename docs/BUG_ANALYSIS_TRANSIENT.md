# Bug Analysis: Transient Error Handling

## Discovery Date: 2026-03-10

## Issue: Agent fails to start when Gateway is draining

### Symptoms
- Agent reaches max wake attempts (3) and is marked offline
- Error message: "Gateway is draining for restart; new tasks are not accepted"
- `wake_attempts = 3`, `last_seen_at = NULL`

### Root Cause

**Bug #5: "draining" not in transient error markers**

File: `backend/app/services/openclaw/constants.py`

```python
_TRANSIENT_GATEWAY_ERROR_MARKERS = (
    "connect call failed",
    "connection refused",
    # ... other markers
    "service restart",  # ← This exists
    # "draining",       # ← Missing!
)
```

The error "Gateway is draining for restart" is not recognized as transient.

**Bug #6: lifecycle_orchestrator doesn't use retry mechanism**

File: `backend/app/services/openclaw/lifecycle_orchestrator.py`

```python
# coordination_service.py uses retry:
return await with_coordination_gateway_retry(fn)

# lifecycle_orchestrator.py does NOT use retry:
try:
    await OpenClawGatewayProvisioner().apply_agent_lifecycle(...)
except OpenClawGatewayError as exc:
    # Fails immediately without retry!
```

### Impact

When Gateway is draining/restarting:
1. Provisioning request fails immediately
2. `wake_attempts` increments
3. After 3 failures, agent is marked offline permanently
4. Agent never actually starts

### Timeline Evidence

```
18:29:22 - Mission Control creates Analyst-CodeReview
18:29:54 - Gateway starts draining (config.patch triggered)
18:30:24 - Agent tries to start → "Gateway is draining"
         → wake_attempts++ (now 3)
         → marked as offline
```

### Recommended Fixes

**Fix #5: Add "draining" to transient markers**

```python
_TRANSIENT_GATEWAY_ERROR_MARKERS = (
    # ... existing markers
    "draining",  # Add this
    "drain",     # And this for broader coverage
)
```

**Fix #6: Use retry in lifecycle_orchestrator**

Option A: Wrap provisioning calls with retry
```python
async def run_lifecycle(...):
    async def _provision():
        await OpenClawGatewayProvisioner().apply_agent_lifecycle(...)
    
    await with_coordination_gateway_retry(_provision)
```

Option B: Add wake_attempts reset on transient errors
```python
except OpenClawGatewayError as exc:
    if _is_transient_gateway_error(exc):
        # Don't count transient errors against wake_attempts
        locked.wake_attempts = max(0, locked.wake_attempts - 1)
    mark_provision_complete(locked, status="offline")
```

### Verification

After fixes:
1. Gateway draining should not increment wake_attempts
2. Agent should retry after Gateway restart completes
3. Agent should successfully start

---

## Related Files

- `backend/app/services/openclaw/constants.py` - Error markers
- `backend/app/services/openclaw/lifecycle_orchestrator.py` - Provisioning
- `backend/app/services/openclaw/internal/retry.py` - Retry logic
- `backend/app/services/openclaw/coordination_service.py` - Example of retry usage
