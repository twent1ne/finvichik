import asyncio

from app.bot import bot, dp
from app.database import init_db


async def main() -> None:
    """
    Главная асинхронная функция запуска бота.
    """

    init_db()

    print("База данных SQLite готова.")
    print("Бот «Финвичик» запущен.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())