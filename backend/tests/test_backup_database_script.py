"""
ops/backup_database.py: the zero-budget backup tool (no database needed here;
the full dump/restore round trip was run against PostgreSQL 18.4, see
audit-status.md, 2026-10-22).
"""

import importlib.util
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

SCRIPT = Path(__file__).resolve().parents[2] / "ops" / "backup_database.py"
spec = importlib.util.spec_from_file_location("backup_database", SCRIPT)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in ("BACKUP_DATABASE_URL", "DATABASE_URL", "BACKUP_ENCRYPTION_KEY", "RESTORE_DATABASE_URL", "PG_BIN"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("url", [
    "postgres://u:p@db.example.com:5432/postgres",
    "postgresql+psycopg2://u:p@db.example.com:5432/postgres",
])
def test_sqlalchemy_and_heroku_style_urls_become_libpq_urls(monkeypatch, url):
    monkeypatch.setenv("DATABASE_URL", url)

    assert backup.database_url() == "postgresql://u:p@db.example.com:5432/postgres"


def test_the_backup_url_wins_over_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://app@one/db")
    monkeypatch.setenv("BACKUP_DATABASE_URL", "postgresql://backup@two/db")

    assert backup.database_url() == "postgresql://backup@two/db"


def test_a_missing_or_foreign_url_is_refused(monkeypatch):
    with pytest.raises(backup.BackupError, match="Set BACKUP_DATABASE_URL"):
        backup.database_url()
    monkeypatch.setenv("DATABASE_URL", "sqlite:///x.db")
    with pytest.raises(backup.BackupError, match="PostgreSQL"):
        backup.database_url()


def test_credentials_go_to_libpq_variables_and_remote_hosts_require_tls():
    env = backup.libpq_environment(
        "postgresql://postgres.abcdef:p%40ss%2Fword@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
    )

    assert env["PGUSER"] == "postgres.abcdef"
    assert env["PGPASSWORD"] == "p@ss/word"
    assert env["PGHOST"] == "aws-0-ap-southeast-1.pooler.supabase.com"
    assert env["PGSSLMODE"] == "require"
    assert backup.libpq_environment("postgresql://postgres@127.0.0.1:55418/x").get("PGSSLMODE") is None
    assert backup.libpq_environment("postgresql://u@h/x?sslmode=verify-full")["PGSSLMODE"] == "verify-full"


def test_encryption_round_trip_and_wrong_key(tmp_path):
    key = Fernet.generate_key().decode()
    plain = tmp_path / "a.dump"
    plain.write_bytes(b"PGDMP student 2026000001 row")
    sealed = tmp_path / "a.dump.fernet"
    backup.encrypt_file(plain, sealed, key)

    assert b"2026000001" not in sealed.read_bytes()
    opened = tmp_path / "b.dump"
    backup.decrypt_file(sealed, opened, key)
    assert opened.read_bytes() == plain.read_bytes()

    other = Fernet.generate_key().decode()
    with pytest.raises(backup.BackupError, match="Wrong key"):
        backup.decrypt_file(sealed, tmp_path / "c.dump", other)
    with pytest.raises(backup.BackupError, match="not a valid key"):
        backup.fernet("not-a-key")


def test_backup_refuses_to_start_without_a_key_when_encryption_is_required(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example.com/postgres")

    def no_connection(*args, **kwargs):
        raise AssertionError("nothing may be dumped")

    monkeypatch.setattr(backup, "server_facts", no_connection)

    assert backup.main(["backup", "--output-dir", str(tmp_path / "out"), "--require-encryption"]) == 1
    assert not (tmp_path / "out").exists()


def test_a_dump_without_the_app_tables_is_rejected():
    entries = ["3345; 0 16390 TABLE DATA public users postgres"]

    with pytest.raises(backup.BackupError, match="public.alembic_version"):
        backup.check_contents(entries)
    assert backup.check_contents(entries + ["3346; 0 16400 TABLE DATA public alembic_version postgres"]) == 2


def test_rotation_keeps_the_newest_backups_and_their_manifests(tmp_path):
    names = [f"pamsu_db_2026102{day}T000000Z_rev.dump.fernet" for day in range(1, 5)]
    for name in names:
        (tmp_path / name).write_bytes(b"x")
        (tmp_path / (name + ".json")).write_text("{}")
    (tmp_path / "unrelated.txt").write_text("keep me")

    removed = backup.rotate(tmp_path, keep=2)

    assert removed == names[:2][::-1]
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(
        names[2:] + [name + ".json" for name in names[2:]] + ["unrelated.txt"]
    )


def test_an_old_pg_dump_is_refused_before_dumping(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example.com/postgres")
    monkeypatch.setattr(backup, "server_facts", lambda env: {
        "server_major": 17, "server_version_num": 170006, "alembic_revision": "b7e4c2a91f03", "tables": 27})
    monkeypatch.setattr(backup, "tool", lambda name: name)
    monkeypatch.setattr(backup, "tool_major_version", lambda path: 16)

    def no_dump(*args, **kwargs):
        raise AssertionError("pg_dump must not run")

    monkeypatch.setattr(backup.subprocess, "run", no_dump)

    assert backup.main(["backup", "--output-dir", str(tmp_path)]) == 1
    assert list(tmp_path.iterdir()) == []
