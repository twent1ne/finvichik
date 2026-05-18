import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def get_required_env(name: str) -> str:
    """
    Возвращает обязательную переменную окружения.

    Если переменной нет, сразу падаем с понятной ошибкой.
    Это лучше, чем потом ловить странные ошибки в Telegram или базе.
    """

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Не найдена переменная окружения {name}. "
            "Проверь файл .env или переменные окружения Render."
        )

    return value


def normalize_url(url: str) -> str:
    """
    Убирает пробелы и завершающий слэш у URL.

    Например:
    https://finvichik.onrender.com/
    превращается в:
    https://finvichik.onrender.com
    """

    return url.strip().rstrip("/")


BOT_TOKEN = get_required_env("BOT_TOKEN")

MINI_APP_URL = normalize_url(
    os.getenv("MINI_APP_URL", "http://localhost:8000")
)

ALLOW_DEV_AUTH = os.getenv("ALLOW_DEV_AUTH", "false").lower() == "true"

DATABASE_URL = os.getenv("DATABASE_URL")

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"


if IS_RENDER and not DATABASE_URL:
    raise RuntimeError(
        "На Render не найдена переменная DATABASE_URL. "
        "Из-за этого проект может случайно работать на SQLite вместо Neon/PostgreSQL. "
        "Добавь DATABASE_URL в Render → Environment."
    )


if IS_RENDER and "localhost" in MINI_APP_URL:
    raise RuntimeError(
        "На Render переменная MINI_APP_URL не должна быть localhost. "
        "Укажи публичный адрес, например: https://finvichik.onrender.com"
    )


if IS_RENDER and ":10000" in MINI_APP_URL:
    raise RuntimeError(
        "В MINI_APP_URL не нужно указывать внутренний порт Render :10000. "
        "Правильно: https://finvichik.onrender.com"
    )