"""Configuration and constants for the Telegram Google One helper."""

import os

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Google OAuth
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

_replit_domain = os.environ.get("REPLIT_DEV_DOMAIN", "").strip()
_default_redirect = (
    f"https://{_replit_domain}/oauth/callback" if _replit_domain else ""
)
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", _default_redirect
).strip()

GOOGLE_OAUTH_SCOPES = [
    "openid",
    "email",
    "profile",
]

OAUTH_PORT = int(os.environ.get("PORT", "8080"))

# Google URLs
GMAIL_LOGIN_URL = "https://accounts.google.com/signin/v2/identifier"
GOOGLE_ONE_URL = "https://one.google.com/"
GOOGLE_ONE_OFFERS_URL = "https://one.google.com/about/plans"

# Legacy browser diagnostics/device profile settings.
DEVICE_MODEL = "Pixel 10 Pro"
DEVICE_BRAND = "google"
DEVICE_MANUFACTURER = "Google"
ANDROID_VERSION = "16"
ANDROID_SDK = "36"
BUILD_ID = "AP4A.250405.002"
CHROME_VERSION = "124.0.6367.82"
CHROME_MAJOR_VERSION = 124

USER_AGENT_TEMPLATES = [
    (
        "Mozilla/5.0 (Linux; Android {android}; {model} Build/{build}; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Version/4.0 Chrome/{chrome} Mobile Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Linux; Android {android}; {model} Build/{build}) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{chrome} Mobile Safari/537.36"
    ),
]

GEMINI_OFFER_KEYWORDS = [
    "gemini pro",
    "gemini advanced",
    "12 month",
    "12-month",
    "free trial",
    "activate",
    "get started",
    "claim offer",
    "redeem",
]

WEBDRIVER_TIMEOUT = 30
IMPLICIT_WAIT = 10
PAGE_LOAD_TIMEOUT = 60
HEADLESS = True

# In-memory Telegram sessions. Passwords are not collected or stored.
SESSION_STORE: dict = {}

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
