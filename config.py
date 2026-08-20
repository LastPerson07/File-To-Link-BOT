import os
import re
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

log = logging.getLogger("config")

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


API_ID      = 0                        # https://my.telegram.org
API_HASH    = ""                       # https://my.telegram.org
BOT_TOKEN   = ""                       # @BotFather

DATABASE_URI  = ""                     # mongodb+srv://...  (mongodb.com/atlas)
DATABASE_NAME = "filetolink"

SESSION        = "appbot"
OWNER_USERNAME = "LastPerson07"

ADMINS = []                            # e.g. [123456789, 987654321]

BIN_CHANNEL   = 0                       # required: file-store channel (-100...)
LOG_CHANNEL   = 0                       # log channel         (-100..., 0 = off)
AUTH_CHANNELS = []                     # force-sub channel IDs

SUPPORT_LINK   = "https://t.me/LastPerson07"
UPDATE_CHANNEL = ""                     # e.g. "https://t.me/YourChannel"
URL            = ""                     # universal server URL — stream/download links

FSUB             = False                # force subscribe to AUTH_CHANNELS
ENABLE_LIMIT     = True                 # rate-limit files per user
MAINTENANCE_MODE = False                # block all users except admins

PORT     = 2626
NO_PORT  = False                        # True = hide port from URL
FQDN     = ""                           # your domain, e.g. "mybot.koyeb.app"
PROTOCOL = ""                           # "http" or "https"  (auto if empty)

RATE_LIMIT_TIMEOUT = 600
MAX_FILES          = 5
BATCH_LIMIT        = 60
SLEEP_THRESHOLD    = 60
PING_INTERVAL      = 1200

AUTH_PICS    = "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg"
PICS         = "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg"
FILE_PIC     = "https://i.postimg.cc/1Xw1wxDw/photo-2025-10-19-07-30-34.jpg"
FILE_CAPTION = """🎬 <i><a href='{}'>{}</a></i>"""   # (channel_link, file_name)

EXTRA_BOT_TOKENS = [
    # "123456:AABBccDDeeFF-your-token-here",
    # "789012:GGHHiiJJkkLL-another-token",
]




def _env(name, fallback):
    v = os.environ.get(name, "")
    v = v.strip() if v else ""
    return v if v else fallback


def _env_int(name, fallback):
    v = _env(name, None)
    if v is None:
        return fallback
    try:
        return int(v)
    except (TypeError, ValueError):
        return fallback


def _env_bool(name, fallback):
    v = os.environ.get(name, "")
    v = v.strip() if v else ""
    if not v:
        return fallback
    return v.lower() in {"1", "true", "yes", "on"}


def _env_ids(name, fallback):
    v = os.environ.get(name, "")
    v = v.strip() if v else ""
    if not v:
        return fallback
    return [int(x) for x in re.split(r"[\s,]+", v) if x.strip().lstrip("-").isdigit()]


def _collect_env_tokens(main):
    out = []
    v = os.environ.get("MULTI_BOT_TOKENS", "").strip()
    if v:
        out += [t.strip() for t in v.split(",") if t.strip()]
    fp = os.environ.get("BOT_TOKENS_FILE", "").strip()
    if fp and Path(fp).is_file():
        out += [l.split("#")[0].strip() for l in Path(fp).read_text().splitlines()
                if l.split("#")[0].strip()]
    for k, val in sorted(os.environ.items()):
        if k.startswith("MULTI_TOKEN") and val.strip():
            out.append(val.strip())
    seen = {main}
    return [t for t in out if t not in seen and not seen.add(t)]


@dataclass(frozen=True)
class AppConfig:
    api_id:     int = 0
    api_hash:   str = ""
    bot_token:  str = ""

    db_url:    str = ""
    db_name:   str = "filetolink"

    session:         str       = "appbot"
    owner_username:  str       = "LastPerson07"
    admins:          List[int] = field(default_factory=list)

    bin_channel:    int            = 0
    log_channel:    int            = 0
    auth_channels:  List[int]      = field(default_factory=list)

    support_link:    str           = "https://t.me/LastPerson07"
    update_channel:  Optional[str] = None
    url_override:    Optional[str] = None

    fsub:              bool = False
    enable_limit:      bool = True
    maintenance_mode:  bool = False

    port:      int  = 2626
    no_port:   bool = False
    fqdn:      str  = "localhost"
    protocol:  str  = "http"

    rate_limit_timeout:  int = 600
    max_files_per_user:  int = 5
    batch_limit:         int = 60
    sleep_threshold:     int = 60
    ping_interval:       int = 1200

    auth_pics:     str = ""
    pics:          str = ""
    file_pic:      str = ""
    file_caption:  str = ""

    on_heroku:  bool           = False

    multi_tokens:  List[str] = field(default_factory=list)
    multi_client:  bool      = False

    problems: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def all_bot_tokens(self) -> List[str]:
        return [self.bot_token] + self.multi_tokens

    @property
    def url(self) -> str:
        if self.url_override:
            u = self.url_override
            return u if u.endswith("/") else u + "/"
        port_seg = "" if self.no_port else f":{self.port}"
        return f"{self.protocol}://{self.fqdn}{port_seg}/"

    @property
    def has_ssl(self) -> bool:
        return self.protocol == "https"

    @property
    def channel_link(self) -> str:
        return self.update_channel or self.support_link

    @property
    def has_critical_errors(self) -> bool:
        return any(level == "error" for level, _ in self.problems)


def _ensure_scheme(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if "://" not in url:
        return "https://" + url
    return url


def _build() -> AppConfig:
    on_heroku = bool(os.environ.get("DYNO"))
    token     = _env("BOT_TOKEN", BOT_TOKEN)
    fqdn_val  = _env("FQDN", "") or _env("HOST", "") or FQDN or "localhost"
    proto     = _env("PROTOCOL", PROTOCOL) or ("https" if on_heroku else "http")
    url_val   = _ensure_scheme(_env("URL", URL)) or None

    all_extras = list(EXTRA_BOT_TOKENS)
    all_extras += _collect_env_tokens(token)
    seen = {token}
    merged = []
    for t in all_extras:
        t = t.strip()
        if t and t not in seen:
            merged.append(t)
            seen.add(t)

    c = AppConfig(
        api_id     = _env_int("API_ID", API_ID),
        api_hash   = _env("API_HASH", API_HASH),
        bot_token  = token,

        db_url   = _env("DATABASE_URI", "") or _env("DB_URL", DATABASE_URI),
        db_name  = _env("DATABASE_NAME", "") or _env("DB_NAME", DATABASE_NAME),

        session        = _env("SESSION", SESSION),
        owner_username = _env("OWNER_USERNAME", OWNER_USERNAME),
        admins         = _env_ids("ADMINS", ADMINS),

        bin_channel    = _env_int("BIN_CHANNEL", BIN_CHANNEL),
        log_channel    = _env_int("LOG_CHANNEL", LOG_CHANNEL),
        auth_channels  = _env_ids("AUTH_CHANNEL", AUTH_CHANNELS),

        support_link   = _env("SUPPORT", SUPPORT_LINK),
        update_channel = _env("UPDATE_CHANNEL", UPDATE_CHANNEL) or None,
        url_override   = url_val,

        fsub             = _env_bool("FSUB", FSUB),
        enable_limit     = _env_bool("ENABLE_LIMIT", ENABLE_LIMIT),
        maintenance_mode = _env_bool("MAINTENANCE_MODE", MAINTENANCE_MODE),

        port     = _env_int("PORT", PORT),
        no_port  = _env_bool("NO_PORT", NO_PORT),
        fqdn     = fqdn_val,
        protocol = proto,

        rate_limit_timeout = _env_int("RATE_LIMIT_TIMEOUT", RATE_LIMIT_TIMEOUT),
        max_files_per_user = _env_int("MAX_FILES", MAX_FILES),
        batch_limit        = _env_int("BATCH_LIMIT", BATCH_LIMIT),
        sleep_threshold    = _env_int("SLEEP_THRESHOLD", SLEEP_THRESHOLD),
        ping_interval      = _env_int("PING_INTERVAL", PING_INTERVAL),

        auth_pics    = _env("AUTH_PICS", AUTH_PICS),
        pics         = _env("PICS", PICS),
        file_pic     = _env("FILE_PIC", FILE_PIC),
        file_caption = _env("FILE_CAPTION", FILE_CAPTION),

        on_heroku = on_heroku,

        multi_tokens = merged,
        multi_client = len(merged) > 0,
    )
    return c


def _validate(c: AppConfig) -> List[Tuple[str, str]]:
    problems: List[Tuple[str, str]] = []

    if not c.api_id:
        problems.append(("error", "API_ID is missing. Get it from https://my.telegram.org"))
    if not c.api_hash:
        problems.append(("error", "API_HASH is missing. Get it from https://my.telegram.org"))
    if not c.bot_token:
        problems.append(("error", "BOT_TOKEN is missing. Get it from @BotFather"))
    if not c.db_url:
        problems.append(("error",
            "DATABASE_URI is missing. Create a free cluster at "
            "https://www.mongodb.com/atlas and paste its connection string."))
    if not c.bin_channel:
        problems.append(("error",
            "BIN_CHANNEL is missing. Create a private channel, add the bot as "
            "admin, and put its -100... id here (where files are stored)."))

    if not c.log_channel:
        problems.append(("warn", "LOG_CHANNEL is not set — new-user logs will be skipped."))
    if not c.admins:
        problems.append(("warn",
            "ADMINS is empty — admin commands (/ban, /broadcast, /stats, …) "
            "won't be usable. Add your Telegram user ID."))
    if c.fsub and not c.auth_channels:
        problems.append(("warn",
            "FSUB is on but AUTH_CHANNELS is empty — set channel IDs or turn FSUB off."))
    if not c.url_override and c.fqdn == "localhost":
        problems.append(("warn",
            "URL/FQDN not set — links will point at localhost. "
            "Set URL or FQDN (or let your host set them)."))

    return problems


def _print_report(c: AppConfig) -> None:
    if not c.problems:
        print("✅ config.py — all required fields are set. Ready to go!")
        return

    errors = [m for lvl, m in c.problems if lvl == "error"]
    warns  = [m for lvl, m in c.problems if lvl == "warn"]

    print("\n" + "═" * 60)
    print(" FILE-TO-LINK-BOT — configuration check")
    print("═" * 60)
    if errors:
        print(f"❌ {len(errors)} required field(s) missing — the bot will NOT start:")
        for m in errors:
            print(f"   • {m}")
    if warns:
        print(f"\n⚠️  {len(warns)} optional note(s):")
        for m in warns:
            print(f"   • {m}")
    print("\n  Tip: any of these can also be set as environment variables.")
    print("═" * 60 + "\n")


cfg = _build()
cfg = AppConfig(**{**cfg.__dict__, "problems": _validate(cfg)})

_runs_as_bot = __name__ == "__main__" or "main.py" in (sys.argv[0] or "")

if _runs_as_bot:
    _print_report(cfg)

if cfg.has_critical_errors and os.environ.get("CONFIG_STRICT", "1") not in {"0", "false", "no", "off"}:
    if _runs_as_bot:
        sys.exit(1)

config = cfg