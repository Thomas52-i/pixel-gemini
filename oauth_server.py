"""Small Google OAuth callback server used by the Telegram bot."""

import logging
import secrets
import threading
import time
from html import escape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import Flow

import config

logger = logging.getLogger(__name__)
app = Flask(__name__)

_STATE_TTL_SECONDS = 15 * 60
_states: dict[str, dict] = {}
_states_lock = threading.Lock()
_server_started = False
_server_lock = threading.Lock()


class OAuthConfigurationError(RuntimeError):
    pass


def oauth_configured() -> bool:
    return bool(
        config.GOOGLE_CLIENT_ID
        and config.GOOGLE_CLIENT_SECRET
        and config.GOOGLE_REDIRECT_URI
    )


def _client_config() -> dict:
    if not oauth_configured():
        raise OAuthConfigurationError(
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI "
            "must be configured."
        )
    return {
        "web": {
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [config.GOOGLE_REDIRECT_URI],
        }
    }


def _new_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        _client_config(),
        scopes=config.GOOGLE_OAUTH_SCOPES,
        state=state,
    )
    flow.redirect_uri = config.GOOGLE_REDIRECT_URI
    return flow


def _cleanup_states(now: float) -> None:
    expired = [
        state
        for state, item in _states.items()
        if item["expires_at"] <= now
    ]
    for state in expired:
        _states.pop(state, None)


def create_authorization_url(chat_id: int) -> str:
    now = time.time()
    state = secrets.token_urlsafe(32)

    with _states_lock:
        _cleanup_states(now)
        stale_for_chat = [
            key for key, item in _states.items() if item["chat_id"] == chat_id
        ]
        for key in stale_for_chat:
            _states.pop(key, None)

        _states[state] = {
            "chat_id": chat_id,
            "expires_at": now + _STATE_TTL_SECONDS,
        }

    flow = _new_flow(state=state)
    authorization_url, returned_state = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
        prompt="select_account",
    )

    if returned_state != state:
        with _states_lock:
            _states.pop(state, None)
        raise OAuthConfigurationError("Google OAuth state mismatch.")

    return authorization_url


def _pop_state(state: str) -> int | None:
    now = time.time()
    with _states_lock:
        _cleanup_states(now)
        item = _states.pop(state, None)

    if not item or item["expires_at"] <= now:
        return None
    return int(item["chat_id"])


def _notify_telegram(chat_id: int, text: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        return

    payload = urlencode(
        {
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    req = Request(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urlopen(req, timeout=10) as response:
            response.read(1)
    except Exception:
        logger.exception("Could not send Telegram OAuth completion message")


@app.get("/")
def health():
    return "Google OAuth callback service is running.", 200


@app.get("/oauth/callback")
def oauth_callback():
    error = request.args.get("error")
    state = request.args.get("state", "")
    code = request.args.get("code", "")

    chat_id = _pop_state(state)
    if chat_id is None:
        return (
            "<h2>Ссылка входа устарела или недействительна.</h2>"
            "<p>Вернитесь в Telegram и снова выполните /login.</p>",
            400,
        )

    if error:
        _notify_telegram(
            chat_id,
            f"❌ Вход Google не завершён: {error}. Используйте /login для новой попытки.",
        )
        return (
            "<h2>Авторизация отменена.</h2>"
            "<p>Можно закрыть эту страницу и вернуться в Telegram.</p>",
            400,
        )

    if not code:
        _notify_telegram(chat_id, "❌ Google не вернул код авторизации.")
        return "<h2>Не получен код авторизации Google.</h2>", 400

    try:
        flow = _new_flow(state=state)
        flow.fetch_token(code=code)

        authorized = AuthorizedSession(flow.credentials)
        response = authorized.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            timeout=15,
        )
        response.raise_for_status()
        user_info = response.json()

        email = user_info.get("email") or ""
        subject = user_info.get("sub") or ""

        session = config.SESSION_STORE.setdefault(chat_id, {})
        session.clear()
        session.update(
            {
                "oauth_authenticated": True,
                "email": email,
                "google_sub": subject,
                "authorized_at": time.time(),
            }
        )

        account_text = email or "Google account"
        _notify_telegram(
            chat_id,
            f"✅ Google успешно подключён: {account_text}\n"
            "Теперь можно использовать /status, /check_offer или /link.",
        )
        return (
            "<h2>Google успешно подключён.</h2>"
            f"<p>Аккаунт: {escape(account_text)}</p>"
            "<p>Можно закрыть эту страницу и вернуться в Telegram.</p>",
            200,
        )
    except Exception as exc:
        logger.exception("Google OAuth callback failed")
        _notify_telegram(
            chat_id,
            "❌ Не удалось завершить авторизацию Google. "
            "Проверьте OAuth-настройки и повторите /login.",
        )
        return (
            "<h2>Не удалось завершить авторизацию.</h2>"
            f"<p>{escape(type(exc).__name__)}</p>"
            "<p>Вернитесь в Telegram и повторите /login.</p>",
            500,
        )


def start_oauth_server() -> None:
    global _server_started

    with _server_lock:
        if _server_started:
            return
        _server_started = True

    def run() -> None:
        logger.info("Starting OAuth callback server on port %s", config.OAUTH_PORT)
        app.run(
            host="0.0.0.0",
            port=config.OAUTH_PORT,
            debug=False,
            use_reloader=False,
            threaded=True,
        )

    thread = threading.Thread(target=run, name="oauth-callback", daemon=True)
    thread.start()
