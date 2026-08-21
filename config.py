"""
File-To-Link-BOT configuration.

Every setting can be set as an environment variable (recommended) OR edited
directly below.
"""
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ── small env helpers ────────────────────────────────────────────────────────

def env(name, default=""):
    return os.environ.get(name, "").strip() or default


def env_int(name, default=0):
    try:
        return int(env(name, default))
    except (TypeError, ValueError):
        return default


def env_bool(name, default=False):
    v = os.environ.get(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"} if v else default


def env_ids(name, default=None):
    v = os.environ.get(name, "").strip()
    if not v:
        return default or []
    return [int(x) for x in re.split(r"[\s,]+", v) if x.strip().lstrip("-").isdigit()]


# ── required ──────────────────────────────────────────────────────────────────

API_ID    = env_int("API_ID")                  # https://my.telegram.org
API_HASH  = env("API_HASH")                     # https://my.telegram.org
BOT_TOKEN = env("BOT_TOKEN")                    # @BotFather

DB_URL  = env("DATABASE_URI") or env("DB_URL")  # mongodb+srv://...
DB_NAME = env("DATABASE_NAME", "filetolink")

BIN_CHANNEL = env_int("BIN_CHANNEL")            # private channel where files are stored (-100...)

# ── optional ──────────────────────────────────────────────────────────────────

SESSION        = env("SESSION", "appbot")
ADMINS         = env_ids("ADMINS")              # e.g. 123456789,987654321

LOG_CHANNEL   = env_int("LOG_CHANNEL")          # 0 = off
AUTH_CHANNEL  = env_ids("AUTH_CHANNEL")         # force-sub channel IDs

SUPPORT        = env("SUPPORT", "https://t.me/LastPerson07")
UPDATE_CHANNEL = env("UPDATE_CHANNEL")
CHANNEL        = UPDATE_CHANNEL or SUPPORT

FSUB              = env_bool("FSUB")            # force subscribe to AUTH_CHANNEL
ENABLE_LIMIT      = env_bool("ENABLE_LIMIT", True)
MAINTENANCE_MODE  = env_bool("MAINTENANCE_MODE")

PORT     = env_int("PORT", 2626)
ON_HEROKU = bool(os.environ.get("DYNO"))

_fqdn = env("FQDN") or env("HOST") or "localhost"
_protocol = env("PROTOCOL") or ("https" if ON_HEROKU else "http")
_no_port = env_bool("NO_PORT")
_url_override = env("URL")
if _url_override and "://" not in _url_override:
    _url_override = "https://" + _url_override

if _url_override:
    URL = _url_override if _url_override.endswith("/") else _url_override + "/"
else:
    URL = f"{_protocol}://{_fqdn}{'' if _no_port else f':{PORT}'}/"

RATE_LIMIT_TIMEOUT = env_int("RATE_LIMIT_TIMEOUT", 600)
MAX_FILES          = env_int("MAX_FILES", 5)
BATCH_LIMIT        = env_int("BATCH_LIMIT", 60)
SLEEP_THRESHOLD    = env_int("SLEEP_THRESHOLD", 60)
PING_INTERVAL      = env_int("PING_INTERVAL", 1200)

AUTH_PICS    = env("AUTH_PICS", "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg")
PICS         = env("PICS", "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg")
FILE_PIC     = env("FILE_PIC", "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg")
FILE_CAPTION = env("FILE_CAPTION", "🎬 <i><a href='{}'>{}</a></i>")

# Extra bot tokens for multi-client streaming (spreads load across sessions).
# Set as a comma-separated MULTI_BOT_TOKENS env var, or a file via BOT_TOKENS_FILE.
_extra = [t.strip() for t in env("MULTI_BOT_TOKENS").split(",") if t.strip()]
_tokens_file = env("BOT_TOKENS_FILE")
if _tokens_file and Path(_tokens_file).is_file():
    _extra += [
        line.split("#")[0].strip()
        for line in Path(_tokens_file).read_text().splitlines()
        if line.split("#")[0].strip()
    ]
_seen = {BOT_TOKEN}
_multi_tokens = [t for t in _extra if t not in _seen and not _seen.add(t)]
ALL_BOT_TOKENS = [BOT_TOKEN] + _multi_tokens
MULTI_CLIENT = bool(_multi_tokens)


# ── validation ────────────────────────────────────────────────────────────────

def _check():
    missing = []
    if not API_ID:
        missing.append("API_ID (https://my.telegram.org)")
    if not API_HASH:
        missing.append("API_HASH (https://my.telegram.org)")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN (@BotFather)")
    if not DB_URL:
        missing.append("DATABASE_URI (https://www.mongodb.com/atlas)")
    if not BIN_CHANNEL:
        missing.append("BIN_CHANNEL (private channel id, bot must be admin)")

    if missing:
        print("\n❌ Missing required config:")
        for m in missing:
            print(f"   • {m}")
        print("Set these as environment variables (or edit config.py).\n")
        if env("CONFIG_STRICT", "1") not in {"0", "false", "no", "off"}:
            sys.exit(1)
        return

    print("✅ config.py — all required fields are set.")
    if not LOG_CHANNEL:
        print("⚠️  LOG_CHANNEL not set — new-user logs will be skipped.")
    if not ADMINS:
        print("⚠️  ADMINS is empty — admin commands won't be usable.")
    if FSUB and not AUTH_CHANNEL:
        print("⚠️  FSUB is on but AUTH_CHANNEL is empty.")
    if not _url_override and _fqdn == "localhost":
        print("⚠️  URL/FQDN not set — links will point at localhost.")


if __name__ == "__main__" or "main.py" in (sys.argv[0] or ""):
    _check()
