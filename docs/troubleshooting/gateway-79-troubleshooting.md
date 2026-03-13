# OpenClaw Mission Control - Gateway Troubleshooting Guide

## Gateway: 电商AI Gateway (.79)
- **Server IP**: 216.116.160.79
- **Gateway ID**: acd4001c-a911-4ec0-9f49-57d7f57a0fb7
- **Agent ID**: 2dde96be-1294-445e-bb70-663f6914f4c9
- **Gateway URL**: wss://gw-79-ec.imlogo.net:443
- **Gateway Token**: eed33f14de30bffdf188302021d697e9835cf46ec0d23a76

## Known Issue: Intermittent SIGTERM Signals

### Symptoms
- Gateway process receives SIGTERM signals erratically (every 10-60 seconds)
- Caddy returns HTTP 502 when gateway is down
- Agent status shows `provision_failed` or `update_failed`

### Investigation Findings
1. **NOT caused by**: systemd, cron jobs, monitoring services, OOM killer
2. **Systemd NRestarts**: Shows 0 (systemd is NOT restarting the service)
3. **Memory**: Plenty available (7.8GB total, 7GB free)
4. **Process**: Runs normally between SIGTERM events
5. **VM Type**: QEMU virtual machine

### Partial Workaround Applied
1. Disabled `commands.restart` in `/root/.openclaw/openclaw.json`
2. Changed systemd service `Restart=on-failure` (from `Restart=always`)
3. Fixed invalid environment variable in systemd service file

## Manual Fix Steps

### 1. Approve Device Pairing
```bash
# On gateway server (.79)
ssh ecs95033

# Check pending devices
cat /root/.openclaw/devices/pending.json | jq '.'

# Approve device
pending=$(cat /root/.openclaw/devices/pending.json)
device_id=$(echo $pending | jq -r '.[].deviceId')
device=$(echo $pending | jq '.[]')
cat /root/.openclaw/devices/paired.json | jq --argjson dev "$device" --arg id "$device_id" '. + {($id): $dev}' > /tmp/paired.json
mv /tmp/paired.json /root/.openclaw/devices/paired.json
echo '{}' > /root/.openclaw/devices/pending.json
```

### 2. Update Agent Status in Database
```bash
# On MC server (.78)
ssh ecs

# Set agent to online
docker exec openclaw-mission-control-db-1 psql -U postgres -d mission_control -c \
  "UPDATE agents SET status = 'online', updated_at = NOW() WHERE id = '2dde96be-1294-445e-bb70-663f6914f4c9';"

# Verify
docker exec openclaw-mission-control-db-1 psql -U postgres -d mission_control -c \
  "SELECT id, status FROM agents WHERE gateway_id = 'acd4001c-a911-4ec0-9f49-57d7f57a0fb7';"
```

### 3. Check Gateway Connection
```bash
# Check from MC server
curl -s -X GET "https://omc.imlogo.net/api/v1/gateways/status?gateway_url=wss://gw-79-ec.imlogo.net:443&gateway_token=eed33f14de30bffdf188302021d697e9835cf46ec0d23a76" \
  -H "Authorization: Bearer mc-local-auth-token-216-116-160-78-mission-control-secure-token-2026" | jq '.'
```

## Configuration Files

### Systemd Service (.79)
**File**: `/root/.config/systemd/user/openclaw-gateway.service`
- Restart: on-failure (not always)
- SuccessExitStatus: 0 143 (SIGTERM = 143, considered success)

### OpenClaw Config (.79)
**File**: `/root/.openclaw/openclaw.json`
- `commands.restart`: false

### Caddy Config (.79)
**File**: `/etc/caddy/Caddyfile`
- Reverse proxy to localhost:18789

## Recommended Next Steps
1. **Investigate VM-level signals**: The SIGTERM source is likely from the hypervisor or VM infrastructure
2. **Contact cloud provider**: Check if there are any VM-level health checks or watchdogs
3. **Consider alternative deployment**: Run gateway on bare metal or different VM provider

## Related Commands
```bash
# Check gateway logs
tail -f /tmp/openclaw/openclaw-2026-03-13.log | grep -a SIGTERM

# Check systemd status
systemctl --user status openclaw-gateway

# Restart gateway
systemctl --user restart openclaw-gateway

# Check listening ports
netstat -tlnp | grep 18789
```
