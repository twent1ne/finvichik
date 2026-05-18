from html import escape

from aiogram import F, Router
from aiogram.types import Message

from app.keyboards import main_menu_keyboard
from app.storage import get_profile, get_user_matches


router = Router()


def format_match_list_item(profile: dict, number: int) -> str:
    """
    Форматирует один мэтч для списка.
    """

    username = profile.get("username")

    if username:
        username_text = f"@{escape(username)}"
    else:
        username_text = "username не указан"

    return (
        f"{number}. <b>{escape(profile['name'])}</b>\n"
        f"Цель: {escape(profile['goal'])}\n"
        f"Интересы: {escape(profile['interests'])}\n"
        f"Контакт: {username_text}"
    )


@router.message(F.text == "💌 Мои мэтчи")
async def my_matches_button(message: Message) -> None:
    """
    Показывает список мэтчей пользователя.
    """

    user_profile = get_profile(message.from_user.id)

    if not user_profile:
        await message.answer(
            "Сначала нужно создать анкету.\n\n"
            "После этого ты сможешь получать мэтчи.",
            reply_markup=main_menu_keyboard(),
        )
        return

    matches = get_user_matches(message.from_user.id)

    if not matches:
        await message.answer(
            "Пока мэтчей нет 😔\n\n"
            "Нажми «🔎 Смотреть анкеты» и ставь лайки. "
            "Когда лайк будет взаимным, мэтч появится здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return

    text_parts = [
        "💌 <b>Твои мэтчи</b>\n",
    ]

    for index, profile in enumerate(matches, start=1):
        text_parts.append(format_match_list_item(profile, index))

    await message.answer(
        "\n\n".join(text_parts),
        reply_markup=main_menu_keyboard(),
    )