from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.handlers.profile import format_profile
from app.keyboards import (
    main_menu_keyboard,
    profile_view_keyboard,
    view_goal_filter_keyboard,
)
from app.storage import (
    block_user,
    create_match,
    get_new_likes_for_user,
    get_profile,
    get_profiles_for_viewer,
    is_mutual_like,
    report_user,
    save_like_action,
)


router = Router()


class BrowseProfiles(StatesGroup):
    """
    Состояния просмотра анкет.

    choosing_filter — пользователь выбирает фильтр обычного просмотра.
    viewing — пользователь смотрит конкретную анкету.
    """

    choosing_filter = State()
    viewing = State()


def format_profile_for_browsing(profile: dict) -> str:
    """
    Форматирует чужую анкету для просмотра.

    Важно: пока НЕ показываем Telegram username.
    Username показываем только при взаимном мэтче.
    """

    profile_copy = dict(profile)
    profile_copy["username"] = None

    return format_profile(profile_copy)


def format_match_message(
    current_user_profile: dict,
    matched_user_profile: dict,
) -> str:
    """
    Формирует текст уведомления о мэтче.

    Здесь username уже можно показать, потому что лайк взаимный.
    """

    matched_username = matched_user_profile.get("username")

    if matched_username:
        contact_text = f"@{matched_username}"
    else:
        contact_text = (
            "username не указан. Можно продолжить общение через Telegram, "
            "если пользователь позже добавит username в настройках аккаунта."
        )

    return (
        "🎉 <b>У вас новый мэтч!</b>\n\n"
        f"Вы взаимно понравились друг другу с пользователем: "
        f"<b>{matched_user_profile['name']}</b>\n\n"
        f"Цель знакомства: {matched_user_profile['goal']}\n"
        f"Интересы: {matched_user_profile['interests']}\n\n"
        f"Контакт: {contact_text}"
    )


async def notify_about_match(
    message: Message,
    current_user_id: int,
    matched_user_id: int,
) -> None:
    """
    Уведомляет обоих пользователей о новом мэтче.
    """

    current_user_profile = get_profile(current_user_id)
    matched_user_profile = get_profile(matched_user_id)

    if not current_user_profile or not matched_user_profile:
        return

    text_for_current_user = format_match_message(
        current_user_profile=current_user_profile,
        matched_user_profile=matched_user_profile,
    )

    text_for_matched_user = format_match_message(
        current_user_profile=matched_user_profile,
        matched_user_profile=current_user_profile,
    )

    await message.bot.send_message(
        chat_id=current_user_id,
        text=text_for_current_user,
        reply_markup=main_menu_keyboard(),
    )

    await message.bot.send_message(
        chat_id=matched_user_id,
        text=text_for_matched_user,
        reply_markup=main_menu_keyboard(),
    )


def get_empty_profiles_message(mode: str | None) -> str:
    """
    Возвращает текст, если в текущем режиме больше нет анкет.
    """

    if mode == "new_likes":
        return (
            "Новых лайков пока нет 😔\n\n"
            "Когда кто-то поставит тебе лайк, но ты ещё не ответишь этому пользователю, "
            "его анкета появится здесь."
        )

    return (
        "Анкеты закончились 😔\n\n"
        "Попробуй позже или выбери другой фильтр."
    )


async def send_next_profile(message: Message, state: FSMContext) -> None:
    """
    Отправляет следующую анкету из списка.

    Список анкет и текущий индекс хранятся в FSMContext.
    """

    data = await state.get_data()

    profiles = data.get("profiles", [])
    current_index = data.get("current_index", 0)
    mode = data.get("mode")

    if current_index >= len(profiles):
        await state.clear()
        await message.answer(
            get_empty_profiles_message(mode),
            reply_markup=main_menu_keyboard(),
        )
        return

    profile = profiles[current_index]

    await state.update_data(current_profile_id=profile["telegram_id"])

    prefix = "💘 <b>Новый лайк</b>\n\n" if mode == "new_likes" else ""

    text = (
        prefix
        + format_profile_for_browsing(profile)
        + "\n\n"
        "Выбери действие:"
    )

    photo_file_id = profile.get("photo_file_id")

    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=text,
            reply_markup=profile_view_keyboard(),
        )
    else:
        await message.answer(
            text=text,
            reply_markup=profile_view_keyboard(),
        )

    await state.set_state(BrowseProfiles.viewing)


@router.message(F.text == "🔎 Смотреть анкеты")
async def browse_profiles_start(message: Message, state: FSMContext) -> None:
    """
    Начинает обычный просмотр анкет.
    """

    viewer_profile = get_profile(message.from_user.id)

    if not viewer_profile:
        await message.answer(
            "Сначала нужно создать свою анкету.\n\n"
            "Нажми «📝 Создать анкету», заполни профиль, "
            "и после этого сможешь смотреть анкеты других студентов.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()

    await message.answer(
        "🔎 Какие анкеты хочешь смотреть?",
        reply_markup=view_goal_filter_keyboard(),
    )

    await state.set_state(BrowseProfiles.choosing_filter)


@router.message(F.text == "💘 Новые лайки")
async def new_likes_start(message: Message, state: FSMContext) -> None:
    """
    Показывает анкеты пользователей, которые лайкнули текущего пользователя,
    но текущий пользователь ещё не ответил им лайком, пропуском или блокировкой.
    """

    viewer_profile = get_profile(message.from_user.id)

    if not viewer_profile:
        await message.answer(
            "Сначала нужно создать свою анкету.\n\n"
            "После этого ты сможешь видеть новые лайки.",
            reply_markup=main_menu_keyboard(),
        )
        return

    profiles = get_new_likes_for_user(message.from_user.id)

    if not profiles:
        await state.clear()
        await message.answer(
            "Новых лайков пока нет 😔\n\n"
            "Когда кто-то поставит тебе лайк, но ты ещё не ответишь этому пользователю, "
            "его анкета появится здесь.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()
    await state.update_data(
        profiles=profiles,
        current_index=0,
        mode="new_likes",
    )

    await send_next_profile(message, state)


@router.message(BrowseProfiles.choosing_filter)
async def process_goal_filter(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает выбор фильтра обычного просмотра.
    """

    if not message.text:
        await message.answer(
            "Пожалуйста, выбери фильтр кнопкой.",
            reply_markup=view_goal_filter_keyboard(),
        )
        return

    text = message.text.strip()

    if text == "⬅️ Назад в меню":
        await state.clear()
        await message.answer(
            "Главное меню:",
            reply_markup=main_menu_keyboard(),
        )
        return

    allowed_filters = [
        "Все анкеты",
        "Проект",
        "Дружба",
        "Отношения",
        "Нетворкинг",
    ]

    if text not in allowed_filters:
        await message.answer(
            "Пожалуйста, выбери фильтр с помощью кнопок.",
            reply_markup=view_goal_filter_keyboard(),
        )
        return

    goal_filter = None if text == "Все анкеты" else text

    profiles = get_profiles_for_viewer(
        viewer_id=message.from_user.id,
        goal_filter=goal_filter,
    )

    if not profiles:
        await state.clear()
        await message.answer(
            "Пока нет доступных анкет по этому фильтру 😔\n\n"
            "Возможные причины:\n"
            "• другие пользователи ещё не создали анкеты;\n"
            "• ты уже просмотрел все доступные анкеты;\n"
            "• выбран слишком узкий фильтр.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.update_data(
        profiles=profiles,
        current_index=0,
        goal_filter=goal_filter,
        mode="browse",
    )

    await send_next_profile(message, state)


@router.message(BrowseProfiles.viewing, F.text == "❤️ Лайк")
async def like_current_profile(message: Message, state: FSMContext) -> None:
    """
    Сохраняет лайк текущей анкете, проверяет мэтч и показывает следующую.
    """

    data = await state.get_data()
    current_profile_id = data.get("current_profile_id")
    current_index = data.get("current_index", 0)

    if not current_profile_id:
        await state.clear()
        await message.answer(
            "Не удалось определить текущую анкету. Попробуй начать просмотр заново.",
            reply_markup=main_menu_keyboard(),
        )
        return

    current_user_id = message.from_user.id

    save_like_action(
        from_user_id=current_user_id,
        to_user_id=current_profile_id,
        action="like",
    )

    await message.answer("❤️ Лайк сохранён.")

    if is_mutual_like(current_user_id, current_profile_id):
        match_created = create_match(current_user_id, current_profile_id)

        if match_created:
            await notify_about_match(
                message=message,
                current_user_id=current_user_id,
                matched_user_id=current_profile_id,
            )

    await state.update_data(current_index=current_index + 1)

    await send_next_profile(message, state)


@router.message(BrowseProfiles.viewing, F.text == "➡️ Пропустить")
async def skip_current_profile(message: Message, state: FSMContext) -> None:
    """
    Сохраняет пропуск текущей анкеты и показывает следующую.
    """

    data = await state.get_data()
    current_profile_id = data.get("current_profile_id")
    current_index = data.get("current_index", 0)

    if not current_profile_id:
        await state.clear()
        await message.answer(
            "Не удалось определить текущую анкету. Попробуй начать просмотр заново.",
            reply_markup=main_menu_keyboard(),
        )
        return

    save_like_action(
        from_user_id=message.from_user.id,
        to_user_id=current_profile_id,
        action="skip",
    )

    await message.answer("➡️ Анкета пропущена.")

    await state.update_data(current_index=current_index + 1)

    await send_next_profile(message, state)


@router.message(BrowseProfiles.viewing, F.text == "⚠️ Пожаловаться")
async def report_current_profile(message: Message, state: FSMContext) -> None:
    """
    Отправляет жалобу на текущую анкету и больше не показывает её пользователю.
    """

    data = await state.get_data()
    current_profile_id = data.get("current_profile_id")
    current_index = data.get("current_index", 0)

    if not current_profile_id:
        await state.clear()
        await message.answer(
            "Не удалось определить текущую анкету. Попробуй начать просмотр заново.",
            reply_markup=main_menu_keyboard(),
        )
        return

    report_user(
        reporter_id=message.from_user.id,
        reported_id=current_profile_id,
        reason="Жалоба из Telegram-бота во время просмотра анкеты.",
    )

    await message.answer("⚠️ Жалоба отправлена. Эта анкета больше не будет тебе показываться.")

    await state.update_data(current_index=current_index + 1)

    await send_next_profile(message, state)


@router.message(BrowseProfiles.viewing, F.text == "🚫 Заблокировать")
async def block_current_profile(message: Message, state: FSMContext) -> None:
    """
    Блокирует текущую анкету для пользователя и показывает следующую.
    """

    data = await state.get_data()
    current_profile_id = data.get("current_profile_id")
    current_index = data.get("current_index", 0)

    if not current_profile_id:
        await state.clear()
        await message.answer(
            "Не удалось определить текущую анкету. Попробуй начать просмотр заново.",
            reply_markup=main_menu_keyboard(),
        )
        return

    block_user(
        blocker_id=message.from_user.id,
        blocked_id=current_profile_id,
    )

    await message.answer("🚫 Пользователь заблокирован. Эта анкета больше не будет тебе показываться.")

    await state.update_data(current_index=current_index + 1)

    await send_next_profile(message, state)


@router.message(BrowseProfiles.viewing, F.text == "🛑 Остановить просмотр")
async def stop_browsing(message: Message, state: FSMContext) -> None:
    """
    Останавливает просмотр анкет.
    """

    await state.clear()

    await message.answer(
        "Просмотр анкет остановлен.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(BrowseProfiles.viewing)
async def wrong_browse_action(message: Message) -> None:
    """
    Если пользователь во время просмотра пишет что-то не то.
    """

    await message.answer(
        "Пожалуйста, выбери действие кнопкой:\n"
        "❤️ Лайк\n"
        "➡️ Пропустить\n"
        "⚠️ Пожаловаться\n"
        "🚫 Заблокировать\n"
        "🛑 Остановить просмотр",
        reply_markup=profile_view_keyboard(),
    )
