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

from database import db


# --------------------------------
# Load Environment Variables
# --------------------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

CHANNEL_URL = os.getenv("CHANNEL_URL")

BROADCAST_HOUR = int(os.getenv("BROADCAST_HOUR", 21))
BROADCAST_MINUTE = int(os.getenv("BROADCAST_MINUTE", 0))


# --------------------------------
# Logging
# --------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# --------------------------------
# Helpers
# --------------------------------

def is_admin(user_id: int):
    return user_id == ADMIN_ID


async def unauthorized(update: Update):
    await update.message.reply_text(
        "❌ You are not authorized."
    )


def channel_button():

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 Join for more exclusive content",
                url=CHANNEL_URL,
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# --------------------------------
# User Commands
# --------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db.add_user(update.effective_chat.id)

    text = db.get_setting("start_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_button(),
        disable_web_page_preview=False,
    )


async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = db.get_setting("next_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_button(),
        disable_web_page_preview=False,
    )


async def more_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = db.get_setting("next_message")

    await update.message.reply_text(
        text=text,
        reply_markup=channel_button(),
        disable_web_page_preview=False,
    )


# --------------------------------
# Admin Commands
# --------------------------------

async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await unauthorized(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setstart"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
            "The replied message has no text."
        )

    db.set_setting(
        "start_message",
        text,
    )

    await update.message.reply_text(
        "✅ Start message updated."
    )


async def set_next(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await unauthorized(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setnext"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
    "The replied message has no text."
)

    db.set_setting(
        "next_message",
        text,
    )

    await update.message.reply_text(
        "✅ Next message updated."
    )

# --------------------------------
# Broadcast Functions
# --------------------------------

async def broadcast_message(application: Application):

    text = db.get_setting("broadcast_message")

    users = db.get_all_users()

    logger.info(f"Broadcast started for {len(users)} users.")

    success = 0
    failed = 0

    batch_size = 25

    for i in range(0, len(users), batch_size):

        batch = users[i:i + batch_size]

        tasks = []

        for chat_id in batch:

            tasks.append(

                application.bot.send_message(

                    chat_id=chat_id,
                    text=text,
                    reply_markup=channel_button(),
                    disable_web_page_preview=False,

                )

            )

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        for result in results:

            if isinstance(result, Exception):

                logger.warning(result)
                failed += 1

            else:

                success += 1

        # Prevent Telegram flood limits
        await asyncio.sleep(1)

    logger.info(
        f"Broadcast completed | Success={success} Failed={failed}"
    )


# --------------------------------
# JobQueue Daily Broadcast
# --------------------------------

async def daily_broadcast(context: ContextTypes.DEFAULT_TYPE):

    logger.info("Running scheduled broadcast...")

    await broadcast_message(context.application)


# --------------------------------
# Admin Commands
# --------------------------------

async def set_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await unauthorized(update)

    if not update.message.reply_to_message:
        return await update.message.reply_text(
            "Reply to a message with /setbroadcast"
        )

    text = update.message.reply_to_message.text

    if not text:
        return await update.message.reply_text(
            "The replied message has no text."
        )

    db.set_setting(
        "broadcast_message",
        text,
    )

    await update.message.reply_text(
        "✅ Broadcast updated."
    )


async def broadcast_now(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await unauthorized(update)
    
    await update.message.reply_text(
        "📢 Starting broadcast..."
    )

    await broadcast_message(context.application)

    await update.message.reply_text(
        "✅ Broadcast finished."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        return await unauthorized(update)

    count = db.get_user_count()

    await update.message.reply_text(

        f"👥 Total Users: {count}"

    )


# --------------------------------
# Ignore Everything Else
# --------------------------------

async def ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return

# --------------------------------
# Main
# --------------------------------

def main():

    logger.info("Starting Telegram Bot...")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------
    # User Commands
    # -----------------------------

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("next", next_command)
    )

    application.add_handler(
        CommandHandler("more", more_command)
    )

    # -----------------------------
    # Admin Commands
    # -----------------------------

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

    # -----------------------------
    # Ignore Everything Else
    # -----------------------------

    application.add_handler(
        MessageHandler(
            filters.ALL,
            ignore,
        )
    )

    # -----------------------------
    # Daily Broadcast (JobQueue)
    # -----------------------------

    application.job_queue.run_daily(
        daily_broadcast,
        time=time(
            hour=BROADCAST_HOUR,
            minute=BROADCAST_MINUTE,
        ),
        name="daily_broadcast",
    )

    logger.info(
        f"Daily broadcast scheduled at "
        f"{BROADCAST_HOUR:02d}:{BROADCAST_MINUTE:02d}"
    )

    logger.info("Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


# --------------------------------
# Entry Point
# --------------------------------

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.info("Bot stopped.")

    except Exception as e:

        logger.exception(e)

    finally:

        db.close()