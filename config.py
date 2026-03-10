# ============================================================
# TELEGRAM CONFIG
# ============================================================
TELEGRAM_API_ID = "33363553"
TELEGRAM_API_HASH = "bc4d206245f0b3bfb2ccbfc6c0d70c23"
TELEGRAM_PHONE = "+919343149455"
NOTIFY_TELEGRAM_USERNAME = "@adarshjoshi93"

# ============================================================
# OPENROUTER API - Claude Access
# ============================================================
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "anthropic/claude-3-haiku"  # Free + Fast

# ============================================================
# TELEGRAM GROUPS
# ============================================================
TELEGRAM_GROUPS = [
    "https://t.me/osmlooters",
    "https://t.me/+kUjM8wtMwBUzNTFl",
]

# ============================================================
# WEBSITES
# ============================================================
WEBSITES = {
    "91": {
        "url": "https://agra91.com/#/",
        "gift_path": "/#/gift",
        "account_path": "/#/mine",
    },
    "55": {
        "url": "https://uoefkt55.com/#/",
        "gift_path": "/#/gift",
        "account_path": "/#/mine",
    },
    "999": {
        "url": "https://in999ff.com/#/",
        "gift_path": "/#/gift",
        "account_path": "/#/mine",
    },
}

# ============================================================
# PROFILES
# ============================================================
PHONE = "9343149455"
PASSWORD = "Adarsh93"

PROFILES = [
    {
        "profile_id": "profile_1",
        "91":  {"phone": PHONE, "password": PASSWORD},
        "55":  {"phone": PHONE, "password": PASSWORD},
        "999": {"phone": PHONE, "password": PASSWORD},
    },
]

# ============================================================
# BOT SETTINGS
# ============================================================
LOGIN_CHECK_INTERVAL = 30
RETRY_ATTEMPTS = 3
MIN_DELAY = 0.1
MAX_DELAY = 0.3
