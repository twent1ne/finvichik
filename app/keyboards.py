from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню бота.

    Mini App здесь НЕ открываем через KeyboardButton(web_app=...),
    потому что у тебя из-за этого возвращалась ошибка авторизации Telegram.

    Mini App теперь открывается через Telegram Menu Button,
    который устанавливается в start.py.
    """

    keyboard = [
        [
            KeyboardButton(text="👤 Моя анкета"),
            KeyboardButton(text="📝 Создать анкету"),
        ],
        [
            KeyboardButton(text="🔎 Смотреть анкеты"),
            KeyboardButton(text="💘 Новые лайки"),
        ],
        [
            KeyboardButton(text="💌 Мои мэтчи"),
            KeyboardButton(text="⚙️ Настройки"),
        ],
        [
            KeyboardButton(text="ℹ️ О проекте"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Можно отменить заполнение",
    )


def goals_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="Проект"),
            KeyboardButton(text="Дружба"),
        ],
        [
            KeyboardButton(text="Отношения"),
            KeyboardButton(text="Нетворкинг"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери цель знакомства",
    )


def view_goal_filter_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="Все анкеты"),
        ],
        [
            KeyboardButton(text="Проект"),
            KeyboardButton(text="Дружба"),
        ],
        [
            KeyboardButton(text="Отношения"),
            KeyboardButton(text="Нетворкинг"),
        ],
        [
            KeyboardButton(text="⬅️ Назад в меню"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери фильтр",
    )


def profile_view_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="❤️ Лайк"),
            KeyboardButton(text="➡️ Пропустить"),
        ],
        [
            KeyboardButton(text="⚠️ Пожаловаться"),
            KeyboardButton(text="🚫 Заблокировать"),
        ],
        [
            KeyboardButton(text="🛑 Остановить просмотр"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


def photo_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="⏭️ Пропустить фото"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Отправь фото или пропусти",
    )


def settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="✏️ Редактировать анкету"),
        ],
        [
            KeyboardButton(text="🗑 Удалить анкету"),
        ],
        [
            KeyboardButton(text="🚫 Заблокированные"),
        ],
        [
            KeyboardButton(text="⬅️ Назад в меню"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери настройку",
    )


def blocked_users_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="♻️ Разблокировать всех"),
        ],
        [
            KeyboardButton(text="⬅️ Назад в меню"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Управление блокировками",
    )
