# ============================================================
# TELEGRAM CONFIG
# ============================================================
TELEGRAM_API_ID = "33363553"
TELEGRAM_API_HASH = "bc4d206245f0b3bfb2ccbfc6c0d70c23"
TELEGRAM_PHONE = "+919343149455"
NOTIFY_TELEGRAM_USERNAME = "@adarshjoshi93"

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
        "dynamic_url": True
    },
    "55": {
        "url": "https://uoefkt55.com/#/",
        "gift_path": "/#/gift",
        "account_path": "/#/mine",
        "dynamic_url": False
    },
    "999": {
        "url": "https://in999ff.com/#/",
        "gift_path": "/#/gift",
        "account_path": "/#/mine",
        "dynamic_url": False
    },
}

# ============================================================
# PROFILES - Phone aur Password
# Teeno sites ka same number aur password hai
# ============================================================
PHONE = "9343149455"    # Bina +91 ke
PASSWORD = "Adarsh93"   # Password

PROFILES = [
    {
        "profile_id": "profile_1",
        "91":  {"phone": PHONE, "password": PASSWORD},
        "55":  {"phone": PHONE, "password": PASSWORD},
        "999": {"phone": PHONE, "password": PASSWORD},
    },
    # Aur accounts add karne ho toh yahan copy karo:
    # {
    #     "profile_id": "profile_2",
    #     "91":  {"phone": "PHONE2", "password": "PASS2"},
    #     "55":  {"phone": "PHONE2", "password": "PASS2"},
    #     "999": {"phone": "PHONE2", "password": "PASS2"},
    # },
]

# ============================================================
# BOT SETTINGS
# ============================================================
LOGIN_CHECK_INTERVAL = 30   # Har 30 sec login check
RETRY_ATTEMPTS = 3          # 3 baar try karo
MIN_DELAY = 0.1             # Min delay (seconds)
MAX_DELAY = 0.3             # Max delay (seconds)
