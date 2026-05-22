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
            "Проверь файл .env или переменные окружения хостинга."
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


def parse_int_list(value: str | None) -> set[int]:
    """
    Превращает строку вида:
    123,456,789

    в set:
    {123, 456, 789}

    Нужна для ADMIN_TELEGRAM_IDS.
    """

    if not value:
        return set()

    result: set[int] = set()

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            result.add(int(item))
        except ValueError:
            raise RuntimeError(
                "ADMIN_TELEGRAM_IDS должен содержать только числовые Telegram ID, "
                "разделённые запятыми. Например: 783877203,123456789"
            )

    return result


def get_int_env(name: str, default: int) -> int:
    """
    Возвращает числовую переменную окружения.

    Если переменной нет, используется default.
    """

    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError:
        raise RuntimeError(
            f"Переменная окружения {name} должна быть числом."
        )


BOT_TOKEN = get_required_env("BOT_TOKEN")

MINI_APP_URL = normalize_url(
    os.getenv("MINI_APP_URL", "http://localhost:8000")
)

ALLOW_DEV_AUTH = os.getenv("ALLOW_DEV_AUTH", "false").lower() == "true"

DATABASE_URL = os.getenv("DATABASE_URL")

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"
IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT"))


# Telegram ID админов, которым будут приходить жалобы.
#
# Пример:
# ADMIN_TELEGRAM_IDS=783877203
#
# Несколько админов:
# ADMIN_TELEGRAM_IDS=783877203,123456789
ADMIN_TELEGRAM_IDS = parse_int_list(
    os.getenv("ADMIN_TELEGRAM_IDS")
)


# Cloudinary.
#
# Эти переменные нужны для хранения фото профилей не на диске хостинга,
# а во внешнем постоянном хранилище Cloudinary.
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "").strip()
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "").strip()


# Настройки модерации жалоб.
#
# Если на анкету приходит REPORTS_DAILY_LIMIT жалоб
# за REPORTS_DAILY_WINDOW_HOURS часов,
# анкета блокируется на TEMPORARY_PROFILE_BLOCK_HOURS часов.
REPORTS_DAILY_LIMIT = get_int_env("REPORTS_DAILY_LIMIT", 5)
REPORTS_DAILY_WINDOW_HOURS = get_int_env("REPORTS_DAILY_WINDOW_HOURS", 24)
TEMPORARY_PROFILE_BLOCK_HOURS = get_int_env("TEMPORARY_PROFILE_BLOCK_HOURS", 24)

# Если временная блокировка повторяется REPORTS_WEEKLY_BLOCK_LIMIT раз
# за REPORTS_WEEKLY_WINDOW_DAYS дней,
# анкета блокируется навсегда.
REPORTS_WEEKLY_BLOCK_LIMIT = get_int_env("REPORTS_WEEKLY_BLOCK_LIMIT", 3)
REPORTS_WEEKLY_WINDOW_DAYS = get_int_env("REPORTS_WEEKLY_WINDOW_DAYS", 7)


def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь админом.
    """

    return int(user_id) in ADMIN_TELEGRAM_IDS


if (IS_RENDER or IS_RAILWAY) and not DATABASE_URL:
    raise RuntimeError(
        "На хостинге не найдена переменная DATABASE_URL. "
        "Добавь DATABASE_URL в Environment Variables."
    )


if (IS_RENDER or IS_RAILWAY) and "localhost" in MINI_APP_URL:
    raise RuntimeError(
        "На хостинге переменная MINI_APP_URL не должна быть localhost. "
        "Укажи публичный адрес приложения."
    )


if IS_RENDER and ":10000" in MINI_APP_URL:
    raise RuntimeError(
        "В MINI_APP_URL не нужно указывать внутренний порт Render :10000. "
        "Правильно: https://finvichik.onrender.com"
    )