import asyncio
import os

import uvicorn

from app.bot import bot, dp
from app.database import init_db
from web import app


async def run_bot() -> None:
    """
    Запускает Telegram-бота в режиме polling.
    """

    print("Бот «Финвичик» запускается...")

    await dp.start_polling(bot)


async def run_web() -> None:
    """
    Запускает FastAPI backend для Mini App.
    Render передаёт порт через переменную окружения PORT.
    """

    port = int(os.getenv("PORT", "8000"))

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )

    server = uvicorn.Server(config)

    print(f"Mini App backend запускается на порту {port}...")

    await server.serve()


async def main() -> None:
    """
    Одновременно запускает базу, Mini App backend и Telegram-бота.
    """

    init_db()

    print("База данных SQLite готова.")
    print("Запускаем backend и Telegram-бота...")

    await asyncio.gather(
        run_web(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())