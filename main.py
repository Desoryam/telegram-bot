import os
import asyncio
import logging
from datetime import time

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import db


# -------------------------
# Load Environment Variables
# -------------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_URL = os.getenv("CHANNEL_URL")

BROADCAST_HOUR = int(os.getenv("BROADCAST_HOUR", 21))
BROADCAST_MINUTE = int(os.getenv("BROADCAST_MINUTE", 0))


# -------------------------
# Logging
# -------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# -------------------------
# Join Channel Button
# -------------------------

def channel_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="📢 Join for exclusive content",
                url=CHANNEL_URL
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# -------------------------
# Helper
# -------------------------

def is_admin(user_id: int):
    return user_id == ADMIN_ID


async def admin_only(update: Update):
    await update.message.reply_text(
        "❌ You are not authorized."
    )


# -------------------------
# User Commands
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    db.add_user(chat_id)

    text = db.get_setting("start_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_keyboard(),
        disable_web_page_preview=False,
    )


async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = db.get_setting("next_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_keyboard(),
        disable_web_page_preview=False,
    )


async def more_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = db.get_setting("more_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_keyboard(),
        disable_web_page_preview=False,
    )


# -------------------------
# Admin Commands
# -------------------------

async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await admin_only(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setstart"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
            "The replied message has no text."
        )

    db.set_setting("start_message", text)

    await update.message.reply_text(
        "✅ Start message updated."
    )


async def set_next(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await admin_only(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setnext"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
            "The replied message has no text."
        )

    db.set_setting("next_message", text)

    await update.message.reply_text(
        "✅ Next message updated."
    )

# -------------------------
# Broadcast Functions
# -------------------------

async def broadcast_message(application: Application):

    text = db.get_setting("broadcast_message")

    users = db.get_all_users()

    logger.info(f"Broadcast started. Users: {len(users)}")

    success = 0
    failed = 0

    # Send in batches to avoid hitting Telegram rate limits
    batch_size = 30

    for i in range(0, len(users), batch_size):

        batch = users[i:i + batch_size]

        tasks = []

        for chat_id in batch:
            tasks.append(
                application.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=channel_keyboard(),
                    disable_web_page_preview=False,
                )
            )

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for result in results:

            if isinstance(result, Exception):
                failed += 1
                logger.warning(result)
            else:
                success += 1

        # Small delay between batches
        await asyncio.sleep(1)

    logger.info(
        f"Broadcast Finished | Success={success} Failed={failed}"
    )


# -------------------------
# Scheduler Wrapper
# -------------------------

async def scheduled_broadcast(application: Application):
    logger.info("Running scheduled broadcast...")
    await broadcast_message(application)


# -------------------------
# Admin Commands
# -------------------------

async def set_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await admin_only(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setbroadcast"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
            "The replied message has no text."
        )

    db.set_setting("broadcast_message", text)

    await update.message.reply_text(
        "✅ Broadcast updated."
    )


async def broadcast_now(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await admin_only(update)

    await update.message.reply_text(
        "📢 Starting broadcast..."
    )

    await broadcast_message(context.application)

    await update.message.reply_text(
        "✅ Broadcast completed."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await admin_only(update)

    users = db.get_user_count()

    await update.message.reply_text(
        f"👥 Total Users: {users}"
    )


# -------------------------
# Ignore Everything Else
# -------------------------

async def ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return


# -------------------------
# Scheduler
# -------------------------

scheduler = AsyncIOScheduler()


def start_scheduler(application: Application):

    scheduler.add_job(
        scheduled_broadcast,
        trigger="cron",
        hour=BROADCAST_HOUR,
        minute=BROADCAST_MINUTE,
        args=[application],
    )

    scheduler.start()

    logger.info(
        f"Scheduler started ({BROADCAST_HOUR:02d}:{BROADCAST_MINUTE:02d})"
    )

# -------------------------
# Main
# -------------------------

def main():

    logger.info("Starting Telegram Bot...")

    application = Application.builder().token(BOT_TOKEN).build()

    # -------------------------
    # User Commands
    # -------------------------

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("next", next_command)
    )

    application.add_handler(
        CommandHandler("more", more_command)
    )

    # -------------------------
    # Admin Commands
    # -------------------------

    application.add_handler(
        CommandHandler("setstart", set_start)
    )

    application.add_handler(
        CommandHandler("setnext", set_next)
    )

    application.add_handler(
        CommandHandler("setbroadcast", set_broadcast)
    )

    application.add_handler(
        CommandHandler("broadcastnow", broadcast_now)
    )

    application.add_handler(
        CommandHandler("stats", stats)
    )

    # -------------------------
    # Ignore Everything Else
    # -------------------------

    application.add_handler(
        MessageHandler(
            filters.ALL,
            ignore,
        )
    )

    # -------------------------
    # Start Scheduler
    # -------------------------

    start_scheduler(application)

    logger.info("Bot is running...")

    application.run_polling(
        drop_pending_updates=True
    )


# -------------------------
# Entry Point
# -------------------------

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")

    except Exception as e:
        logger.exception(e)

    finally:
        db.close()
