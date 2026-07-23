# PAMSU Python IDE — Current AI Handoff

## Mandatory Reading

Before changing code, read:

1. `docs/ai/PROJECT_CONTEXT.md`
2. `docs/ai/ROADMAP.md`
3. `docs/ai/WORKFLOW.md`
4. `docs/ai/CURRENT_HANDOFF.md`

These repository files are the authoritative source of truth.

---

## Current Repository State

Current local branch:

```text
review/backend-p16-release-candidate
```

Backend version:

```text
1.0.0-rc1
```

Migration head:

```text
9f2c6e4a1b7d
```

The Pillar 16 review branch must remain local.

Do not push the review branch.

---

## Pillar 16 Status

Pillar 16 — V-Model Verification and Release Candidate

Completed scope:

- requirements-to-test traceability
- backend acceptance verification
- authentication and OTP verification
- classroom and enrollment verification
- activity and paste-policy verification
- immutable submission verification
- isolated execution-contract verification
- coding-session and privacy verification
- evaluation and manual grading verification
- notification verification
- audit-trail verification
- reporting and export verification
- partner-contract verification
- privacy and security negative tests
- migration verification
- OpenAPI release-candidate freeze
- frontend handoff package
- partner handoff package
- defect register
- release notes
- local LLM safety-boundary tests
- version bump to `1.0.0-rc1`

---

## Authoritative Verification Results

```text
Complete review-branch regression:
731 passed in 133.58s (0:02:13)

Execution verification:
75 passed in 32.12s

Evaluation verification:
38 passed in 2.85s

Security verification:
73 passed in 23.51s

Migration verification:
16 passed in 4.62s

Local LLM verification:
18 passed in 0.88s
```

Migration verification:

```text
9f2c6e4a1b7d (head)
No new upgrade operations detected.
```

Frozen OpenAPI checksum:

```text
8225e721e7ae3d1318d5af5ac67377af12cedccab61cd82ce164cdc402ec84b1
```

Unresolved high-severity defects:

```text
0
```

Do not replace these results with estimates.

---

## Release-Candidate Artifacts

```text
docs/ai/P16_REQUIREMENTS_TRACEABILITY.md
docs/ai/P16_TEST_NODE_INVENTORY.txt
docs/ai/P16_OPENAPI_RC1.json
docs/ai/P16_OPENAPI_RC1.sha256
docs/ai/P16_DEFECT_REGISTER.md
docs/ai/P16_RELEASE_NOTES.md
docs/ai/P16_FRONTEND_HANDOFF.md
docs/ai/P16_PARTNER_HANDOFF.md
docs/ai/CURRENT_HANDOFF.md
```

---

## Frozen API Contract

OpenAPI release-candidate version:

```text
1.0.0-rc1
```

Frozen artifact:

```text
docs/ai/P16_OPENAPI_RC1.json
```

Checksum artifact:

```text
docs/ai/P16_OPENAPI_RC1.sha256
```

Frontend and partner integrations must use the frozen RC1 contract.

No unapproved endpoint, role, status, field, or response schema may be introduced after the freeze without an approved release-candidate fix.

---

## Permanent Authorization and Academic Boundaries

- Registration accepts only `@pampangastateu.edu.ph`.
- School ID is exactly 10 digits.
- School ID is stored as a string.
- School ID and email remain unique.
- Roles are controlled only by the backend allowlist.
- OTP verification remains required.
- Plaintext OTP values are never persisted, logged, or returned.
- Classroom and enrollment actions remain ownership-controlled.
- Hidden test cases are never exposed to students.
- Submission attempts are immutable.
- Attempt numbering is backend-controlled.
- The latest accepted attempt becomes official.
- Only the latest accepted official submission may receive an official grade.
- Official grades remain manually controlled by authorized instructors.
- Grade changes do not silently change submission review status.
- Unreleased grades remain hidden from students.
- Students see only their own released manual grades.

---

## Permanent Execution and Review Boundaries

- React never executes student Python.
- FastAPI never executes student Python.
- Student code runs only through the partner-owned isolated sandbox.
- Execution requests are queued by the backend.
- Partner updates require trusted authentication.
- Partner lifecycle updates require valid sequence and correlation data.
- Identical partner retries remain replay-safe.
- Conflicting or out-of-order updates are rejected.
- Student execution idempotency remains scoped to the authenticated student.
- AST indicators are review-only.
- Similarity indicators are review-only.
- Execution indicators are review-only.
- Coding-session indicators are review-only.
- Local LLM output may provide explanations, hints, or draft feedback only.
- Automated indicators and local LLM output never assign grades.
- Automated indicators and local LLM output never determine plagiarism, cheating, copying, misconduct, or academic dishonesty.
- Automated indicators never produce an official risk ranking.

---

## Permanent Privacy Boundaries

Approved aggregate session telemetry is limited to:

- tab-switch count
- blocked-paste count
- run-attempt count
- idle-duration total
- approved timestamps

Prohibited collection and storage:

- clipboard contents
- pasted external text
- browsing history
- individual keystrokes
- screen recordings
- webcam data
- microphone data

Paste policy remains:

```text
internal_only
disabled
```

Blocked-paste telemetry stores count and timestamp only.

Request logs exclude:

- request and response bodies
- query strings
- sensitive headers
- credentials
- OTP values
- JWT values
- partner tokens
- database URLs
- source code
- standard input
- hidden tests
- grade values
- private analytics
- raw exception messages
- tracebacks

---

## Migration State

Migration chain:

```text
18d3ef8f020d  baseline
4b3a1d9e7c25  add execution request idempotency
9f2c6e4a1b7d  optimize proven index coverage
```

Current head:

```text
9f2c6e4a1b7d
```

Observed drift result:

```text
No new upgrade operations detected.
```

Migrations do not run automatically during FastAPI import.

---

## Pillar 16 Commits

```text
df4f9ab docs: add pillar 16 release handoff package
18a3182 chore: freeze pillar 16 rc1 api contract
d0392b4 test: verify local llm safety boundary
ce44d7a test: add pillar 16 release candidate verification
```

---

## Git State and Boundaries

Current review branch:

```text
review/backend-p16-release-candidate
```

The review branch remains local and must not be pushed.

Legacy remote feature, fix, audit, and backup branches existed before Pillar 16 and were not deleted during release-candidate verification.

Only `dev` may be pushed during the Pillar 16 completion procedure.

Do not use:

```powershell
git add .
```

Stage exact files only.

---

## Remaining Completion Sequence

1. Commit this updated handoff.
2. Confirm the review branch working tree is clean.
3. Merge the review branch locally into `dev`.
4. Run the complete backend regression on `dev`.
5. Push only `dev`.
6. Confirm the final working tree is clean.
7. Confirm the review branch was not pushed.

Do not claim final Pillar 16 completion until the post-merge regression passes on `dev`.

---

## Final Verification Commands

From `backend`:

```powershell
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m alembic heads
.\venv\Scripts\python.exe -m alembic check
```

Expected review-branch regression:

```text
731 passed in 133.58s (0:02:13)
```

Expected migration head:

```text
9f2c6e4a1b7d (head)
```

Expected migration drift result:

```text
No new upgrade operations detected.
```

---

## Final Pillar 16 Git Procedure

Commit this handoff, merge locally into `dev`, rerun the complete regression, and push only `dev`.

Do not push:

```text
review/backend-p16-release-candidate
```
