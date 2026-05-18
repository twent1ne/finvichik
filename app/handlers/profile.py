from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message

from app.keyboards import (
    blocked_users_keyboard,
    cancel_keyboard,
    goals_keyboard,
    main_menu_keyboard,
    photo_keyboard,
    settings_keyboard,
)
from app.storage import (
    delete_profile,
    get_blocked_profiles,
    get_profile,
    save_profile,
    unblock_all_users,
)


router = Router()


BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"


class ProfileForm(StatesGroup):
    """
    Состояния заполнения анкеты.
    """

    name = State()
    faculty = State()
    course = State()
    goal = State()
    about = State()
    interests = State()
    photo = State()


def format_profile(profile: dict[str, Any]) -> str:
    """
    Форматирует анкету в красивый текст.

    Эту функцию используют и обработчики профиля, и просмотр чужих анкет.
    """

    username = profile.get("username")

    if username:
        username_text = f"@{username}"
    else:
        username_text = "не указан"

    return (
        "👤 <b>Анкета</b>\n\n"
        f"<b>Имя:</b> {profile.get('name', '—')}\n"
        f"<b>Факультет / направление:</b> {profile.get('faculty', '—')}\n"
        f"<b>Курс:</b> {profile.get('course', '—')}\n"
        f"<b>Цель знакомства:</b> {profile.get('goal', '—')}\n\n"
        f"<b>О себе:</b>\n{profile.get('about', '—')}\n\n"
        f"<b>Интересы:</b>\n{profile.get('interests', '—')}\n\n"
        f"<b>Telegram:</b> {username_text}"
    )


def get_local_photo_path(photo_file_id: str) -> Path | None:
    """
    Если фото загружено через Mini App, оно может храниться локально.

    В базе оно выглядит так:
    local:profile_photos/123456789.jpg

    Эта функция превращает такую строку в путь к файлу.
    Если файла уже нет на Render, возвращает None.
    """

    if not photo_file_id.startswith("local:"):
        return None

    relative_path = photo_file_id.replace("local:", "", 1).lstrip("/")

    if not relative_path:
        return None

    file_path = UPLOADS_DIR / relative_path

    try:
        file_path.resolve().relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        return None

    if not file_path.exists() or not file_path.is_file():
        return None

    return file_path


def normalize_photo_url(photo_url: str) -> str | None:
    """
    Нормализует внешний URL фото.

    Telegram плохо принимает URL с внутренним Render-портом, например:
    https://finvichik.onrender.com:10000/uploads/...

    Поэтому порт убираем. Также отбрасываем локальные адреса,
    которые Telegram всё равно не сможет открыть.
    """

    photo_url = photo_url.strip()

    if not photo_url:
        return None

    parsed = urlsplit(photo_url)

    if parsed.scheme not in {"http", "https"}:
        return None

    hostname = parsed.hostname

    if not hostname:
        return None

    blocked_hosts = {
        "0.0.0.0",
        "127.0.0.1",
        "localhost",
    }

    if hostname in blocked_hosts:
        return None

    netloc = hostname

    if parsed.username or parsed.password:
        return None

    # Важно: порт специально не добавляем обратно.
    # Telegram должен видеть публичный HTTPS URL без :10000.
    normalized_url = urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )

    return normalized_url


def resolve_photo_for_telegram(photo_file_id: str) -> FSInputFile | str | None:
    """
    Готовит фото для отправки в Telegram.

    Возможные варианты:
    - local:...          -> отправляем как FSInputFile, если файл существует;
    - https://...        -> отправляем как URL, предварительно убирая порт;
    - Telegram file_id   -> отправляем напрямую;
    - битая ссылка/файл  -> возвращаем None.
    """

    photo_file_id = photo_file_id.strip()

    if not photo_file_id:
        return None

    if photo_file_id.startswith("local:"):
        local_photo_path = get_local_photo_path(photo_file_id)

        if local_photo_path:
            return FSInputFile(local_photo_path)

        print(f"Фото профиля не найдено на сервере: {photo_file_id}")
        return None

    if photo_file_id.startswith(("http://", "https://")):
        normalized_url = normalize_photo_url(photo_file_id)

        if not normalized_url:
            print(f"Некорректный URL фото профиля: {photo_file_id}")
            return None

        return normalized_url

    # Если это не local: и не URL, считаем, что это Telegram file_id.
    return photo_file_id


async def send_profile_text(message: Message, text: str) -> None:
    """
    Отправляет анкету обычным текстом.
    """

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
    )


async def send_profile_message(
    message: Message,
    profile: dict[str, Any],
) -> None:
    """
    Отправляет анкету пользователю.

    Важно:
    если фото битое, пропало с Render или Telegram не принимает URL,
    обработчик не должен падать. В таком случае отправляем анкету текстом.
    """

    text = format_profile(profile)
    photo_file_id = profile.get("photo_file_id")

    if not photo_file_id:
        await send_profile_text(message, text)
        return

    photo = resolve_photo_for_telegram(str(photo_file_id))

    if not photo:
        await send_profile_text(message, text)
        return

    try:
        # У Telegram есть лимит на caption. Если анкета длинная,
        # сначала отправляем фото, потом полный текст отдельным сообщением.
        if len(text) <= 1000:
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=main_menu_keyboard(),
            )
        else:
            await message.answer_photo(
                photo=photo,
                reply_markup=main_menu_keyboard(),
            )
            await message.answer(text)

    except TelegramBadRequest as error:
        print(f"Не удалось отправить фото профиля: {error}")
        await send_profile_text(message, text)


@router.message(F.text == "👤 Моя анкета")
async def my_profile_button(message: Message) -> None:
    """
    Показывает анкету текущего пользователя.
    """

    profile = get_profile(message.from_user.id)

    if not profile:
        await message.answer(
            "У тебя пока нет анкеты.\n\n"
            "Нажми «📝 Создать анкету», чтобы заполнить профиль.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await send_profile_message(message, profile)


@router.message(F.text == "📝 Создать анкету")
async def create_profile_button(message: Message, state: FSMContext) -> None:
    """
    Начинает создание анкеты.
    """

    await state.clear()

    await message.answer(
        "Начинаем создание анкеты 👤\n\n"
        "Напиши своё имя.",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.name)


@router.message(F.text == "✏️ Редактировать анкету")
async def edit_profile_button(message: Message, state: FSMContext) -> None:
    """
    Начинает редактирование анкеты.

    Для простоты редактирование работает как повторное заполнение анкеты.
    Старые данные будут заменены новыми.
    """

    await state.clear()

    await message.answer(
        "Редактируем анкету ✏️\n\n"
        "Напиши своё имя.",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.name)


@router.message(ProfileForm.name, F.text == "❌ Отмена")
@router.message(ProfileForm.faculty, F.text == "❌ Отмена")
@router.message(ProfileForm.course, F.text == "❌ Отмена")
@router.message(ProfileForm.goal, F.text == "❌ Отмена")
@router.message(ProfileForm.about, F.text == "❌ Отмена")
@router.message(ProfileForm.interests, F.text == "❌ Отмена")
@router.message(ProfileForm.photo, F.text == "❌ Отмена")
async def cancel_profile_form(message: Message, state: FSMContext) -> None:
    """
    Отмена заполнения анкеты.
    """

    await state.clear()

    await message.answer(
        "Заполнение анкеты отменено.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(ProfileForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """
    Сохраняет имя.
    """

    if not message.text:
        await message.answer("Пожалуйста, напиши имя текстом.")
        return

    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Имя слишком короткое. Напиши, пожалуйста, ещё раз.")
        return

    await state.update_data(name=name)

    await message.answer(
        "Отлично.\n\n"
        "Теперь напиши факультет или направление.\n"
        "Например: «Бизнес-информатика», «Экономика», «Финансы и кредит».",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.faculty)


@router.message(ProfileForm.faculty)
async def process_faculty(message: Message, state: FSMContext) -> None:
    """
    Сохраняет факультет или направление.
    """

    if not message.text:
        await message.answer("Пожалуйста, напиши факультет или направление текстом.")
        return

    faculty = message.text.strip()

    if len(faculty) < 2:
        await message.answer("Слишком коротко. Напиши, пожалуйста, подробнее.")
        return

    await state.update_data(faculty=faculty)

    await message.answer(
        "Теперь напиши курс.\n\n"
        "Например: 1, 2, 3, 4, 5 или 6.",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.course)


@router.message(ProfileForm.course)
async def process_course(message: Message, state: FSMContext) -> None:
    """
    Сохраняет курс.
    """

    if not message.text:
        await message.answer("Пожалуйста, напиши курс текстом.")
        return

    course = message.text.strip()

    allowed_courses = ["1", "2", "3", "4", "5", "6"]

    if course not in allowed_courses:
        await message.answer(
            "Пожалуйста, укажи курс числом от 1 до 6.\n\n"
            "Например: 2"
        )
        return

    await state.update_data(course=course)

    await message.answer(
        "Выбери цель знакомства:",
        reply_markup=goals_keyboard(),
    )

    await state.set_state(ProfileForm.goal)


@router.message(ProfileForm.goal)
async def process_goal(message: Message, state: FSMContext) -> None:
    """
    Сохраняет цель знакомства.
    """

    if not message.text:
        await message.answer(
            "Пожалуйста, выбери цель кнопкой.",
            reply_markup=goals_keyboard(),
        )
        return

    goal = message.text.strip()

    allowed_goals = [
        "Проект",
        "Дружба",
        "Отношения",
        "Нетворкинг",
    ]

    if goal not in allowed_goals:
        await message.answer(
            "Пожалуйста, выбери цель с помощью кнопок.",
            reply_markup=goals_keyboard(),
        )
        return

    await state.update_data(goal=goal)

    await message.answer(
        "Теперь коротко расскажи о себе.\n\n"
        "Например: чем занимаешься, что изучаешь, какой у тебя характер.",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.about)


@router.message(ProfileForm.about)
async def process_about(message: Message, state: FSMContext) -> None:
    """
    Сохраняет описание о себе.
    """

    if not message.text:
        await message.answer("Пожалуйста, напиши описание текстом.")
        return

    about = message.text.strip()

    if len(about) < 5:
        await message.answer("Слишком коротко. Напиши хотя бы одно предложение.")
        return

    await state.update_data(about=about)

    await message.answer(
        "Напиши свои интересы.\n\n"
        "Например: стартапы, финансы, спорт, музыка, аналитика.",
        reply_markup=cancel_keyboard(),
    )

    await state.set_state(ProfileForm.interests)


@router.message(ProfileForm.interests)
async def process_interests(message: Message, state: FSMContext) -> None:
    """
    Сохраняет интересы.
    """

    if not message.text:
        await message.answer("Пожалуйста, напиши интересы текстом.")
        return

    interests = message.text.strip()

    if len(interests) < 3:
        await message.answer("Слишком коротко. Напиши интересы подробнее.")
        return

    await state.update_data(interests=interests)

    await message.answer(
        "Теперь отправь фото для анкеты.\n\n"
        "Можно отправить фотографию или нажать «⏭️ Пропустить фото».",
        reply_markup=photo_keyboard(),
    )

    await state.set_state(ProfileForm.photo)


@router.message(ProfileForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    """
    Сохраняет фото из Telegram.
    """

    largest_photo = message.photo[-1]
    photo_file_id = largest_photo.file_id

    await state.update_data(photo_file_id=photo_file_id)

    await finish_profile_creation(message, state)


@router.message(ProfileForm.photo, F.text == "⏭️ Пропустить фото")
async def skip_photo(message: Message, state: FSMContext) -> None:
    """
    Завершает создание анкеты без нового фото.

    Если анкета уже была и в ней было фото, старое фото сохраняется.
    """

    existing_profile = get_profile(message.from_user.id)

    if existing_profile:
        await state.update_data(
            photo_file_id=existing_profile.get("photo_file_id")
        )
    else:
        await state.update_data(photo_file_id=None)

    await finish_profile_creation(message, state)


@router.message(ProfileForm.photo)
async def wrong_photo(message: Message) -> None:
    """
    Если пользователь на этапе фото отправил что-то не то.
    """

    await message.answer(
        "Пожалуйста, отправь именно фото или нажми «⏭️ Пропустить фото».",
        reply_markup=photo_keyboard(),
    )


async def finish_profile_creation(message: Message, state: FSMContext) -> None:
    """
    Финально сохраняет анкету в базу данных.
    """

    data = await state.get_data()

    profile = {
        "username": message.from_user.username,
        "name": data["name"],
        "faculty": data["faculty"],
        "course": data["course"],
        "goal": data["goal"],
        "about": data["about"],
        "interests": data["interests"],
        "photo_file_id": data.get("photo_file_id"),
    }

    save_profile(
        user_id=message.from_user.id,
        profile=profile,
    )

    await state.clear()

    saved_profile = get_profile(message.from_user.id)

    await message.answer(
        "Анкета сохранена ✅",
        reply_markup=main_menu_keyboard(),
    )

    if saved_profile:
        await send_profile_message(message, saved_profile)


@router.message(F.text == "⚙️ Настройки")
async def settings_button(message: Message) -> None:
    """
    Показывает настройки.
    """

    await message.answer(
        "⚙️ Настройки\n\n"
        "Здесь можно редактировать или удалить анкету, а также посмотреть заблокированных пользователей.",
        reply_markup=settings_keyboard(),
    )


@router.message(F.text == "🗑 Удалить анкету")
async def delete_profile_button(message: Message) -> None:
    """
    Удаляет анкету пользователя.
    """

    profile = get_profile(message.from_user.id)

    if not profile:
        await message.answer(
            "У тебя пока нет анкеты.",
            reply_markup=main_menu_keyboard(),
        )
        return

    delete_profile(message.from_user.id)

    await message.answer(
        "Анкета удалена 🗑\n\n"
        "Ты можешь создать новую анкету в любой момент.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🚫 Заблокированные")
async def blocked_users_button(message: Message) -> None:
    """
    Показывает список заблокированных пользователей.
    """

    blocked_profiles = get_blocked_profiles(message.from_user.id)

    if not blocked_profiles:
        await message.answer(
            "У тебя пока нет заблокированных пользователей.",
            reply_markup=blocked_users_keyboard(),
        )
        return

    text_parts = [
        "🚫 <b>Заблокированные пользователи</b>\n",
    ]

    for index, profile in enumerate(blocked_profiles, start=1):
        text_parts.append(
            f"{index}. <b>{profile['name']}</b>\n"
            f"Цель: {profile['goal']}\n"
            f"Интересы: {profile['interests']}"
        )

    await message.answer(
        "\n\n".join(text_parts),
        reply_markup=blocked_users_keyboard(),
    )


@router.message(F.text == "♻️ Разблокировать всех")
async def unblock_all_users_button(message: Message) -> None:
    """
    Разблокирует всех пользователей, которых заблокировал текущий пользователь.
    """

    unblock_all_users(message.from_user.id)

    await message.answer(
        "♻️ Все пользователи разблокированы.\n\n"
        "Теперь их анкеты снова могут появляться в просмотре, "
        "если они подходят под фильтр и не были лайкнуты или пропущены ранее.",
        reply_markup=main_menu_keyboard(),
    )