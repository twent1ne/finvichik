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
        "ℹ️ <b>О «Финвичике»</b>\n\n"
        "«Финвичик» — это бот для знакомств студентов Финансового университета.\n\n"
        "Мы создали его как уютное пространство, где можно найти людей со схожими интересами, "
        "познакомиться для общения, дружбы, отношений, совместных проектов или полезного университетского нетворкинга.\n\n"
        "Здесь всё построено вокруг студенческой среды: факультеты, курсы, цели знакомства и интересы помогают быстрее "
        "понять, с кем тебе будет интересно пообщаться.\n\n"
        "Что можно делать в «Финвичике»:\n"
        "• создать свою анкету;\n"
        "• добавить фото и рассказать о себе;\n"
        "• смотреть анкеты других студентов;\n"
        "• выбирать цель знакомства;\n"
        "• ставить лайки и получать взаимные мэтчи;\n"
        "• открывать контакты только после взаимной симпатии.\n\n"
        "🔒 <b>Приватность</b>\n"
        "Telegram username другого пользователя показывается только после взаимного лайка. "
        "Так знакомство остаётся комфортным и безопасным.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(lambda message: message.text == "⬅️ Назад в меню")
async def back_to_menu_button(message: Message) -> None:
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )