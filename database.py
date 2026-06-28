
"""
database.py

Handles all PostgreSQL operations for the Telegram bot.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )
        self.conn.autocommit = True
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:

            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id BIGINT PRIMARY KEY,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Settings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

            # Insert default settings if missing
            defaults = [
                ("start_message", "Welcome!"),
                ("next_message", "More content coming soon."),
                ("broadcast_message", "Daily broadcast.")
            ]

            for key, value in defaults:
                cur.execute("""
                    INSERT INTO settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO NOTHING;
                """, (key, value))

    # -------------------------
    # User Functions
    # -------------------------

    def add_user(self, chat_id: int):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users(chat_id)
                VALUES(%s)
                ON CONFLICT(chat_id) DO NOTHING;
            """, (chat_id,))

    def get_all_users(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT chat_id
                FROM users;
            """)
            return [row["chat_id"] for row in cur.fetchall()]

    def get_user_count(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM users;
            """)
            return cur.fetchone()["total"]

    # -------------------------
    # Settings Functions
    # -------------------------

    def get_setting(self, key: str):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT value
                FROM settings
                WHERE key=%s;
            """, (key,))
            result = cur.fetchone()

            if result:
                return result["value"]

            return None

    def set_setting(self, key: str, value: str):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO settings(key, value)
                VALUES(%s, %s)
                ON CONFLICT(key)
                DO UPDATE
                SET value = EXCLUDED.value;
            """, (key, value))

    # -------------------------
    # Cleanup
    # -------------------------

    def close(self):
        if self.conn:
            self.conn.close()


# Singleton database instance
db = Database()
