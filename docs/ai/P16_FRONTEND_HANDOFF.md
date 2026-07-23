# Pillar 16 Frontend Handoff

Backend version: 1.0.0-rc1

## Contract

- Frozen OpenAPI: `P16_OPENAPI_RC1.json`
- Checksum: `P16_OPENAPI_RC1.sha256`
- Authentication and authorization remain backend-enforced.
- React must never execute student Python.
- Student responses exclude hidden tests and instructor-only analytics.
- Paste telemetry sends aggregate counts and timestamps only.
- No clipboard content, browsing history, screen, webcam, microphone, or individual keystrokes.

## Integration Rule

Generate frontend API types and clients only from the frozen RC1 OpenAPI contract.
