# PAMSU Python IDE — Current AI Handoff

## Mandatory Reading

Before changing code, every AI assistant must read:

1. `docs/ai/PROJECT_CONTEXT.md`
2. `docs/ai/ROADMAP.md`
3. `docs/ai/WORKFLOW.md`
4. `docs/ai/CURRENT_HANDOFF.md`

These repository files are the authoritative source of truth.

---

## Current Repository State

Current local working branch: `review/backend-p10-review-queue-gradebook`

Backend version: `0.10.0`

Completed pillars:

- Pillar 1 — Core security and domain foundations
- Pillar 2 — OTP registration workflow
- Pillar 3 — API and OpenAPI contracts
- Pillar 4 — Classrooms and enrollment
- Pillar 5 — Activities and test cases
- Pillar 6 — Immutable submissions
- Pillar 7 — Execution requests
- Pillar 8 — Coding sessions and privacy-safe telemetry
- Pillar 9 — Structural evaluation review and manual grading

Current implementation:

- Pillar 10 — Instructor Review Queue and Gradebook APIs

Implemented endpoints:

- `GET /instructors/review-queue`
- `GET /instructors/gradebook`
- `GET /activities/released-grades`

Pillar 10 includes:

- instructor-owned review queues;
- instructor-owned gradebook summaries;
- bounded pagination;
- filtering and deterministic sorting;
- student access to their own released manual grades;
- no raw source code in summary endpoints;
- no unreleased grade exposure to students;
- no automatic grading, plagiarism, cheating, or misconduct verdicts.

Final backend verification must report:

- `220 passed`

Branch policy:

- Review, feature, and fix branches stay local.
- Never push the review branch.
- Merge locally into `dev`.
- Push only `dev`.

---

## Non-Negotiable Rules

- Registration accepts only `@pampangastateu.edu.ph`.
- School IDs contain exactly 10 digits and are stored as strings.
- Clients cannot select account roles.
- Instructor accounts are controlled by the backend allowlist.
- Registration requires OTP verification.
- Submission attempts are immutable.
- The latest accepted attempt is the official attempt.
- Official grades are entered manually by authorized instructors.
- AST, similarity, execution, and session indicators are review-only.
- Automated indicators never assign grades.
- Automated indicators never determine plagiarism, cheating, copying, or misconduct.
- Students never receive unreleased grades.
- Review queue and gradebook summaries never expose raw source code.
- Paste policy remains `internal_only` or `disabled`.
- Blocked external-paste telemetry stores count and timestamp only.
- Clipboard contents and pasted text are never stored.
- Browsing history, screen recordings, webcam data, microphone data, and every keystroke are never collected.
- Student Python code never executes in React or FastAPI.
- Student code executes only through the partner-owned isolated sandbox worker.

---

## Next Planned Pillar

Pillar 11 — In-App Notification and Academic Event Workflow

Target backend version: `0.11.0`

Planned local branch: `review/backend-p11-notification-workflow`

Do not begin Pillar 11 until Pillar 10 passes the full backend suite, is merged locally into `dev`, and `dev` is pushed successfully.
