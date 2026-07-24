# Changelog

## 1.0.0 — Final Release

- Promoted backend version from `1.0.0-rc1` to `1.0.0`.
- No new features were introduced after release-candidate acceptance.
- API contract remains unchanged except for the version string.
- Frozen final OpenAPI artifacts:
  - `docs/ai/OPENAPI_1_0_0.json`
  - `docs/ai/OPENAPI_1_0_0.sha256`
- OpenAPI checksum: `c962d2ce3924bc2bb3e064941715a4c21803dfffa2256839b6da153679aa0560`
- Migration head remains `9f2c6e4a1b7d`.
- Authorization, privacy, grading, execution, and sandbox boundaries remain unchanged.
- Review-branch regression: `731 passed in 115.83s (0:01:55)`

## 1.0.0-rc1 — Release Candidate

- Completed requirements-to-test traceability.
- Verified backend acceptance scenarios.
- Verified privacy, security, migration, and partner contracts.
- Frozen the RC1 OpenAPI contract.
- Recorded zero unresolved high-severity defects.
