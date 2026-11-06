"""Extra sign-in protection for faculty (instructor and admin) accounts.

Panel recommendation (oral defense, 2026-09-30): add a security mechanism
for faculty login. Faculty accounts can create activities, see every
student's code and release grades, so repeated wrong passwords lock the
account for a short time.

The count comes from the immutable audit log (login_failed records), so the
lock holds across server restarts and while Redis is unavailable. Attempts
refused because of the lock are recorded as "denied" and do not extend it.
"""

from datetime import datetime, timedelta, timezone

from app.models.domain_models import AuditRecord, User
from sqlalchemy.orm import Session

FACULTY_ROLES = frozenset({"instructor", "admin"})
FACULTY_LOCKOUT_THRESHOLD = 5
FACULTY_LOCKOUT_WINDOW = timedelta(minutes=15)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def faculty_lockout_remaining(
    db: Session,
    user: User,
    now: datetime | None = None,
) -> timedelta | None:
    """Time left on the account's lock, or None when it may sign in."""

    if user.role not in FACULTY_ROLES:
        return None

    current_time = _as_utc(now or datetime.now(timezone.utc))
    window_start = current_time - FACULTY_LOCKOUT_WINDOW

    recent_failures = (
        db.query(AuditRecord.occurred_at)
        .filter(
            AuditRecord.action_type == "login_failed",
            AuditRecord.actor_user_id == user.user_id,
            AuditRecord.outcome == "failed",
            AuditRecord.occurred_at >= window_start,
        )
        .order_by(AuditRecord.occurred_at.desc())
        .limit(FACULTY_LOCKOUT_THRESHOLD)
        .all()
    )

    if len(recent_failures) < FACULTY_LOCKOUT_THRESHOLD:
        return None

    # Locked until the oldest of the last N failures leaves the window.
    unlocks_at = _as_utc(recent_failures[-1].occurred_at) + FACULTY_LOCKOUT_WINDOW
    remaining = unlocks_at - current_time

    return remaining if remaining > timedelta(0) else None


def lockout_message(remaining: timedelta) -> str:
    minutes = max(1, -(-int(remaining.total_seconds()) // 60))
    unit = "minute" if minutes == 1 else "minutes"
    return (
        "Too many failed sign-in attempts. For security, this faculty "
        f"account is locked for {minutes} more {unit}. Use \"Forgot "
        "password?\" if you no longer know the password."
    )
