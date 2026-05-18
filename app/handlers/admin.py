import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import is_admin
from app.storage import (
    get_report_by_id,
    get_reports_for_admin,
    manually_block_profile,
    manually_unblock_profile,
    mark_report_reviewed,
)


router = Router()


def admin_only(message: Message) -> bool:
    """
    Проверяет, что команду выполняет админ.
    """

    return bool(message.from_user and is_admin(message.from_user.id))


def format_value(value) -> str:
    """
    Безопасно форматирует значение для HTML-сообщения Telegram.
    """

    if value is None or value == "":
        return "—"

    return html.escape(str(value))


def format_username(username: str | None) -> str:
    """
    Форматирует username.
    """

    if not username:
        return "не указан"

    return f"@{html.escape(username)}"


def format_report_short(report: dict) -> str:
    """
    Краткое отображение жалобы для списка.
    """

    report_id = format_value(report.get("id"))
    reporter_id = format_value(report.get("reporter_id"))
    reported_id = format_value(report.get("reported_id"))
    reason = format_value(report.get("reason"))
    created_at = format_value(report.get("created_at"))

    reported_name = format_value(report.get("reported_name"))
    reported_username = format_username(report.get("reported_username"))
    moderation_status = format_value(report.get("reported_moderation_status"))

    return (
        f"🚨 <b>Жалоба #{report_id}</b>\n"
        f"<b>Дата:</b> {created_at}\n"
        f"<b>От:</b> <code>{reporter_id}</code>\n"
        f"<b>На:</b> <code>{reported_id}</code> — {reported_name} ({reported_username})\n"
        f"<b>Статус анкеты:</b> {moderation_status}\n"
        f"<b>Причина:</b> {reason}\n\n"
        f"/report_{report_id} — открыть подробно\n"
        f"/resolve_report_{report_id} — пометить обработанной\n"
        f"/block_profile_{reported_id} — заблокировать анкету навсегда\n"
        f"/unblock_profile_{reported_id} — разблокировать анкету"
    )


def format_report_details(report: dict) -> str:
    """
    Подробное отображение жалобы.
    """

    report_id = format_value(report.get("id"))
    reporter_id = format_value(report.get("reporter_id"))
    reported_id = format_value(report.get("reported_id"))
    reason = format_value(report.get("reason"))
    status = format_value(report.get("status"))
    created_at = format_value(report.get("created_at"))
    reviewed_by = format_value(report.get("reviewed_by"))
    reviewed_at = format_value(report.get("reviewed_at"))

    reporter_name = format_value(report.get("reporter_name"))
    reporter_username = format_username(report.get("reporter_username"))

    reported_name = format_value(report.get("reported_name"))
    reported_username = format_username(report.get("reported_username"))
    reported_gender = format_value(report.get("reported_gender"))
    reported_age = format_value(report.get("reported_age"))
    reported_faculty = format_value(report.get("reported_faculty"))
    reported_course = format_value(report.get("reported_course"))
    reported_goal = format_value(report.get("reported_goal"))
    reported_about = format_value(report.get("reported_about"))
    reported_interests = format_value(report.get("reported_interests"))
    moderation_status = format_value(report.get("reported_moderation_status"))
    blocked_until = format_value(report.get("reported_blocked_until"))
    permanent_blocked_at = format_value(report.get("reported_permanent_blocked_at"))

    return (
        f"🚨 <b>Жалоба #{report_id}</b>\n\n"
        f"<b>Статус жалобы:</b> {status}\n"
        f"<b>Создана:</b> {created_at}\n"
        f"<b>Обработал:</b> {reviewed_by}\n"
        f"<b>Обработана:</b> {reviewed_at}\n\n"
        f"<b>Кто пожаловался:</b>\n"
        f"ID: <code>{reporter_id}</code>\n"
        f"Имя: {reporter_name}\n"
        f"Username: {reporter_username}\n\n"
        f"<b>На кого пожаловались:</b>\n"
        f"ID: <code>{reported_id}</code>\n"
        f"Имя: {reported_name}\n"
        f"Username: {reported_username}\n"
        f"Пол: {reported_gender}\n"
        f"Возраст: {reported_age}\n"
        f"Факультет: {reported_faculty}\n"
        f"Курс: {reported_course}\n"
        f"Цель: {reported_goal}\n\n"
        f"<b>Статус модерации анкеты:</b> {moderation_status}\n"
        f"<b>Блокировка до:</b> {blocked_until}\n"
        f"<b>Вечная блокировка:</b> {permanent_blocked_at}\n\n"
        f"<b>Причина жалобы:</b>\n"
        f"{reason}\n\n"
        f"<b>О себе:</b>\n"
        f"{reported_about}\n\n"
        f"<b>Интересы:</b>\n"
        f"{reported_interests}\n\n"
        f"<b>Команды:</b>\n"
        f"/resolve_report_{report_id} — пометить жалобу обработанной\n"
        f"/block_profile_{reported_id} — заблокировать анкету навсегда\n"
        f"/unblock_profile_{reported_id} — разблокировать анкету"
    )


@router.message(Command("my_id"))
async def my_id_command(message: Message) -> None:
    """
    Показывает Telegram ID пользователя.

    Нужно, чтобы быстро узнать свой ID и добавить его в ADMIN_TELEGRAM_IDS.
    """

    if not message.from_user:
        return

    await message.answer(
        f"Твой Telegram ID: <code>{message.from_user.id}</code>"
    )


@router.message(Command("reports"))
@router.message(F.text == "🛡 Жалобы")
async def reports_command(message: Message) -> None:
    """
    Показывает последние новые жалобы.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    reports = get_reports_for_admin(
        status="new",
        limit=10,
    )

    if not reports:
        await message.answer(
            "Новых жалоб нет.\n\n"
            "Можно посмотреть все жалобы командой /reports_all."
        )
        return

    text_parts = [
        "🛡 <b>Новые жалобы</b>\n",
    ]

    for report in reports:
        text_parts.append(format_report_short(report))

    await message.answer("\n\n".join(text_parts))


@router.message(Command("reports_all"))
async def reports_all_command(message: Message) -> None:
    """
    Показывает последние жалобы без фильтра по статусу.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    reports = get_reports_for_admin(
        status=None,
        limit=10,
    )

    if not reports:
        await message.answer("Жалоб пока нет.")
        return

    text_parts = [
        "🛡 <b>Последние жалобы</b>\n",
    ]

    for report in reports:
        text_parts.append(format_report_short(report))

    await message.answer("\n\n".join(text_parts))


@router.message(F.text.regexp(r"^/report_(\d+)$"))
async def report_details_command(message: Message) -> None:
    """
    Показывает подробности одной жалобы.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    if not message.text:
        return

    report_id = int(message.text.replace("/report_", "", 1))

    report = get_report_by_id(report_id)

    if not report:
        await message.answer("Жалоба не найдена.")
        return

    await message.answer(format_report_details(report))


@router.message(F.text.regexp(r"^/resolve_report_(\d+)$"))
async def resolve_report_command(message: Message) -> None:
    """
    Помечает жалобу как обработанную.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    if not message.text or not message.from_user:
        return

    report_id = int(message.text.replace("/resolve_report_", "", 1))

    updated = mark_report_reviewed(
        report_id=report_id,
        reviewed_by=message.from_user.id,
    )

    if not updated:
        await message.answer("Жалоба не найдена.")
        return

    await message.answer(
        f"✅ Жалоба #{report_id} помечена как обработанная."
    )


@router.message(F.text.regexp(r"^/block_profile_(\d+)$"))
async def block_profile_command(message: Message) -> None:
    """
    Навсегда блокирует анкету.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    if not message.text:
        return

    telegram_id = int(message.text.replace("/block_profile_", "", 1))

    blocked = manually_block_profile(
        telegram_id=telegram_id,
        reason=f"Анкета заблокирована администратором {message.from_user.id}.",
    )

    if not blocked:
        await message.answer("Анкета не найдена.")
        return

    await message.answer(
        f"⛔ Анкета <code>{telegram_id}</code> заблокирована навсегда."
    )


@router.message(F.text.regexp(r"^/unblock_profile_(\d+)$"))
async def unblock_profile_command(message: Message) -> None:
    """
    Снимает модерационную блокировку с анкеты.
    """

    if not admin_only(message):
        await message.answer("Этот раздел доступен только администратору.")
        return

    if not message.text:
        return

    telegram_id = int(message.text.replace("/unblock_profile_", "", 1))

    unblocked = manually_unblock_profile(telegram_id)

    if not unblocked:
        await message.answer("Анкета не найдена.")
        return

    await message.answer(
        f"✅ Анкета <code>{telegram_id}</code> разблокирована."
    )