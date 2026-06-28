# Telegram Broadcast Bot

A simple Telegram bot built with Python that:

- Responds to `/start`
- Responds to `/next`
- Responds to `/more`
- Stores users in PostgreSQL
- Sends a daily broadcast to every user
- Includes a "📢 Join Our Telegram Channel" button on every message
- Allows the admin to update messages without editing the code

---

# Features

### User Commands

- /start
- /next
- /more

### Admin Commands

- /setstart
- /setnext
- /setbroadcast
- /broadcastnow
- /stats

---

# Requirements

- Python 3.10+
- PostgreSQL
- Telegram Bot Token

---

# Installation

## Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd telegram_bot
```

## Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## Install packages

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a file named `.env`

Example:

```env
BOT_TOKEN=YOUR_BOT_TOKEN

DATABASE_URL=YOUR_POSTGRESQL_DATABASE_URL

ADMIN_ID=YOUR_TELEGRAM_USER_ID

CHANNEL_URL=https://t.me/YourChannel

BROADCAST_HOUR=21

BROADCAST_MINUTE=0
```

---

# Run

```bash
python main.py
```

---

# PostgreSQL

The bot automatically creates all required tables when it starts.

Tables:

- users
- settings

No manual SQL setup is required.

---

# Deploy on Render

1. Push the project to GitHub.
2. Create a PostgreSQL database on Render.
3. Copy the **Internal Database URL**.
4. Create a new Python Web Service on Render.
5. Add all environment variables.
6. Build Command:

```bash
pip install -r requirements.txt
```

7. Start Command:

```bash
python main.py
```

Render will automatically deploy your bot.

---

# Notes

- Only the ADMIN_ID can use admin commands.
- Unknown messages are ignored.
- Daily broadcasts are sent automatically at the configured time.
- Every message includes a "📢 Join Our Telegram Channel" button.

---

Created with Python + python-telegram-bot + PostgreSQL.