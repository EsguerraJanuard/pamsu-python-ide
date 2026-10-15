from typing import Any
from sqlalchemy.orm import Session
from app.models.domain_models import SystemSetting

DEFAULT_SYSTEM_SETTINGS = {
    "maintenance_mode": False,
    "default_ast_strictness": "moderate",
    "registration_enabled": False,
}


def get_system_setting(db: Session, key: str, default: Any = None) -> Any:
    """Retrieve a system setting from the database with fallback to default."""
    try:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting is not None:
            val = setting.value
            if val.lower() in ("true", "1"):
                return True
            if val.lower() in ("false", "0"):
                return False
            return val
    except Exception:
        pass
    return DEFAULT_SYSTEM_SETTINGS.get(key, default)


def set_system_setting(db: Session, key: str, value: Any) -> None:
    """Persist a system setting to the database."""
    val_str = str(value).lower() if isinstance(value, bool) else str(value)
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        setting.value = val_str
    else:
        setting = SystemSetting(key=key, value=val_str)
        db.add(setting)
    db.commit()


def get_all_system_settings(db: Session) -> dict[str, Any]:
    """Retrieve all system settings as a dictionary."""
    res = dict(DEFAULT_SYSTEM_SETTINGS)
    try:
        settings = db.query(SystemSetting).all()
        for s in settings:
            val = s.value
            if val.lower() in ("true", "1"):
                res[s.key] = True
            elif val.lower() in ("false", "0"):
                res[s.key] = False
            else:
                res[s.key] = val
    except Exception:
        pass
    return res
