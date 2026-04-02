# Health Chatbot (Telegram)

A lightweight Telegram bot for logging meals, tracking your day, and editing or deleting entries. Data is stored in a local SQLite database for reliability and simplicity.

## Features

- Log meals
- Track meals for a specific day
- Edit logged meals
- Delete logged meals

## Requirements

- Python 3.10+
- Telegram bot token from **@BotFather**

## Setup

1. Create a Telegram bot via **@BotFather** and copy the token.
2. Create and activate a virtual environment (recommended).
3. Install dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `venv` is missing on Ubuntu/Debian:

```bash
sudo apt install python3.10-venv
```

4. Create a `.env` file and set your bot token:

```bash
cp .env.example .env
```

Edit `.env` and set:

```
BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
```

5. Run the bot:

```bash
python bot.py
```

## Commands

- `/log <meal>` - Log a meal for today
- `/day [YYYY-MM-DD]` - Show meals for a day (default: today)
- `/edit <id> <new meal text>` - Edit a logged meal
- `/delete <id>` - Delete a logged meal
- `/help` - Show help

## Data Storage

- SQLite DB file is stored at `data/health.db` by default.
- You can override the path with the `DB_PATH` environment variable.
- The bot uses the server's local date for "today".

## Project Structure

- `bot.py` - Telegram bot commands and handlers
- `storage.py` - SQLite storage layer
- `requirements.txt` - Python dependencies
- `data/` - Local SQLite database (created automatically)
- `.env` - Your local environment variables (not committed)

## Troubleshooting

- `Invalid bot selected` in BotFather. Make sure you are signed in to the same Telegram account that created the bot. Use `/mybots` in BotFather to find your bot.
- `telegram.error.TimedOut`. Usually a temporary network hiccup. The bot can keep running. If it happens frequently, increase timeouts.

## Security Notes

- Never share your bot token publicly.
- If a token is exposed, revoke it immediately in BotFather and use the new one.
