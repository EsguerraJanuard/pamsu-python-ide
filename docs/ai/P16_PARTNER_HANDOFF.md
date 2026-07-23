# Pillar 16 Partner Handoff

Backend version: 1.0.0-rc1

## Execution Contract

- Partner updates require the configured authentication header.
- Updates must include the correct correlation ID, worker identity, and sequence.
- Replays are idempotent only when payloads are identical.
- Out-of-order, conflicting, or terminal-state changes are rejected.
- FastAPI queues requests only; Python executes exclusively in the isolated partner sandbox.
- Partner responses must never include grades, misconduct verdicts, or private telemetry.

## Frozen API

- `P16_OPENAPI_RC1.json`
- `P16_OPENAPI_RC1.sha256`
