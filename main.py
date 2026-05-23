import asyncio

import aiohttp

from app.bot import bot, dp
from app.config import MINI_APP_URL
from app.database import init_db


async def keep_mini_app_awake() -> None:
    """
    Периодически пингует Mini App backend.

    Это нужно, чтобы Render Free не засыпал,
    пока Telegram-бот работает на Waifly через polling.
    """

    if not MINI_APP_URL:
        print("MINI_APP_URL не указан. Keep-alive отключён.")
        return

    if "localhost" in MINI_APP_URL or "127.0.0.1" in MINI_APP_URL:
        print("MINI_APP_URL указывает на localhost. Keep-alive отключён.")
        return

    await asyncio.sleep(30)

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(MINI_APP_URL, timeout=20) as response:
                    print(
                        f"Keep-alive ping Mini App: {MINI_APP_URL} "
                        f"status={response.status}"
                    )
        except Exception as error:
            print(f"Keep-alive ping failed: {error}")

        await asyncio.sleep(10 * 60)


async def main() -> None:
    """
    Запуск Telegram-бота через polling.

    На Waifly бот работает постоянно.
    Mini App остаётся на Render, а этот процесс периодически пингует Render,
    чтобы уменьшить проблему cold start.
    """

    init_db()

    print("База данных готова.")
    print("Удаляем Telegram webhook перед polling-запуском...")

    await bot.delete_webhook(
        drop_pending_updates=True,
    )

    print("Бот «Финвичик» запущен через polling.")

    asyncio.create_task(keep_mini_app_awake())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())