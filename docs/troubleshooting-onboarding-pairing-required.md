# Troubleshooting: Onboarding "pairing required" Error

## Problem

When starting onboarding from Mission Control UI or API, you get:

```
Gateway onboarding start dispatch failed: pairing required
```

## Root Cause

This error occurs when Mission Control database is missing required records:

1. **Gateway not registered** - The gateways table is empty
2. **User has no organization access** - Missing organization membership
3. **Gateway Agent not provisioned** - No agent record with valid authentication

## Solution

### Step 1: Seed Gateway and Organization

Run the seed script to create required database records:

```bash
cd /root/openclaw-mission-control/backend
source .venv/bin/activate
python scripts/seed_real.py
```

This creates: Organization, Gateway, Board, User

### Step 2: Configure User Organization Access

```sql
UPDATE users SET active_organization_id = '<org-id>', is_super_admin = true WHERE clerk_user_id = 'local-auth-user';

INSERT INTO organization_members (id, organization_id, user_id, role, all_boards_read, all_boards_write, created_at, updated_at) VALUES (gen_random_uuid(), '<org-id>', '<user-id>', 'admin', true, true, now(), now());
```

### Step 3: Provision Gateway Agent

```bash
cd /root/openclaw-mission-control/backend
source .venv/bin/activate
python scripts/provision_gateway_agent.py
```

### Step 4: Set Agent Session Key

```sql
UPDATE agents SET openclaw_session_id = 'agent:mc-gateway-<gateway-id>:main' WHERE id = '<agent-id>';
```

## Verification

```bash
# Test user endpoint
curl -s -X POST 'http://localhost:8000/api/v1/boards/<board-id>/onboarding/start' -H 'Authorization: Bearer <local-auth-token>' -H 'Content-Type: application/json' -d '{}'

# Test agent endpoint
curl -s -X POST 'http://localhost:8000/api/v1/agent/boards/<board-id>/onboarding' -H 'X-Agent-Token: <agent-token>' -H 'Content-Type: application/json' -d '{"question":"Test?","options":[{"id":"1","label":"Yes"}]}'
```

Both should return 200 OK.

## Key Concepts

### Agent Authentication Requirements

1. **agent_token_hash** - PBKDF2 hash of the agent token (for API auth)
2. **openclaw_session_id** - Must match `agent:mc-gateway-<gateway-id>:main` pattern
3. **gateway_id** - Must reference a valid gateway in the database

### Local Auth User

When using LOCAL_AUTH_TOKEN, Mission Control looks for a user with `clerk_user_id = 'local-auth-user'`. This user must have:
- `active_organization_id` set to a valid organization
- Membership record in `organization_members` table

## Related Files

- `backend/scripts/seed_real.py` - Initialize database with Gateway/Org/Board/User
- `backend/scripts/provision_gateway_agent.py` - Create and authenticate Gateway Agent
- `backend/app/services/openclaw/policies.py` - Authorization policy

---

*Last updated: 2026-03-09*
*Author: Mush (OpenClaw Agent)*

---

## Remote Access Configuration

When accessing Mission Control from a remote IP (not localhost), you must configure:

### 1. Frontend API URL
Edit `frontend/.env`:
```
NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000
```

### 2. Backend CORS Origins
Edit `backend/.env`:
```
CORS_ORIGINS=http://localhost:3000,http://YOUR_SERVER_IP:3000
```

### 3. Restart Services
```bash
mc-restart
```

**Note:** Both changes are required. Without CORS configuration, the browser will reject API calls from the frontend.

---

*Updated: 2026-03-09 - Added remote access config*
