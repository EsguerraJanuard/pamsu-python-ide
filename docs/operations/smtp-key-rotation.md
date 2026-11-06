# Rotating the SMTP (Brevo) key

**Why:** the current key was exposed during testing (audit-status.md, "Incident note: real email from test runs", 2026-10-17) and has been an open release blocker since 2026-10-20. Every email depends on this key: account set-up emails, faculty invitations, and password-reset codes.

**Who:** Errol owns the Brevo account and the Render service. Januard can follow along. About 15 minutes.

**What changes:** only the Render environment variable `SMTP_PASS`, and `SMTP_USER` if Brevo shows a different login. No code, no migration.

## Steps

1. **Create the new key.** Brevo → profile menu → **SMTP & API** → **SMTP** tab → **Generate a new SMTP key**.
   - Name it `pamsu-render-2026-10`.
   - Copy the key once. Brevo won't show it again.
   - Note the **SMTP login** on the same page; that is `SMTP_USER`.
2. **Check that the key works before Render uses it.** From the repository folder, in PowerShell:
   ```powershell
   $env:SMTP_HOST = "smtp-relay.brevo.com"; $env:SMTP_PORT = "587"
   $env:SMTP_USER = "<SMTP login from Brevo>"
   $env:SMTP_SENDER_EMAIL = "<the sender address Render uses>"
   backend\venv\Scripts\python.exe ops\check_smtp.py --send-test <your own university email>
   ```
   - It asks for the key without showing it, logs in, and sends one short test email.
   - `535` means the key or login is wrong.
   - "sender refused" means the sender address is not verified: Brevo → **Senders, Domains & Dedicated IPs** → verify it.
3. **Put it on Render.** Render → `pamsu-backend` → **Environment**:
   - set `SMTP_PASS` to the new key;
   - check `SMTP_USER`, `SMTP_HOST` (`smtp-relay.brevo.com`), `SMTP_PORT` (`587`) and `SMTP_SENDER_EMAIL`;
   - click **Save and deploy**.

   `SMTP_HOST` must be set explicitly: the password-reset mailer has no default host.
4. **Test in production.**
   - On the live site, use **Forgot password?** with a test account you control; the code should arrive within a minute.
   - In the Render log, look for `Provisioning email … failed (SMTPAuthenticationError 535)`. That line means the key on Render is wrong.
5. **Revoke the old key.** In Brevo's SMTP tab, delete the old key only after step 4 works. Until then, a quick rollback is possible.
6. **Record it.** Add the date to audit-status.md ("SMTP key rotated"). Never write the key itself into a file or a commit.

## If something goes wrong

- **No emails after the deploy:** check step 3's values, then run `ops/check_smtp.py` again with the key from Render. If the new key fails and the old one hasn't been deleted yet, put the old key back and Save and deploy. Then generate a fresh key and start again.
- **Brevo shows "account suspended" or a sending limit:** the free plan allows 300 emails a day. Masterlist imports of more than 300 students should be split across days.
