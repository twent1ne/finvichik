from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


def get_connection() -> psycopg.Connection:
    """
    Создаёт подключение к PostgreSQL.

    row_factory=dict_row нужен, чтобы получать строки базы данных
    как словари по названиям колонок.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "Не найден DATABASE_URL. Добавь строку подключения PostgreSQL "
            "в .env или в Environment Variables на Render."
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        autocommit=False,
    )


def init_db() -> None:
    """
    Создаёт таблицы PostgreSQL, если они ещё не существуют.

    Также добавляет недостающие колонки через ALTER TABLE.
    Это важно, если таблицы уже были созданы старой версией проекта.
    """

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                name TEXT NOT NULL,
                faculty TEXT NOT NULL,
                course TEXT NOT NULL,
                goal TEXT NOT NULL,
                about TEXT NOT NULL,
                interests TEXT NOT NULL,
                photo_file_id TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        connection.execute(
            """
            ALTER TABLE profiles
            ADD COLUMN IF NOT EXISTS username TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE profiles
            ADD COLUMN IF NOT EXISTS photo_file_id TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE profiles
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()
            """
        )

        connection.execute(
            """
            ALTER TABLE profiles
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS likes (
                id BIGSERIAL PRIMARY KEY,
                from_user_id BIGINT NOT NULL,
                to_user_id BIGINT NOT NULL,
                action TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(from_user_id, to_user_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id BIGSERIAL PRIMARY KEY,
                user1_id BIGINT NOT NULL,
                user2_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user1_id, user2_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS blocks (
                id BIGSERIAL PRIMARY KEY,
                blocker_id BIGINT NOT NULL,
                blocked_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(blocker_id, blocked_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id BIGSERIAL PRIMARY KEY,
                reporter_id BIGINT NOT NULL,
                reported_id BIGINT NOT NULL,
                reason TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_likes_from_user_id
            ON likes(from_user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_likes_to_user_id
            ON likes(to_user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_user1_id
            ON matches(user1_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_user2_id
            ON matches(user2_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_blocker_id
            ON blocks(blocker_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_blocked_id
            ON blocks(blocked_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reports_reporter_id
            ON reports(reporter_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reports_reported_id
            ON reports(reported_id)
            """
        )

        connection.commit()

    print("База данных PostgreSQL готова.")


def row_to_dict(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Безопасно преобразует строку PostgreSQL в обычный dict.
    """

    if row is None:
        return None

    return dict(row)