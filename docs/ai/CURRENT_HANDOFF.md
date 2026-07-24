# PAMSU Python IDE — Current AI Handoff

## Current State

Branch: `review/backend-final-release-1.0.0`
Backend version: `1.0.0`
Migration head: `9f2c6e4a1b7d`

The final-release review branch must remain local.

## Final Release Verification

- Review-branch regression: `731 passed in 115.83s (0:01:55)`
- Alembic head: `9f2c6e4a1b7d`
- Migration drift: none detected
- Final OpenAPI checksum: `c962d2ce3924bc2bb3e064941715a4c21803dfffa2256839b6da153679aa0560`
- Unresolved high-severity defects: `0`

## Final Release Scope

- Version promotion from `1.0.0-rc1` to `1.0.0`
- Final OpenAPI freeze
- Final changelog and handoff
- No new features
- No API contract changes except the version string

## Permanent Boundaries

- Student Python never executes in React or FastAPI.
- Student code executes only in the partner-owned isolated sandbox.
- Official grades remain manually controlled by authorized instructors.
- Automated indicators and local LLM output never assign grades or determine misconduct.
- Students see only their own permitted data and released grades.
- Clipboard contents, pasted text, browsing history, screen, webcam, microphone, and individual keystrokes are not collected.
- Feature and review branches remain local.
- Only `dev` is pushed.

## Remaining Procedure

1. Commit final-release documentation.
2. Merge locally into `dev`.
3. Run the complete backend regression on `dev`.
4. Update the final handoff and roadmap.
5. Push only `dev`.
