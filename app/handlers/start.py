from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, MenuButtonWebApp, WebAppInfo

from app.config import MINI_APP_URL
from app.keyboards import main_menu_keyboard


router = Router()


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    """
    Обработчик команды /start.

    При запуске бота устанавливаем Telegram Menu Button.
    Это кнопка слева от поля ввода сообщения.
    Через неё Mini App открывается одной кнопкой и без отдельного сообщения.
    """

    await message.bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(
            text="🌐 Открыть Финвичик",
            web_app=WebAppInfo(url=MINI_APP_URL),
        ),
    )

    text = (
        "👋 Привет!\n\n"
        "Я — «Финвичик», бот для студентов Финансового университета.\n\n"
        "Здесь можно:\n"
        "• найти команду для проекта;\n"
        "• познакомиться для дружбы;\n"
        "• найти отношения;\n"
        "• расширить университетский нетворкинг.\n\n"
        "Mini App можно открыть одной кнопкой — через кнопку меню слева от поля ввода сообщения."
    )

    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(),
    )


@router.message(lambda message: message.text == "ℹ️ О проекте")
async def about_button(message: Message) -> None:
    await message.answer(
        "ℹ️ «Финвичик» — учебный проект для студентов Финансового университета.\n\n"
        "Что уже работает:\n"
        "• создание анкеты;\n"
        "• сохранение анкет в SQLite;\n"
        "• просмотр чужих анкет;\n"
        "• фильтр по цели знакомства;\n"
        "• лайки и пропуски;\n"
        "• взаимные мэтчи;\n"
        "• жалобы и блокировки;\n"
        "• первая версия Telegram Mini App.\n\n"
        "Приватность: Telegram username другого пользователя показывается "
        "только после взаимного лайка.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(lambda message: message.text == "⬅️ Назад в меню")
async def back_to_menu_button(message: Message) -> None:
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )