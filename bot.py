import logging
import os
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from dotenv import load_dotenv
from storage import Storage

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO
)
logger = logging.getLogger("health-bot")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

COMMANDS_TEXT = (
    "Commands:\n"
    "/log <meal> - Log a meal for today\n"
    "/day [YYYY-MM-DD] - Show meals for a day (default: today)\n"
    "/edit <id> <new meal text> - Edit a logged meal\n"
    "/delete <id> - Delete a logged meal\n"
    "/help - Show this help"
)


def today_str() -> str:
    return datetime.now().date().isoformat()


def extract_tail(message_text: str | None) -> str:
    if not message_text:
        return ""
    parts = message_text.split(" ", 1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


def parse_date_arg(arg: str | None) -> str | None:
    if not arg:
        return today_str()
    lowered = arg.strip().lower()
    if lowered in {"today", "tod"}:
        return today_str()
    if DATE_RE.match(arg):
        return arg
    return None


load_dotenv()

storage = Storage(os.getenv("DB_PATH", "data/health.db"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name or 'there'}! I can help log meals and track your day.\n\n"
        f"{COMMANDS_TEXT}"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(COMMANDS_TEXT)


async def log_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = extract_tail(update.message.text)
    if not text:
        await update.message.reply_text("Usage: /log <meal>")
        return

    log_date = today_str()
    meal = storage.add_meal(update.effective_user.id, text, log_date)
    await update.message.reply_text(
        f"Logged meal #{meal.id} for {log_date}: {meal.text}"
    )


async def day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg = context.args[0] if context.args else None
    log_date = parse_date_arg(arg)
    if log_date is None:
        await update.message.reply_text("Usage: /day [YYYY-MM-DD]")
        return

    meals = storage.list_meals_for_day(update.effective_user.id, log_date)
    if not meals:
        await update.message.reply_text(f"No meals logged for {log_date}.")
        return

    lines = [f"Meals for {log_date}:"]
    for meal in meals:
        lines.append(f"{meal.id}. {meal.text}")
    await update.message.reply_text("\n".join(lines))


async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /edit <id> <new meal text>")
        return

    try:
        meal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Meal id must be a number. Usage: /edit <id> <new meal text>")
        return

    new_text = " ".join(context.args[1:]).strip()
    if not new_text:
        await update.message.reply_text("Usage: /edit <id> <new meal text>")
        return

    ok = storage.update_meal(update.effective_user.id, meal_id, new_text)
    if not ok:
        await update.message.reply_text(f"Meal #{meal_id} not found.")
        return

    await update.message.reply_text(f"Updated meal #{meal_id}.")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /delete <id>")
        return

    try:
        meal_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Meal id must be a number. Usage: /delete <id>")
        return

    ok = storage.delete_meal(update.effective_user.id, meal_id)
    if not ok:
        await update.message.reply_text(f"Meal #{meal_id} not found.")
        return

    await update.message.reply_text(f"Deleted meal #{meal_id}.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error", exc_info=context.error)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("log", log_meal))
    app.add_handler(CommandHandler("day", day))
    app.add_handler(CommandHandler("meals", day))
    app.add_handler(CommandHandler("edit", edit))
    app.add_handler(CommandHandler("delete", delete))

    app.add_error_handler(error_handler)

    logger.info("Health bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
