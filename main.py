"""Telegram entry point for Google authorization and Google One links."""

import logging
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from oauth_server import (
    OAuthConfigurationError,
    create_authorization_url,
    oauth_configured,
    start_oauth_server,
)

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def _get_session(chat_id: int) -> dict:
    if chat_id not in config.SESSION_STORE:
        config.SESSION_STORE[chat_id] = {}
    return config.SESSION_STORE[chat_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Google One Bot*\n\n"
        "Авторизация выполняется на официальной странице Google — "
        "пароль не передаётся боту и не хранится в Replit.\n\n"
        "Команды:\n"
        "• /login — войти через Google\n"
        "• /check\\_offer — открыть страницы Google One после авторизации\n"
        "• /get\\_link или /link — получить ссылки Google One\n"
        "• /status — статус авторизации\n"
        "• /logout — очистить текущую сессию",
        parse_mode="Markdown",
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if not oauth_configured():
        await update.message.reply_text(
            "⚠️ Google OAuth ещё не настроен в Replit.\n\n"
            "Добавьте Secrets: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET и "
            "GOOGLE_REDIRECT_URI, затем перезапустите бота."
        )
        return

    try:
        auth_url = create_authorization_url(chat_id)
    except OAuthConfigurationError as exc:
        await update.message.reply_text(f"❌ Ошибка OAuth: {exc}")
        return
    except Exception:
        logger.exception("Failed to create OAuth URL for chat %s", chat_id)
        await update.message.reply_text(
            "❌ Не удалось создать ссылку входа Google. Проверьте OAuth-настройки."
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔐 Войти через Google", url=auth_url)]]
    )
    await update.message.reply_text(
        "Нажмите кнопку ниже. Откроется официальный сайт Google.\n\n"
        "После успешного входа вернитесь в Telegram.",
        reply_markup=keyboard,
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = _get_session(update.effective_chat.id)

    if session.get("oauth_authenticated"):
        email = session.get("email") or "Google account"
        await update.message.reply_text(
            f"✅ Google подключён.\nАккаунт: {email}"
        )
    else:
        await update.message.reply_text(
            "ℹ️ Google ещё не подключён. Используйте /login."
        )


def _google_one_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Google One", url=config.GOOGLE_ONE_URL)],
            [
                InlineKeyboardButton(
                    "Тарифы Google One", url=config.GOOGLE_ONE_OFFERS_URL
                )
            ],
        ]
    )


async def check_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = _get_session(update.effective_chat.id)

    if not session.get("oauth_authenticated"):
        await update.message.reply_text(
            "⚠️ Сначала авторизуйтесь через /login."
        )
        return

    await update.message.reply_text(
        "✅ Авторизация Google подтверждена.\n\n"
        "Откройте Google One кнопкой ниже. Google не предоставляет обычному "
        "OAuth-приложению доступ к вашей браузерной сессии Google One, поэтому "
        "персональное предложение проверяется на официальной странице Google.",
        reply_markup=_google_one_keyboard(),
    )


async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = _get_session(update.effective_chat.id)

    if not session.get("oauth_authenticated"):
        await update.message.reply_text(
            "⚠️ Сначала авторизуйтесь через /login."
        )
        return

    await update.message.reply_text(
        "🔗 Официальные страницы Google One:",
        reply_markup=_google_one_keyboard(),
    )


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    config.SESSION_STORE.pop(chat_id, None)
    await update.message.reply_text(
        "✅ Локальная сессия бота очищена. Для нового входа используйте /login."
    )


def main() -> None:
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. Add it to Replit Secrets and restart."
        )
        sys.exit(1)

    start_oauth_server()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("check_offer", check_offer))
    app.add_handler(CommandHandler("get_link", get_link))
    app.add_handler(CommandHandler("link", get_link))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("logout", logout))

    logger.info("Bot is running. Press Ctrl-C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
