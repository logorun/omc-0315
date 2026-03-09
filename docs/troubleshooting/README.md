# Troubleshooting

- [Gateway connection issues](./gateway-connection.md) — Device pairing, origin errors, Docker networking, public access
- [Gateway agent provisioning and check-in](./gateway-agent-provisioning.md)

## Common issues

- Frontend can't reach backend (check `NEXT_PUBLIC_API_URL`)
- Auth errors (check `AUTH_MODE`, tokens)
- DB connection/migrations
- Gateway shows "origin not allowed" (see [Gateway connection issues](./gateway-connection.md#origin-not-allowed))
- Gateway creation stuck on "pairing required" (see [Device pairing](./gateway-connection.md#device-pairing-required))

> **Note**
> Expand with concrete symptoms + fixes as issues are discovered.
