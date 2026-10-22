# Handoff for Errol: October 22 sprint

_Prepared 2026-10-22. Code on `dev`: `404d88a` (the sprint), `8e9b377` (PostgreSQL 17 record) and the gap follow-up commit after them. Vercel deploys each push to `dev` automatically; **the backend waits for your Manual Deploy.** Full details: `audit-status.md`, sections "October 22 handoff" and "October 22 follow-up"._

## 1. Executive summary

- **Practice submit no longer waits on Judge0.** It answers in about 150 ms (it used to block up to 15 s) and the page polls for the result. This needs one additive migration, `b7e4c2a91f03`.
- **The remaining owner decisions are made and built:**
  - the legacy routes are removed;
  - the enrollment rules are set;
  - faculty invites no longer email a password;
  - three MIS features are added.
- **Ops tooling is added at zero cost:** encrypted `pg_dump` backups with a nightly GitHub Action, and a Brevo key rotation guide with a checker script.
- **Testing:** the backend suite passed (1104 passed, 0 failed). The migration and concurrency suites passed on PostgreSQL **17.6** and 18.4.
- **Still to do:** your deploy, the key rotation, the backup secrets, and the smoke test.

## 2. Technical changelog

### Judge0 async practice submit: migration `b7e4c2a91f03`
- **Flow** (same pattern as the IDE Run button):
  1. `POST /practice/tasks/{id}/submit` saves a `pending` attempt and queues the Celery task `dispatch_practice_attempt`. It returns at once with `status: "pending"` and `attempt_id`.
  2. The worker POSTs to Judge0 with `callback_url = WEBHOOK_BASE_URL/practice/internal/judge0-callback?attempt_id=…&correlation_id=…`. It does not use `wait=true`, has a 10 s timeout, and retries twice, 3 s apart.
  3. Judge0 calls back with `PUT`. The handler records the verdict (status 3 plus the AST check at the admin default strictness) and counts the try in `practice_progress`.
  4. The page polls `GET /practice/attempts/{id}` every 1.5 s (limit 90/min per student).
- **Cost unchanged:** still exactly one Judge0 call per attempt. Nothing polls Judge0.
- **States:** `pending` → `completed` (judged) or `failed`.
  - `failed` means the code never ran: queue down, Judge0 status 13/14/missing, or no answer within **120 s** (closed the next time the page reads it).
  - Failed and pending attempts don't count as tries, are excluded from growth stats, and can't request an AI hint (409 while pending, 400 when failed).
- **Callback security:** the callback is public, like the IDE one. It is bound by a random UUID `correlation_id` that only the server and Judge0 see; students never get it. A wrong pair gets 404; a finished attempt gets 409, and nothing changes.
- **Concurrency:**
  - the attempt row is locked `FOR UPDATE`, so a duplicate callback is applied once;
  - the progress row is locked, and a savepoint plus the unique `(student_id, task_id)` constraint make two simultaneous verdicts count correctly;
  - the 120 s expiry is a conditional `UPDATE … WHERE status = 'pending'`, so it never overwrites a verdict.
- **Migration** `b7e4c2a91f03` (down revision `61330560eec5`, single head):
  - adds `practice_attempts.status` (VARCHAR(20) NOT NULL DEFAULT `'completed'`, CHECK `ck_practice_attempts_status`), `correlation_id` (VARCHAR(36), unique) and `completed_at`;
  - additive only: existing rows become `completed`, and old code still works during the switch-over;
  - `lock_timeout` 10 s;
  - downgrade refuses while any attempt is pending or failed.
- **Submissions cleanup:**
  - `POST/GET /execution/submissions/…` were removed (unused by the frontend; now 404);
  - `POST /submissions/` is the only creator of "submit" runs: `POST /execution/requests/` refuses `request_kind: "submit"` with 409;
  - run requests are limited to **5 per 10 s per student**.
- **Frontend** (`PracticeWorkspace.jsx`): polls until done and rides out up to two failed polls in a row. It also works with the current production backend, which still answers synchronously until you deploy.
- **No paid double runs** (follow-up): after a failed send, `judge0_dispatch_outcome()` decides:
  - retry only when Judge0 certainly didn't queue the code (connect error, 429, 5xx);
  - close the attempt at once on another 4xx;
  - when the answer was lost after sending, leave it pending (the callback or the 120 s expiry finishes it).
- **IDE Run race fix** (follow-up; a real bug in today's production code):
  - `dispatch_to_partner` used to set `running` after Judge0 answered its POST. If the callback had already arrived, that overwrote `completed`, and the run looked stuck.
  - Now "running" is written only on a request that is still `queued`, "failed" only on one nothing has answered, and a retry after an answer sends nothing.
- **Contract test and live run against `mock_judge0`** (now a Judge0 CE stand-in: same `/submissions` API, base64 fields, status ids, PUT callback):
  - the real worker code covers practice (pass, wrong output, runtime error, time limit) and the IDE Run;
  - over real HTTP, practice answered in 122–149 ms and finished in 1.4–2.0 s.
  - Real RapidAPI Judge0 is still only testable in production.

### PostgreSQL 17 test run
- **Binaries:** the official EDB `postgresql-17.6-1-windows-x64-binaries.zip` (the production version), run on a throwaway local cluster. SHA-256 is in `audit-status.md`.
- **Suites:** **28 passed, 0 skipped**:
  - the full migration chain (up, down to base, up, `alembic check`);
  - the admin-audit and practice-status migration suites;
  - all five concurrency suites, including the new practice-callback races;
  - Redis TLS.
- **Stability:** the concurrency suites passed **5 runs in a row**. The same 28 also pass on 18.4.
- **Production-like upgrade:** the demo semester (183 students, 1,862 attempts) at `61330560eec5` upgraded to `b7e4c2a91f03` with every row `completed`, and the migration step took **well under a second**.

### Free automated backups (`pg_dump`)
- **`ops/backup_database.py`** has five commands: `backup | verify | decrypt | restore | generate-key`.
  - Backs up the `public` schema in pg_dump's custom format, after checking that pg_dump's major version is at least the server's.
  - Rejects dumps without `users` or `alembic_version` data.
  - Fernet-encrypts the dump before it reaches the output folder.
  - Writes a JSON manifest (SHA-256 and revision; no data). `--keep N` rotates old backups.
  - `restore` works **only into an empty database**, in one transaction.
  - The connection URL is never printed or put on a command line.
- **`.github/workflows/database-backup.yml`** runs nightly at 02:30 Manila, or on demand.
  - It installs `postgresql-client-17` and uploads only the encrypted file, kept 14 days.
  - It is **off until** the variable `DATABASE_BACKUP_ENABLED=true` and the secrets `BACKUP_DATABASE_URL` and `BACKUP_ENCRYPTION_KEY` exist.
  - `BACKUP_DATABASE_URL` must be the **Supabase Session pooler** URI on port 5432: GitHub runners are IPv4-only, and port 6543 doesn't work with pg_dump.
- **Why not Render cron:** it has no free tier ($1/month minimum per job), and the free instance has no disk.
- **Tested** on 17.6 and 18.4: backup → verify → restore, a wrong key refused, a missing key refused, a restore over a database with tables refused.
- **Self-test on GitHub** (follow-up): `.github/workflows/backup-tool-selftest.yml` runs the same client install, a backup, a restore and both safety guards against a throwaway `postgres:17` container. It needs no secrets and runs when the tool or the workflow changes.
- **Guide:** `docs/operations/database-backups.md`.

### MIS dashboard features
- **Show guests:** a switch in the Student directory (`GET /admin/users?include_guests=true`). Guest rows get a "Guest" badge and only Suspend/Activate. Account lists now carry `is_guest`.
- **School ID editing:** in the Edit dialog, students only. `PATCH /admin/users/{id}` with `school_id` (10 digits or `2026-00001`).
  - Another account using the ID gets 409; faculty get 400.
  - Audited as `user_updated` with `changed_fields: ["school_id"]`, never the value.
- **Re-apply pending:** a button on each active student row (`POST /admin/students/{id}/pending-enrollments/apply`).
- **Queued class enrollments** panel, with "Ready to apply" and "Waiting" views and per-row Apply. It uses the new **admin-only** `GET /admin/pending-enrollments`, and each row shows why it waits: no account, class archived, or suspended.
- **Faculty invites:** no password field.
  - The account is created with an unusable password, and the welcome email links to "Forgot password?" (one-time code).
  - Audit metadata gets `sign_in_setup`.
- **Enrollment rules:**
  - bulk enroll reports **suspended** students (new `suspended` count) and **self-service guests** (counted as `ineligible`) instead of enrolling them;
  - the pending-enrollment retry refuses guests.
- **Fix:** `ClassroomResponse.section` is optional, so a class without a section no longer makes the class lists return 500.

### SMTP/Brevo key rotation
Guide: `docs/operations/smtp-key-rotation.md`. Checker: `ops/check_smtp.py`, which asks for the key with hidden input and prints only SMTP codes.

1. In Brevo → **SMTP & API → SMTP**, generate a new key named `pamsu-render-2026-10` and note the SMTP login.
2. Check it before Render uses it:
   ```powershell
   backend\venv\Scripts\python.exe ops\check_smtp.py --send-test <your email>
   ```
   - `535` means a wrong key or login;
   - "sender refused" means you need to verify the sender in Brevo.
3. On Render, set `SMTP_PASS` (and check `SMTP_USER`, `SMTP_HOST=smtp-relay.brevo.com`, `SMTP_PORT=587`, `SMTP_SENDER_EMAIL`), then **Save and deploy**. `SMTP_HOST` must be set explicitly: the reset-code mailer has no default.
4. On the live site, test **Forgot password?**. In the Render log, `SMTPAuthenticationError 535` means the key is wrong.
5. Delete the old key in Brevo only after step 4 works.

## 3. Pending tasks

### Deploy steps (Errol)
- [ ] **Rotate the Brevo key** (steps above).
- [ ] **Take a manual backup before deploying.** You need the PostgreSQL 17 client tools:
  ```powershell
  backend\venv\Scripts\python.exe ops\backup_database.py backup --output-dir $HOME\pamsu-backups --keep 10 --require-encryption
  ```
  This needs `BACKUP_DATABASE_URL`, `BACKUP_ENCRYPTION_KEY` and `PG_BIN` set; see guide §3.
- [ ] **Manual Deploy `dev`** (at `8e9b377` or later).
  - The log must show `Running upgrade 61330560eec5 -> b7e4c2a91f03`.
  - Check that `WEBHOOK_BASE_URL` is still set and the Celery worker started; `start.sh` runs it in the same container.
- [ ] **After the deploy, check:**
  - [ ] a correct practice submit shows "Passed" within a few seconds;
  - [ ] a wrong submit shows the error and the AI Tutor hint;
  - [ ] the IDE Run still works;
  - [ ] an admin School ID edit saves, and the Queued class enrollments panel loads;
  - [ ] a new faculty account gets the set-password email, with no password in it.
- [ ] Send Januard the **Supabase Session pooler URI** privately, for the backup secret.
- [ ] Update **your local AGENTS.md**. It is gitignored. The approved rule is `gemini-3.8-flash`, falling back to `gemini-3.6-flash` only on 503/429.

### Januard
- [ ] After pushing the follow-up commit, check that **Actions → Backup tool self-test** passes. It runs by itself because the workflow is new.
- [ ] Run `ops/backup_database.py generate-key` and keep the key offline as well.
- [ ] Add the secrets `BACKUP_DATABASE_URL` and `BACKUP_ENCRYPTION_KEY`, and the variable `DATABASE_BACKUP_ENABLED=true`. Then run **Actions → Database backup** once.

### Both
- [ ] Run the **production smoke test** (the list in `audit-status.md`, 2026-10-21). It has not been done yet.

### Known gaps and untested edge cases (after the follow-up)
- [ ] **Real Judge0 (RapidAPI) is only testable in production.** The practice callback is proven against a Judge0-shaped mock and over real HTTP, and the IDE Run already uses the same callback mechanism in production. If the callback can't reach `WEBHOOK_BASE_URL`, attempts close as "could not be checked" after 120 s. The post-deploy checks above cover this.
- [ ] **Until your deploy, faculty invites fall back to the old flow:** the old backend still requires a password and emails it, so the UI generates one and shows it to MIS. School ID editing and the queued-enrollments panel show "needs the latest server update" until then.
- [ ] **The nightly backup itself** needs the secrets (Januard) and one manual run. The new self-test proves the install, tool and restore on GitHub, but not the Supabase connection.
  - Artifacts in this **public** repo are encrypted but downloadable; a private repo copy is safer.
  - GitHub pauses scheduled workflows after 60 days with no repo activity.
- [ ] The **IDE Run** still retries after a lost answer, unlike practice: execution requests have no expiry, so not retrying could leave a run waiting forever. A duplicate is refused (409), and the race fix keeps the first result.
- [ ] Tabs opened before Vercel deployed `404d88a` and still open at your deploy show "Checking your code…" without polling until they reload. `autoUpdate` fixes this on the next page load.
- [ ] The single-student form (`POST /admin/students`) still emails an MIS-chosen temporary password, per Januard's 2026-10-21 spec. Switching it to the password-free invite is recommended.
- [ ] Brevo's free plan is ~300 emails a day. Masterlist uploads that create more than 250 accounts now show a warning in the UI, but the limit itself remains.
- [ ] The local venv is Python 3.13; Render is 3.11.4. `greenlet==3.2.5` has no 3.13 Windows build, so a few pins differ locally. A Python 3.11 venv would match production exactly.
- [ ] Not done (not requested): admin dark mode, and rebuilding `PracticeModuleManager.jsx`/`ActivityEditor.jsx` on `PageShell`.
- [x] ~~Practice dispatch could pay for two runs~~: fixed (no resend after a lost answer).
- [x] ~~IDE Run could look stuck after an early callback~~: fixed.
- [x] ~~`mock_judge0` outdated~~: rewritten as a Judge0 CE stand-in, with a contract test.
- [x] ~~Backup workflow never run on GitHub~~: self-test workflow added.
- [x] ~~Windows test runs ~45 min; 3 AI Tutor tests skipped~~: 6.6 min by default; `google-genai` installed, 39/39.
