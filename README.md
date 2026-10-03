# pixel-gemini

Telegram bot with official Google OAuth sign-in and Google One navigation.

## What changed

The bot no longer asks for or stores a Google password. `/login` sends an official Google authorization button. After Google confirms the account, the bot marks that Telegram session as connected and provides Google One links.

## Commands

- `/start` — help
- `/login` — sign in with Google OAuth
- `/status` — show Google connection status
- `/check_offer` — open Google One after authorization
- `/get_link` or `/link` — show Google One links
- `/logout` — clear the bot's local session

## Replit setup

Add these Secrets:

- `TELEGRAM_BOT_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

For Replit, `GOOGLE_REDIRECT_URI` must be your public HTTPS Replit URL followed by:

```text
/oauth/callback
```

Example:

```text
https://YOUR-REPLIT-DOMAIN/oauth/callback
```

Use exactly the same URI in the Google Cloud OAuth client under **Authorized redirect URIs**.

Install and run:

```bash
pip install -r requirements.txt
python main.py
```

The bot also starts a small Flask callback server on `PORT` (default `8080`).

## Google Cloud OAuth client

Create an OAuth 2.0 Client ID of type **Web application** in Google Cloud Console. Configure the OAuth consent screen and add the exact Replit callback URL as an authorized redirect URI.

The bot requests only the OpenID Connect identity scopes:

- `openid`
- `email`
- `profile`

These scopes identify the signed-in account. They do not provide a browser session for Google One and do not expose the user's Google password.

## Diagnostics

`diagnostics.py` can still be used to verify Chromium/ChromeDriver and the public Google sign-in page:

```bash
python diagnostics.py
```

This diagnostic does not submit account credentials.
