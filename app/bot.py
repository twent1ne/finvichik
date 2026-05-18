from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import BOT_TOKEN
from app.handlers import admin, browse, matches, profile, start


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
# сначала админские команды, чтобы /reports, /my_id,
# /resolve_report_..., /block_profile_... и /unblock_profile_...
# точно обрабатывались отдельным admin router.
dp.include_router(admin.router)

# Потом /start и базовое меню.
dp.include_router(start.router)

# Потом анкета, просмотр и мэтчи.
dp.include_router(profile.router)
dp.include_router(browse.router)
dp.include_router(matches.router)