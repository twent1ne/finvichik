from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

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


dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(browse.router)
dp.include_router(matches.router)