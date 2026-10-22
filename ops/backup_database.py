#!/usr/bin/env python3
"""
Zero-budget backups of the PAMS(U) IDE database (Supabase free tier: none).

    python ops/backup_database.py backup [--output-dir backups] [--keep 14] [--require-encryption]
    python ops/backup_database.py verify FILE
    python ops/backup_database.py decrypt FILE [--output PATH]
    python ops/backup_database.py restore FILE        (into the EMPTY database in RESTORE_DATABASE_URL)
    python ops/backup_database.py generate-key

backup
    Dumps the `public` schema (every table the app uses, alembic_version
    included) with pg_dump's custom format, checks that pg_restore can read
    it, and writes a small JSON manifest beside it (size, SHA-256, server
    version, Alembic revision; no data). With BACKUP_ENCRYPTION_KEY set the
    dump is encrypted (Fernet: AES-128-CBC + HMAC-SHA256) before it reaches
    the output folder, so no plaintext copy is left behind. --keep N deletes
    all but the newest N backups in that folder.

Environment
    BACKUP_DATABASE_URL     the database to back up (falls back to DATABASE_URL).
                            For Supabase from an IPv4-only machine (GitHub
                            Actions), use the Session pooler URI (port 5432),
                            not the direct host (IPv6) or port 6543.
    BACKUP_ENCRYPTION_KEY   a key from `generate-key`. Keep a copy outside the
                            machine that holds the backups: without it they
                            cannot be restored.
    PG_BIN                  folder with pg_dump/pg_restore (default: PATH).

The connection URL is never printed or put on a command line: pg_dump gets
it through libpq environment variables. The tool only reads the database.
Requires psycopg2 and cryptography (both in backend/requirements.txt).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

DUMP_SUFFIX = ".dump"
ENCRYPTED_SUFFIX = ".dump.fernet"
FILE_PREFIX = "pamsu_db_"
# Fernet works on whole files; the free-tier database is capped at 500 MB and
# a compressed dump of it is far smaller.
MAX_ENCRYPT_BYTES = 1024 * 1024 * 1024
REQUIRED_TABLES = ("alembic_version", "users")


class BackupError(RuntimeError):
    """A failure with a message that is safe to print (no credentials)."""


# ------------------------------------------------------------------ helpers


def database_url() -> str:
    url = (os.getenv("BACKUP_DATABASE_URL") or os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise BackupError("Set BACKUP_DATABASE_URL (or DATABASE_URL) to the database to back up.")
    # SQLAlchemy-style URLs (postgresql+psycopg2://) are not libpq URIs.
    url = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql://", url)
    if not url.startswith("postgresql://"):
        raise BackupError("The database URL must be a PostgreSQL URL (postgresql://…).")
    return url


def libpq_environment(url: str) -> dict[str, str]:
    """libpq variables for pg_dump, so the password never appears in a process list."""

    parts = urlsplit(url)
    query = {key: values[-1] for key, values in parse_qs(parts.query).items()}
    env = {
        "PGHOST": parts.hostname or "",
        "PGPORT": str(parts.port or 5432),
        "PGUSER": unquote(parts.username or ""),
        "PGPASSWORD": unquote(parts.password or ""),
        "PGDATABASE": unquote(parts.path.lstrip("/")) or "postgres",
        "PGCONNECT_TIMEOUT": "20",
        "PGAPPNAME": "pamsu-backup",
    }
    if "sslmode" in query:
        env["PGSSLMODE"] = query["sslmode"]
    elif env["PGHOST"] not in ("localhost", "127.0.0.1", "::1"):
        # Supabase and other hosted servers: never send the password in clear.
        env["PGSSLMODE"] = "require"
    return {key: value for key, value in env.items() if value}


def tool(name: str) -> str:
    folder = os.getenv("PG_BIN")
    if folder:
        candidate = Path(folder) / (name + (".exe" if os.name == "nt" else ""))
        if candidate.exists():
            return str(candidate)
        raise BackupError(f"{name} was not found in PG_BIN.")
    found = shutil.which(name)
    if not found:
        raise BackupError(f"{name} is not installed (or set PG_BIN to the PostgreSQL bin folder).")
    return found


def tool_major_version(path: str) -> int:
    output = subprocess.run([path, "--version"], capture_output=True, text=True, check=True).stdout
    match = re.search(r"(\d+)(?:\.\d+)?", output)
    if not match:
        raise BackupError(f"Could not read the version of {Path(path).name}.")
    return int(match.group(1))


def server_facts(env: dict[str, str]) -> dict:
    import psycopg2

    try:
        connection = psycopg2.connect(
            host=env.get("PGHOST"), port=env.get("PGPORT"), user=env.get("PGUSER"),
            password=env.get("PGPASSWORD"), dbname=env.get("PGDATABASE"),
            sslmode=env.get("PGSSLMODE", "prefer"), connect_timeout=20, application_name="pamsu-backup",
        )
    except psycopg2.Error as error:
        # Class name only: libpq messages can quote the host and user.
        raise BackupError(f"Could not connect to the database ({type(error).__name__}).") from None
    try:
        connection.set_session(readonly=True, autocommit=True)
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version_num")
            version_num = int(cursor.fetchone()[0])
            cursor.execute("SELECT to_regclass('public.alembic_version') IS NOT NULL")
            revision = None
            if cursor.fetchone()[0]:
                cursor.execute("SELECT version_num FROM public.alembic_version")
                row = cursor.fetchone()
                revision = row[0] if row else None
            cursor.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
            tables = int(cursor.fetchone()[0])
    finally:
        connection.close()
    return {"server_major": version_num // 10000, "server_version_num": version_num,
            "alembic_revision": revision, "tables": tables}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fernet(key: str):
    from cryptography.fernet import Fernet

    try:
        return Fernet(key.strip().encode())
    except (ValueError, TypeError):
        raise BackupError("BACKUP_ENCRYPTION_KEY is not a valid key (create one with generate-key).") from None


def encrypt_file(source: Path, target: Path, key: str) -> None:
    if source.stat().st_size > MAX_ENCRYPT_BYTES:
        raise BackupError("The dump is larger than 1 GiB; encrypt it with a streaming tool instead.")
    target.write_bytes(fernet(key).encrypt(source.read_bytes()))


def decrypt_file(source: Path, target: Path, key: str) -> None:
    from cryptography.fernet import InvalidToken

    try:
        target.write_bytes(fernet(key).decrypt(source.read_bytes()))
    except InvalidToken:
        raise BackupError("Wrong key, or the file is damaged: it could not be decrypted.") from None


def list_dump(path: Path) -> list[str]:
    """pg_restore's table of contents for a custom-format dump (proves it is readable)."""

    result = subprocess.run([tool("pg_restore"), "--list", str(path)], capture_output=True, text=True)
    if result.returncode != 0:
        raise BackupError("pg_restore could not read the dump; it is not a valid backup.")
    return [line for line in result.stdout.splitlines() if line and not line.startswith(";")]


def check_contents(entries: list[str]) -> int:
    data = [entry for entry in entries if " TABLE DATA public " in entry]
    for table in REQUIRED_TABLES:
        if not any(re.search(rf" TABLE DATA public {table} ", entry + " ") for entry in data):
            raise BackupError(f"The dump has no data for public.{table}; refusing to keep it.")
    return len(data)


def rotate(folder: Path, keep: int) -> list[str]:
    backups = sorted(
        (path for path in folder.iterdir()
         if path.name.startswith(FILE_PREFIX) and path.name.endswith((DUMP_SUFFIX, ENCRYPTED_SUFFIX))),
        key=lambda path: path.name,
        reverse=True,
    )
    removed = []
    for path in backups[keep:]:
        path.unlink()
        manifest = path.with_name(path.name + ".json")
        manifest.unlink(missing_ok=True)
        removed.append(path.name)
    return removed


# ------------------------------------------------------------------ commands


def command_backup(args) -> int:
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
    if args.require_encryption and not key:
        raise BackupError("--require-encryption is set but BACKUP_ENCRYPTION_KEY is empty; nothing was dumped.")
    if key:
        fernet(key)  # fail before dumping if the key is malformed

    env = libpq_environment(database_url())
    pg_dump = tool("pg_dump")
    facts = server_facts(env)
    dump_major = tool_major_version(pg_dump)
    if dump_major < facts["server_major"]:
        raise BackupError(
            f"pg_dump {dump_major} cannot dump a PostgreSQL {facts['server_major']} server. "
            f"Install the PostgreSQL {facts['server_major']} client tools (or newer)."
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"{FILE_PREFIX}{stamp}_{facts['alembic_revision'] or 'norevision'}"

    # The plaintext dump only ever exists in a private temporary folder.
    with tempfile.TemporaryDirectory(prefix="pamsu-backup-") as work:
        plain = Path(work) / (base + DUMP_SUFFIX)
        result = subprocess.run(
            [pg_dump, "--format=custom", "--compress=6", "--no-owner", "--no-privileges",
             "--schema=public", "--file", str(plain)],
            env={**os.environ, **env}, capture_output=True, text=True,
        )
        if result.returncode != 0 or not plain.exists():
            # pg_dump's messages carry no password (it came from PGPASSWORD).
            reason = (result.stderr or "").strip().splitlines()[-1:] or ["unknown error"]
            raise BackupError(f"pg_dump failed: {reason[0]}")

        data_entries = check_contents(list_dump(plain))
        if key:
            final = output_dir / (base + ENCRYPTED_SUFFIX)
            encrypt_file(plain, final, key)
        else:
            final = output_dir / (base + DUMP_SUFFIX)
            shutil.move(str(plain), final)

    manifest = {
        "file": final.name,
        "created_at": stamp,
        "bytes": final.stat().st_size,
        "sha256": sha256_of(final),
        "encrypted": bool(key),
        "server_version_num": facts["server_version_num"],
        "pg_dump_major": dump_major,
        "alembic_revision": facts["alembic_revision"],
        "public_tables": facts["tables"],
        "tables_with_data": data_entries,
    }
    final.with_name(final.name + ".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    removed = rotate(output_dir, args.keep) if args.keep else []
    print(f"Backup written: {final} ({manifest['bytes']:,} bytes, {'encrypted' if key else 'NOT encrypted'})")
    print(f"Alembic revision {manifest['alembic_revision']}, {data_entries} tables with data.")
    if removed:
        print(f"Removed {len(removed)} older backup(s).")
    if not key:
        print("Warning: this file holds student records in plain form. Keep it off shared drives.")
    return 0


def command_verify(args) -> int:
    path = Path(args.file)
    with tempfile.TemporaryDirectory(prefix="pamsu-verify-") as work:
        if path.name.endswith(ENCRYPTED_SUFFIX):
            key = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
            if not key:
                raise BackupError("This backup is encrypted: set BACKUP_ENCRYPTION_KEY.")
            plain = Path(work) / "check.dump"
            decrypt_file(path, plain, key)
        else:
            plain = path
        data_entries = check_contents(list_dump(plain))
    manifest = path.with_name(path.name + ".json")
    if manifest.exists():
        expected = json.loads(manifest.read_text(encoding="utf-8")).get("sha256")
        if expected and expected != sha256_of(path):
            raise BackupError("The file does not match its manifest checksum.")
    print(f"OK: {path.name} is a readable backup with {data_entries} tables with data.")
    return 0


def command_decrypt(args) -> int:
    key = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
    if not key:
        raise BackupError("Set BACKUP_ENCRYPTION_KEY to the key the backup was made with.")
    source = Path(args.file)
    target = Path(args.output) if args.output else source.with_name(source.name.removesuffix(".fernet"))
    decrypt_file(source, target, key)
    print(f"Decrypted to {target}. Restore it with pg_restore (see docs/operations/database-backups.md).")
    return 0


def command_restore(args) -> int:
    """Restore into an EMPTY database (a restore drill, or a replacement project)."""

    target = os.getenv("RESTORE_DATABASE_URL", "").strip()
    if not target:
        raise BackupError("Set RESTORE_DATABASE_URL to an empty database to restore into.")
    target = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql://", target)
    env = libpq_environment(target)
    if server_facts(env)["tables"]:
        # Never over a live database: the target must have no tables in public.
        raise BackupError("The target database already has tables in its public schema; restore only into an empty one.")

    source = Path(args.file)
    with tempfile.TemporaryDirectory(prefix="pamsu-restore-") as work:
        plain = source
        if source.name.endswith(ENCRYPTED_SUFFIX):
            key = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
            if not key:
                raise BackupError("This backup is encrypted: set BACKUP_ENCRYPTION_KEY.")
            plain = Path(work) / "restore.dump"
            decrypt_file(source, plain, key)
        # A new database already has the public schema: skip only that entry.
        entries = subprocess.run([tool("pg_restore"), "--list", str(plain)], capture_output=True, text=True, check=True)
        listing = Path(work) / "restore.list"
        listing.write_text(
            "\n".join(line for line in entries.stdout.splitlines() if not re.search(r" SCHEMA - public ", line)) + "\n",
            encoding="utf-8",
        )
        # --dbname takes only the database name; host, user and password come
        # from the libpq variables. Without it pg_restore would print SQL.
        result = subprocess.run(
            [tool("pg_restore"), "--no-owner", "--no-privileges", "--exit-on-error", "--single-transaction",
             "--use-list", str(listing), "--dbname", env.get("PGDATABASE", "postgres"), str(plain)],
            env={**os.environ, **env}, capture_output=True, text=True,
        )
        if result.returncode != 0:
            reason = (result.stderr or "").strip().splitlines()[-1:] or ["unknown error"]
            raise BackupError(f"pg_restore failed and rolled back: {reason[0]}")

    facts = server_facts(env)
    print(f"Restored {facts['tables']} tables at Alembic revision {facts['alembic_revision']}.")
    return 0


def command_generate_key(_args) -> int:
    from cryptography.fernet import Fernet

    print(Fernet.generate_key().decode())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup", help="dump, check and (optionally) encrypt the database")
    backup.add_argument("--output-dir", default="backups")
    backup.add_argument("--keep", type=int, default=0, help="keep only the newest N backups in the folder")
    backup.add_argument("--require-encryption", action="store_true",
                        help="refuse to run without BACKUP_ENCRYPTION_KEY")
    backup.set_defaults(handler=command_backup)

    verify = sub.add_parser("verify", help="check that a backup file can be restored")
    verify.add_argument("file")
    verify.set_defaults(handler=command_verify)

    decrypt = sub.add_parser("decrypt", help="decrypt an encrypted backup for pg_restore")
    decrypt.add_argument("file")
    decrypt.add_argument("--output")
    decrypt.set_defaults(handler=command_decrypt)

    restore = sub.add_parser("restore", help="restore a backup into the EMPTY database in RESTORE_DATABASE_URL")
    restore.add_argument("file")
    restore.set_defaults(handler=command_restore)

    sub.add_parser("generate-key", help="print a new encryption key").set_defaults(handler=command_generate_key)

    args = parser.parse_args(argv)
    if getattr(args, "keep", 0) and args.keep < 1:
        parser.error("--keep must be at least 1")
    try:
        return args.handler(args)
    except BackupError as error:
        print(f"Backup error: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"Backup error: {Path(str(error.cmd[0])).name} failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
