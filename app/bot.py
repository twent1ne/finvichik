from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.handlers import browse, matches, profile, start


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    ),
)


dp = Dispatcher(
    storage=MemoryStorage(),
)


# Важен порядок:
# сначала /start и базовое меню,
# потом анкета,
# потом просмотр и мэтчи.
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(browse.router)
dp.include_router(matches.router)