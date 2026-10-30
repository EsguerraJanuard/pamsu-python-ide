# Database backups (zero budget)

Production runs on the Supabase **free tier, which keeps no backups**, and `start.sh` runs `alembic upgrade head` on every Render deploy. This page sets up free, encrypted backups and a tested way to restore them.

| What | Where | Cost |
|---|---|---|
| Backup tool (dump, check, encrypt, rotate, restore) | `ops/backup_database.py` | free |
| Nightly automatic backup | `.github/workflows/database-backup.yml` (GitHub Actions) | free (public repository) |
| Backup before a risky deploy | the same tool, run by hand | free |
| Self-test on GitHub (no secrets, throwaway PostgreSQL 17 container) | `.github/workflows/backup-tool-selftest.yml`: runs when the tool or the backup workflow changes, or by hand | free |

**Why not a Render cron job?** Render cron jobs have no free tier (minimum $1 per month per job), and free Render instances have no persistent disk to keep backups on.

## How the tool works

`python ops/backup_database.py backup` does the following:

1. Connects read-only and checks that `pg_dump` is at least the server's major version (production is PostgreSQL 17).
2. Dumps the `public` schema, which holds every app table plus `alembic_version`, in pg_dump's compressed custom format.
3. Refuses to keep a dump that `pg_restore` can't read, or that lacks `users` or `alembic_version` data.
4. With `BACKUP_ENCRYPTION_KEY` set, encrypts the dump before it reaches the output folder, so no plaintext copy is left.
5. Writes `<file>.json` beside it (size, SHA-256, server version, Alembic revision; no student data).
6. With `--keep N`, deletes all but the newest N backups.

The connection URL is never printed or put on a command line.

Tested on 2026-10-22 on a throwaway PostgreSQL 18.4 server:
- backup, verify, decrypt and restore into an empty database (the same 250 users, revision `b7e4c2a91f03`, and `alembic check` clean);
- rotation;
- the wrong key is refused;
- `--require-encryption` without a key dumps nothing;
- restoring over a database that has tables is refused.

## 1. Create the encryption key (once)

```bash
backend/venv/Scripts/python.exe ops/backup_database.py generate-key
```

Store the printed key in **two** places: the GitHub secret below and a password manager or offline note held by Errol or Januard. Without it, the backups cannot be opened. If the key leaks, generate a new one, replace the secret, and delete the old artifacts.

## 2. Turn on the nightly backup (GitHub Actions)

The repository owner (Januard) does this in **GitHub → repository → Settings → Secrets and variables → Actions**:

1. **Secrets → New repository secret**
   - `BACKUP_DATABASE_URL`: the Supabase **Session pooler** connection string. Errol copies it from Supabase → Project → **Connect** → *Session pooler* (host `aws-…pooler.supabase.com`, port **5432**, user `postgres.<project-ref>`).
     - Not the direct `db.<ref>.supabase.co` host: it is IPv6-only, and GitHub's runners use IPv4.
     - Not port 6543 (transaction mode): pg_dump needs a session.
   - `BACKUP_ENCRYPTION_KEY`: the key from step 1.
2. **Variables → New repository variable:** `DATABASE_BACKUP_ENABLED` = `true`.
3. **Actions → Database backup → Run workflow** once to test it. The run should end with an artifact named `database-backup-N`.

It then runs every day at 02:30 Manila time. Each artifact holds one encrypted `.dump.fernet` file and its manifest, and is kept for 14 days.

> **The repository is public.** Anyone signed in to GitHub can download its Actions artifacts. That is why the workflow refuses to run without the encryption key, and only the encrypted file is uploaded. For extra protection, put the same workflow in a separate **private** repository (free). Check out this repository's `ops/` folder there and keep the secrets in the private one.

GitHub pauses scheduled workflows in a repository with no activity for 60 days. After a long break, open **Actions** and re-enable it.

## 3. Back up by hand before a deploy that migrates the database

Errol should do this before every Render **Manual Deploy** that includes a new migration (for example `b7e4c2a91f03` on 2026-10-22). He needs PostgreSQL **17** client tools (Windows installer: "Command Line Tools" only).

```powershell
$env:BACKUP_DATABASE_URL = "<Session pooler URI>"   # or the direct URI if your network has IPv6
$env:BACKUP_ENCRYPTION_KEY = "<key>"
$env:PG_BIN = "C:\Program Files\PostgreSQL\17\bin"
backend\venv\Scripts\python.exe ops\backup_database.py backup --output-dir $HOME\pamsu-backups --keep 10 --require-encryption
```

Then close the PowerShell window, so the URL and key don't stay in that session.

## 4. Restore

**Always rehearse into an empty database first** (a local PostgreSQL 17, or a new free Supabase project). The tool refuses to restore into a database that already has tables, so it can't overwrite production by mistake.

```powershell
$env:BACKUP_ENCRYPTION_KEY = "<key>"
$env:RESTORE_DATABASE_URL = "postgresql://postgres:<password>@127.0.0.1:5432/pamsu_restore"
backend\venv\Scripts\python.exe ops\backup_database.py verify  pamsu_db_<timestamp>_<revision>.dump.fernet
backend\venv\Scripts\python.exe ops\backup_database.py restore pamsu_db_<timestamp>_<revision>.dump.fernet
```

The restore runs in one transaction: it either completes or changes nothing.

To recover production, restore into a **new** Supabase project, then point Render's `DATABASE_URL` at it (Errol, then Save and deploy). The backup's Alembic revision is in its file name. If it is older than the deployed code, `start.sh` upgrades it on start.

`decrypt FILE` turns an encrypted backup back into a normal `.dump` for any other `pg_restore` use. Delete that plaintext file afterwards.
