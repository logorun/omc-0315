# Gateway Connection Troubleshooting

This guide covers common issues when connecting OpenClaw Gateways to Mission Control, especially in Docker deployments with public network access.

## Table of Contents

- [Device Pairing Required](#device-pairing-required)
- [Origin Not Allowed](#origin-not-allowed)
- [Docker Network Connectivity](#docker-network-connectivity)
- [Public Network Access](#public-network-access)
- [Complete Configuration Checklist](#complete-configuration-checklist)

---

## Device Pairing Required

### Symptoms

- Gateway creation shows "pairing required" status
- Gateway creation fails with no clear error
- Mission Control shows "origin not allowed" error even with correct origins configured

### Root Cause

When Mission Control first connects to an OpenClaw Gateway, it initiates a device pairing request. This request enters a **pending** state and must be explicitly approved by an operator on the gateway host. The pairing flow is a security measure to prevent unauthorized control of gateways.

### Solution

1. **Check for pending pairing requests:**

   ```bash
   # On the OpenClaw gateway host
   openclaw devices list
   ```

2. **Approve the pending request:**

   ```bash
   openclaw devices approve <request-id>
   ```

   Example output:
   ```
   Pending (1)
   ┌──────────────────────────────────────┬────────────────────────────────────┬──────────┬────────────┐
   │ Request                              │ Device                             │ Role     │ IP         │
   ├──────────────────────────────────────┼────────────────────────────────────┼──────────┼────────────┤
   │ 43813a04-4a1d-4cf3-b39b-2078febc15c8 │ 9e32992a38455e9c...                │ operator │ 172.18.0.5 │
   └──────────────────────────────────────┴────────────────────────────────────┴──────────┴────────────┘

   # Approve
   openclaw devices approve 43813a04-4a1d-4cf3-b39b-2078febc15c8
   ```

3. **Retry gateway creation in Mission Control UI**

### Alternative: Disable Device Pairing

For trusted environments, you can disable device pairing in the gateway creation form by enabling "Disable device pairing". This allows direct connection without approval.

---

## Origin Not Allowed

### Symptoms

- Error message: `origin not allowed (open the Control UI from the gateway host or allow it in gateway.controlUi.allowedOrigins)`
- Gateway compatibility check fails

### Root Cause

OpenClaw Gateway validates the `Origin` header of incoming WebSocket connections. Mission Control's backend sends requests with its own origin, which must be explicitly allowed.

### Solution

1. **Identify Mission Control's origin:**
   - If running in Docker: `http://host.docker.internal:<frontend-port>`
   - If accessing from public network: `http://<public-ip>:<frontend-port>`

2. **Update OpenClaw gateway configuration (`~/.openclaw/openclaw.json`):**

   ```json
   {
     "gateway": {
       "controlUi": {
         "allowedOrigins": [
           "http://localhost:18789",
           "http://127.0.0.1:18789",
           "http://<public-ip>:3001",
           "http://localhost:3001",
           "http://host.docker.internal:3001"
         ]
       }
     }
   }
   ```

3. **Restart the OpenClaw gateway** (or wait for config hot-reload if supported)

### Docker Container Origins

When Mission Control runs in Docker and connects to a gateway on the host:

- The backend container sees itself as originating from `host.docker.internal`
- Add `http://host.docker.internal:<port>` to allowed origins
- The port is Mission Control's **frontend** port (not the gateway port)

---

## Docker Network Connectivity

### Symptoms

- "Connection refused" errors
- Gateway URL `ws://localhost:18789` doesn't work from containers
- Backend cannot reach gateway

### Root Cause

Docker containers have their own network namespace. `localhost` inside a container refers to the container itself, not the host machine.

### Solution

1. **Use `host.docker.internal` as the gateway URL:**

   ```
   ws://host.docker.internal:18789
   ```

2. **Enable host resolution in `compose.yml`:**

   ```yaml
   services:
     backend:
       extra_hosts:
         - "host.docker.internal:host-gateway"
   ```

   This maps `host.docker.internal` to the host's Docker bridge gateway IP (typically `172.17.0.1`).

3. **Verify connectivity:**

   ```bash
   # From inside the backend container
   docker exec -it <backend-container> curl -v http://host.docker.internal:18789
   ```

### Alternative: Host Network Mode

For development, you can use host networking:

```yaml
services:
  backend:
    network_mode: "host"
```

This allows `localhost` to work, but may cause port conflicts.

---

## Public Network Access

### Symptoms

- "Unable to reach backend to validate token" from public access
- CORS errors in browser console
- API calls fail from public IP

### Root Cause

Mission Control needs explicit configuration for public access, including CORS origins and public API URL.

### Solution

1. **Configure CORS origins (`.env`):**

   ```bash
   CORS_ORIGINS=http://localhost:3001,http://<public-ip>:3001
   ```

2. **Set public API URL (`.env`):**

   ```bash
   NEXT_PUBLIC_API_URL=http://<public-ip>:8000
   ```

3. **Ensure OpenClaw gateway binds to LAN (not loopback):**

   In `~/.openclaw/openclaw.json`:

   ```json
   {
     "gateway": {
       "bind": "lan",
       "port": 18789
     }
   }
   ```

4. **Firewall configuration:**

   Ensure the following ports are accessible:
   - Frontend: 3001 (or your chosen port)
   - Backend: 8000
   - Gateway: 18789 (WebSocket)

---

## Complete Configuration Checklist

### OpenClaw Gateway (`~/.openclaw/openclaw.json`)

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://<public-ip>:3001",
        "http://localhost:3001",
        "http://host.docker.internal:3001"
      ]
    },
    "auth": {
      "mode": "token",
      "token": "<your-gateway-token>"
    }
  }
}
```

### Mission Control (`.env`)

```bash
# Ports
FRONTEND_PORT=3001
BACKEND_PORT=8000

# Authentication
AUTH_MODE=local
LOCAL_AUTH_TOKEN=<your-mission-control-token>

# Public access
CORS_ORIGINS=http://localhost:3001,http://<public-ip>:3001
NEXT_PUBLIC_API_URL=http://<public-ip>:8000
```

### Mission Control (`compose.yml`)

```yaml
services:
  backend:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    # ... other config
```

### Gateway Creation in Mission Control UI

| Field | Value |
|-------|-------|
| Gateway name | `My Gateway` |
| Gateway URL | `ws://host.docker.internal:18789` |
| Gateway token | `<gateway-token-from-openclaw.json>` |
| Workspace root | `~/.openclaw` |
| Disable device pairing | ✓ (for trusted environments) or leave unchecked and approve manually |

---

## Quick Diagnostic Commands

```bash
# Check OpenClaw gateway is running
curl http://localhost:18789

# List pending/paired devices
openclaw devices list

# Approve pending device
openclaw devices approve <request-id>

# Check Mission Control backend health
curl http://localhost:8000/healthz

# Check backend logs for gateway errors
docker compose logs backend --tail=50 | grep -i gateway

# Test gateway connectivity from backend container
docker exec -it <backend-container> curl -v http://host.docker.internal:18789
```
