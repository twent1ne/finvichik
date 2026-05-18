import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "finvichik.db"


def get_connection() -> sqlite3.Connection:
    """
    Создаёт подключение к базе данных SQLite.

    row_factory нужен, чтобы получать строки базы данных
    как словари по названиям колонок.
    """

    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db() -> None:
    """
    Создаёт таблицы базы данных, если они ещё не существуют.
    """

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT NOT NULL,
                faculty TEXT NOT NULL,
                course TEXT NOT NULL,
                goal TEXT NOT NULL,
                about TEXT NOT NULL,
                interests TEXT NOT NULL,
                photo_file_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user_id, to_user_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user1_id, user2_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blocker_id INTEGER NOT NULL,
                blocked_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(blocker_id, blocked_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                reported_id INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()