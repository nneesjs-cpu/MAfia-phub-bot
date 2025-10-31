import os

def _parse_int(value):
    try:
        return int(value) if value is not None and value != "" else None
    except Exception:
        return None

def _parse_sudo(value):
    if not value:
        return []
    # قابل للاستخدام: "12345" أو "123,456,789"
    parts = [p.strip() for p in value.split(",") if p.strip()]
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            pass
    return out

class Config:
    # environment variables (strings)
    API_ID = _parse_int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    # SUDO can be comma separated list
    SUDO = _parse_sudo(os.getenv("SUDO_ID") or os.getenv("SUDO"))
    # optional database URL
    SQL_DB = os.getenv("SQL_DB", "sqlite:///bot.db")

    @classmethod
    def is_sudo(cls, user_id: int) -> bool:
        return user_id in cls.SUDO