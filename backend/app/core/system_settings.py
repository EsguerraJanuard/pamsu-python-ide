from typing import Any
from sqlalchemy.orm import Session
from app.core.ttl_cache import TTLCache
from app.models.domain_models import SystemSetting

DEFAULT_SYSTEM_SETTINGS = {
    "maintenance_mode": False,
    "default_ast_strictness": "moderate",
    "registration_enabled": False,
}

# Settings are read on every student request (maintenance mode) and on every
# sign-in, but change only when MIS saves them. The stored rows are kept in
# memory for a few seconds instead of being queried each time. Saving
# through set_system_setting() clears this process's copy at once; another
# process sees the change within SETTINGS_CACHE_TTL_SECONDS.
SETTINGS_CACHE_TTL_SECONDS = 15
_settings_cache = TTLCache(ttl_seconds=SETTINGS_CACHE_TTL_SECONDS, max_entries=1)
_STORED_SETTINGS_KEY = "stored"


def _parse_setting_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in ("true", "1"):
        return True
    if lowered in ("false", "0"):
        return False
    return value


def _load_stored_settings(db: Session) -> dict[str, Any]:
    return {setting.key: _parse_setting_value(setting.value) for setting in db.query(SystemSetting).all()}


def _cached_stored_settings(db: Session) -> dict[str, Any]:
    """Stored rows only (no defaults). Database errors propagate and are not cached."""
    return _settings_cache.get_or_load(_STORED_SETTINGS_KEY, lambda: _load_stored_settings(db))


def invalidate_system_settings_cache() -> None:
    """Forget this process's copy, so the next read queries the database."""
    _settings_cache.clear()


def get_system_setting(db: Session, key: str, default: Any = None) -> Any:
    """Retrieve a system setting from the database with fallback to default."""
    try:
        stored = _cached_stored_settings(db)
    except Exception:
        stored = {}
    if key in stored:
        return stored[key]
    return DEFAULT_SYSTEM_SETTINGS.get(key, default)


def set_system_setting(db: Session, key: str, value: Any, *, commit: bool = True) -> None:
    """Persist a system setting to the database.

    With commit=False the change is only flushed, so several settings (and
    their audit record) can be committed together by the caller. The caller
    then calls invalidate_system_settings_cache() again after its commit or
    rollback, so no other request keeps the value from before.
    """
    val_str = str(value).lower() if isinstance(value, bool) else str(value)
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        setting.value = val_str
    else:
        setting = SystemSetting(key=key, value=val_str)
        db.add(setting)
    if commit:
        db.commit()
    else:
        db.flush()
    invalidate_system_settings_cache()


def read_stored_system_settings(db: Session) -> dict[str, Any]:
    """Current values (stored or default), read from the database without
    the cache and without swallowing database errors."""
    values = dict(DEFAULT_SYSTEM_SETTINGS)
    values.update(_load_stored_settings(db))
    return values


def get_all_system_settings(db: Session) -> dict[str, Any]:
    """Retrieve all system settings as a dictionary."""
    res = dict(DEFAULT_SYSTEM_SETTINGS)
    try:
        res.update(_cached_stored_settings(db))
    except Exception:
        pass
    return res


AST_STRICTNESS_LEVELS = ("lax", "moderate", "strict")


def get_default_ast_strictness(db: Session) -> str:
    """
    The admin's default AST strictness.

    It is the starting level of new instructor accounts and the level used
    where no instructor applies (practice modules, or a task whose
    instructor no longer exists). Instructors keep the level they chose.
    """
    value = get_system_setting(db, "default_ast_strictness")
    return value if value in AST_STRICTNESS_LEVELS else DEFAULT_SYSTEM_SETTINGS["default_ast_strictness"]
