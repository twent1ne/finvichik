from typing import Any
from urllib.parse import urlsplit, urlunsplit

from app.config import (
    REPORTS_DAILY_LIMIT,
    REPORTS_DAILY_WINDOW_HOURS,
    REPORTS_WEEKLY_BLOCK_LIMIT,
    REPORTS_WEEKLY_WINDOW_DAYS,
    TEMPORARY_PROFILE_BLOCK_HOURS,
)
from app.database import get_connection


ALLOWED_GENDERS = {"Парень", "Девушка"}


def normalize_gender(gender: Any) -> str | None:
    """
    Нормализует пол перед сохранением и фильтрацией.
    """

    if gender is None:
        return None

    value = str(gender).strip()

    if not value:
        return None

    if value not in ALLOWED_GENDERS:
        return None

    return value


def normalize_age(age: Any) -> int | None:
    """
    Нормализует возраст перед сохранением и фильтрацией.
    """

    if age is None:
        return None

    try:
        value = int(str(age).strip())
    except (TypeError, ValueError):
        return None

    if value < 16 or value > 80:
        return None

    return value


def normalize_course(course: Any) -> str | None:
    """
    Нормализует курс для фильтрации.
    """

    if course is None:
        return None

    value = str(course).strip()

    if value not in {"1", "2", "3", "4", "5", "6"}:
        return None

    return value


def normalize_goal(goal: Any) -> str | None:
    """
    Нормализует цель знакомства для фильтрации.
    """

    if goal is None:
        return None

    value = str(goal).strip()

    if value not in {"Проект", "Дружба", "Отношения", "Нетворкинг"}:
        return None

    return value


def normalize_report_reason(reason: Any) -> str:
    """
    Нормализует текст жалобы.

    Пустую жалобу заменяем на стандартный текст.
    Слишком длинную обрезаем, чтобы не перегружать базу и админские сообщения.
    """

    if reason is None:
        return "Причина не указана."

    value = str(reason).strip()

    if not value:
        return "Причина не указана."

    max_length = 1000

    if len(value) > max_length:
        value = value[:max_length].strip() + "..."

    return value


def normalize_photo_file_id(photo_file_id: Any) -> str | None:
    """
    Нормализует photo_file_id перед сохранением в базу.

    Возможные варианты:
    - None или пустая строка -> None
    - Telegram file_id -> сохраняем как есть
    - local:profile_photos/123.jpg -> сохраняем как есть
    - cloudinary:finvichik/profile_photos/123/123456789 -> сохраняем как есть
    - https://...:10000/... -> убираем порт, чтобы Telegram не ругался
    """

    if photo_file_id is None:
        return None

    value = str(photo_file_id).strip()

    if not value:
        return None

    if value.startswith(("local:", "cloudinary:")):
        return value

    if not value.startswith(("http://", "https://")):
        return value

    parsed = urlsplit(value)

    if not parsed.scheme or not parsed.hostname:
        return None

    if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return None

    if parsed.username or parsed.password:
        return None

    normalized_url = urlunsplit(
        (
            parsed.scheme,
            parsed.hostname,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )

    return normalized_url


def release_expired_profile_blocks() -> None:
    """
    Снимает временные блокировки, у которых истёк срок.

    Вечные блокировки не трогаем.
    """

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE profiles
            SET
                moderation_status = 'active',
                blocked_until = NULL,
                updated_at = NOW()
            WHERE moderation_status = 'temporary_block'
            AND blocked_until IS NOT NULL
            AND blocked_until <= NOW()
            """
        )

        connection.commit()


def save_profile(user_id: int, profile: dict[str, Any]) -> None:
    """
    Сохраняет анкету пользователя в PostgreSQL.

    Если анкета уже есть, она обновляется.
    Если анкеты нет, она создаётся.

    Важно:
    при редактировании анкеты не сбрасываем moderation_status.
    Если анкета заблокирована, редактирование не должно автоматически
    возвращать её в просмотр.
    """

    gender = normalize_gender(profile.get("gender"))
    age = normalize_age(profile.get("age"))
    photo_file_id = normalize_photo_file_id(profile.get("photo_file_id"))

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO profiles (
                telegram_id,
                username,
                name,
                gender,
                age,
                faculty,
                course,
                goal,
                about,
                interests,
                photo_file_id,
                moderation_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = EXCLUDED.username,
                name = EXCLUDED.name,
                gender = EXCLUDED.gender,
                age = EXCLUDED.age,
                faculty = EXCLUDED.faculty,
                course = EXCLUDED.course,
                goal = EXCLUDED.goal,
                about = EXCLUDED.about,
                interests = EXCLUDED.interests,
                photo_file_id = EXCLUDED.photo_file_id,
                updated_at = NOW()
            """,
            (
                user_id,
                profile.get("username"),
                profile["name"],
                gender,
                age,
                profile["faculty"],
                profile["course"],
                profile["goal"],
                profile["about"],
                profile["interests"],
                photo_file_id,
            ),
        )

        connection.commit()


def get_profile(user_id: int) -> dict[str, Any] | None:
    """
    Возвращает анкету пользователя из PostgreSQL.
    Если анкеты нет, возвращает None.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                telegram_id,
                username,
                name,
                gender,
                age,
                faculty,
                course,
                goal,
                about,
                interests,
                photo_file_id,
                moderation_status,
                blocked_until,
                permanent_blocked_at,
                created_at,
                updated_at
            FROM profiles
            WHERE telegram_id = %s
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def delete_profile(user_id: int) -> None:
    """
    Удаляет анкету пользователя из PostgreSQL.

    Дополнительно удаляем связанные лайки, мэтчи, блокировки, жалобы
    и события модерации.
    """

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM likes
            WHERE from_user_id = %s OR to_user_id = %s
            """,
            (user_id, user_id),
        )

        connection.execute(
            """
            DELETE FROM matches
            WHERE user1_id = %s OR user2_id = %s
            """,
            (user_id, user_id),
        )

        connection.execute(
            """
            DELETE FROM blocks
            WHERE blocker_id = %s OR blocked_id = %s
            """,
            (user_id, user_id),
        )

        connection.execute(
            """
            DELETE FROM reports
            WHERE reporter_id = %s OR reported_id = %s
            """,
            (user_id, user_id),
        )

        connection.execute(
            """
            DELETE FROM profile_moderation_events
            WHERE telegram_id = %s
            """,
            (user_id,),
        )

        connection.execute(
            """
            DELETE FROM profiles
            WHERE telegram_id = %s
            """,
            (user_id,),
        )

        connection.commit()


def has_profile(user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя анкета.
    """

    return get_profile(user_id) is not None


def get_profiles_for_viewer(
    viewer_id: int,
    gender_filter: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    goal_filter: str | None = None,
    course_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Возвращает анкеты для просмотра.

    Не показываем:
    - самого пользователя;
    - анкеты, которые пользователь уже лайкнул или пропустил;
    - анкеты, которые пользователь заблокировал;
    - анкеты пользователей, которые заблокировали текущего пользователя;
    - анкеты, временно или навсегда заблокированные модерацией.

    Фильтры:
    - gender_filter: Парень / Девушка;
    - age_min: минимальный возраст;
    - age_max: максимальный возраст;
    - goal_filter: цель знакомства;
    - course_filter: курс.
    """

    release_expired_profile_blocks()

    normalized_gender = normalize_gender(gender_filter)
    normalized_age_min = normalize_age(age_min)
    normalized_age_max = normalize_age(age_max)
    normalized_goal = normalize_goal(goal_filter)
    normalized_course = normalize_course(course_filter)

    params: list[Any] = [viewer_id, viewer_id, viewer_id, viewer_id]

    query = """
        SELECT
            profiles.telegram_id,
            profiles.username,
            profiles.name,
            profiles.gender,
            profiles.age,
            profiles.faculty,
            profiles.course,
            profiles.goal,
            profiles.about,
            profiles.interests,
            profiles.photo_file_id,
            profiles.moderation_status,
            profiles.blocked_until,
            profiles.permanent_blocked_at,
            profiles.created_at,
            profiles.updated_at
        FROM profiles
        WHERE profiles.telegram_id != %s
        AND COALESCE(profiles.moderation_status, 'active') = 'active'
        AND profiles.telegram_id NOT IN (
            SELECT likes.to_user_id
            FROM likes
            WHERE likes.from_user_id = %s
        )
        AND profiles.telegram_id NOT IN (
            SELECT blocks.blocked_id
            FROM blocks
            WHERE blocks.blocker_id = %s
        )
        AND profiles.telegram_id NOT IN (
            SELECT blocks.blocker_id
            FROM blocks
            WHERE blocks.blocked_id = %s
        )
    """

    if normalized_gender:
        query += " AND profiles.gender = %s"
        params.append(normalized_gender)

    if normalized_age_min is not None:
        query += " AND profiles.age >= %s"
        params.append(normalized_age_min)

    if normalized_age_max is not None:
        query += " AND profiles.age <= %s"
        params.append(normalized_age_max)

    if normalized_goal:
        query += " AND profiles.goal = %s"
        params.append(normalized_goal)

    if normalized_course:
        query += " AND profiles.course = %s"
        params.append(normalized_course)

    query += " ORDER BY profiles.updated_at DESC"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def save_like_action(
    from_user_id: int,
    to_user_id: int,
    action: str,
) -> None:
    """
    Сохраняет действие пользователя по отношению к анкете.

    action может быть:
    - like
    - skip
    """

    if action not in {"like", "skip"}:
        raise ValueError("action должен быть 'like' или 'skip'.")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO likes (
                from_user_id,
                to_user_id,
                action
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (from_user_id, to_user_id) DO UPDATE SET
                action = EXCLUDED.action,
                created_at = NOW()
            """,
            (from_user_id, to_user_id, action),
        )

        connection.commit()


def get_like_action(
    from_user_id: int,
    to_user_id: int,
) -> str | None:
    """
    Возвращает действие пользователя по отношению к другой анкете.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT action
            FROM likes
            WHERE from_user_id = %s
            AND to_user_id = %s
            """,
            (from_user_id, to_user_id),
        ).fetchone()

    if row is None:
        return None

    return str(row["action"])


def undo_last_skip_action(from_user_id: int) -> dict[str, Any] | None:
    """
    Отменяет последний пропуск анкеты текущим пользователем.

    Если пропущенная анкета сейчас заблокирована модерацией,
    не возвращаем её в просмотр.
    """

    release_expired_profile_blocks()

    with get_connection() as connection:
        skipped_row = connection.execute(
            """
            SELECT
                likes.to_user_id
            FROM likes
            JOIN profiles
                ON profiles.telegram_id = likes.to_user_id
            WHERE likes.from_user_id = %s
            AND likes.action = 'skip'
            AND COALESCE(profiles.moderation_status, 'active') = 'active'
            ORDER BY likes.created_at DESC
            LIMIT 1
            """,
            (from_user_id,),
        ).fetchone()

        if skipped_row is None:
            return None

        skipped_user_id = skipped_row["to_user_id"]

        connection.execute(
            """
            DELETE FROM likes
            WHERE from_user_id = %s
            AND to_user_id = %s
            AND action = 'skip'
            """,
            (from_user_id, skipped_user_id),
        )

        profile_row = connection.execute(
            """
            SELECT
                telegram_id,
                username,
                name,
                gender,
                age,
                faculty,
                course,
                goal,
                about,
                interests,
                photo_file_id,
                moderation_status,
                blocked_until,
                permanent_blocked_at,
                created_at,
                updated_at
            FROM profiles
            WHERE telegram_id = %s
            """,
            (skipped_user_id,),
        ).fetchone()

        connection.commit()

    if profile_row is None:
        return None

    return dict(profile_row)


def remove_like_action(
    from_user_id: int,
    to_user_id: int,
) -> bool:
    """
    Убирает лайк текущего пользователя с другой анкеты.

    Логика:
    - удаляем запись из likes, где текущий пользователь поставил like;
    - если между пользователями был мэтч, удаляем его;
    - лайк второго пользователя не трогаем.

    Возвращает True, если лайк реально был удалён.
    Возвращает False, если лайка не было.
    """

    normalized_user1_id, normalized_user2_id = normalize_match_pair(
        from_user_id,
        to_user_id,
    )

    with get_connection() as connection:
        deleted_like = connection.execute(
            """
            DELETE FROM likes
            WHERE from_user_id = %s
            AND to_user_id = %s
            AND action = 'like'
            RETURNING id
            """,
            (from_user_id, to_user_id),
        ).fetchone()

        connection.execute(
            """
            DELETE FROM matches
            WHERE user1_id = %s
            AND user2_id = %s
            """,
            (normalized_user1_id, normalized_user2_id),
        )

        connection.commit()

    return deleted_like is not None


def is_mutual_like(
    user1_id: int,
    user2_id: int,
) -> bool:
    """
    Проверяет, поставили ли пользователи лайк друг другу.
    """

    first_like = get_like_action(user1_id, user2_id)
    second_like = get_like_action(user2_id, user1_id)

    return first_like == "like" and second_like == "like"


def normalize_match_pair(
    user1_id: int,
    user2_id: int,
) -> tuple[int, int]:
    """
    Приводит пару пользователей к единому порядку.
    """

    if user1_id < user2_id:
        return user1_id, user2_id

    return user2_id, user1_id


def create_match(
    user1_id: int,
    user2_id: int,
) -> bool:
    """
    Создаёт мэтч между двумя пользователями.

    Возвращает True, если мэтч создан впервые.
    Возвращает False, если такой мэтч уже был.
    """

    normalized_user1_id, normalized_user2_id = normalize_match_pair(
        user1_id,
        user2_id,
    )

    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO matches (
                user1_id,
                user2_id
            )
            VALUES (%s, %s)
            ON CONFLICT (user1_id, user2_id) DO NOTHING
            RETURNING id
            """,
            (normalized_user1_id, normalized_user2_id),
        ).fetchone()

        connection.commit()

    return row is not None


def get_user_matches(user_id: int) -> list[dict[str, Any]]:
    """
    Возвращает список анкет, с которыми у пользователя есть мэтч.

    Не показываем мэтчи с пользователями, которые были заблокированы
    любой из сторон или заблокированы модерацией.
    """

    release_expired_profile_blocks()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                profiles.telegram_id,
                profiles.username,
                profiles.name,
                profiles.gender,
                profiles.age,
                profiles.faculty,
                profiles.course,
                profiles.goal,
                profiles.about,
                profiles.interests,
                profiles.photo_file_id,
                profiles.moderation_status,
                profiles.blocked_until,
                profiles.permanent_blocked_at,
                profiles.created_at,
                profiles.updated_at
            FROM matches
            JOIN profiles
                ON profiles.telegram_id = CASE
                    WHEN matches.user1_id = %s THEN matches.user2_id
                    ELSE matches.user1_id
                END
            WHERE (matches.user1_id = %s OR matches.user2_id = %s)
            AND COALESCE(profiles.moderation_status, 'active') = 'active'
            AND profiles.telegram_id NOT IN (
                SELECT blocks.blocked_id
                FROM blocks
                WHERE blocks.blocker_id = %s
            )
            AND profiles.telegram_id NOT IN (
                SELECT blocks.blocker_id
                FROM blocks
                WHERE blocks.blocked_id = %s
            )
            ORDER BY matches.created_at DESC
            """,
            (user_id, user_id, user_id, user_id, user_id),
        ).fetchall()

    return [dict(row) for row in rows]


def block_user(
    blocker_id: int,
    blocked_id: int,
) -> None:
    """
    Блокирует пользователя.

    После блокировки:
    - удаляем лайки между пользователями;
    - удаляем мэтч между пользователями, если был;
    - сохраняем запись о блокировке.
    """

    normalized_user1_id, normalized_user2_id = normalize_match_pair(
        blocker_id,
        blocked_id,
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO blocks (
                blocker_id,
                blocked_id
            )
            VALUES (%s, %s)
            ON CONFLICT (blocker_id, blocked_id) DO NOTHING
            """,
            (blocker_id, blocked_id),
        )

        connection.execute(
            """
            DELETE FROM likes
            WHERE
                (from_user_id = %s AND to_user_id = %s)
                OR
                (from_user_id = %s AND to_user_id = %s)
            """,
            (blocker_id, blocked_id, blocked_id, blocker_id),
        )

        connection.execute(
            """
            DELETE FROM matches
            WHERE user1_id = %s
            AND user2_id = %s
            """,
            (normalized_user1_id, normalized_user2_id),
        )

        connection.commit()


def count_recent_reports(
    reported_id: int,
    window_hours: int = REPORTS_DAILY_WINDOW_HOURS,
) -> int:
    """
    Считает количество жалоб на пользователя за последние window_hours часов.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM reports
            WHERE reported_id = %s
            AND created_at >= NOW() - (%s * INTERVAL '1 hour')
            """,
            (reported_id, window_hours),
        ).fetchone()

    return int(row["count"])


def count_recent_temporary_blocks(
    telegram_id: int,
    window_days: int = REPORTS_WEEKLY_WINDOW_DAYS,
) -> int:
    """
    Считает количество временных блокировок пользователя за последние window_days дней.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM profile_moderation_events
            WHERE telegram_id = %s
            AND event_type = 'temporary_block'
            AND created_at >= NOW() - (%s * INTERVAL '1 day')
            """,
            (telegram_id, window_days),
        ).fetchone()

    return int(row["count"])


def get_profile_moderation_summary(telegram_id: int) -> dict[str, Any]:
    """
    Возвращает сводку по жалобам и блокировкам анкеты.
    """

    profile = get_profile(telegram_id)

    return {
        "profile": profile,
        "reports_24h": count_recent_reports(
            telegram_id,
            REPORTS_DAILY_WINDOW_HOURS,
        ),
        "temporary_blocks_7d": count_recent_temporary_blocks(
            telegram_id,
            REPORTS_WEEKLY_WINDOW_DAYS,
        ),
    }


def apply_report_moderation_rules(
    reported_id: int,
) -> dict[str, Any]:
    """
    Применяет автоматические правила модерации:

    - 5 жалоб за 24 часа -> временная блокировка на 24 часа;
    - 3 временных блокировки за 7 дней -> вечная блокировка.

    Возвращает информацию о том, что произошло.
    """

    release_expired_profile_blocks()

    result: dict[str, Any] = {
        "reports_24h": 0,
        "temporary_blocks_7d": 0,
        "temporary_block_applied": False,
        "permanent_block_applied": False,
        "blocked_until": None,
    }

    with get_connection() as connection:
        profile = connection.execute(
            """
            SELECT
                telegram_id,
                moderation_status,
                blocked_until,
                permanent_blocked_at
            FROM profiles
            WHERE telegram_id = %s
            """,
            (reported_id,),
        ).fetchone()

        if profile is None:
            connection.commit()
            return result

        if profile["moderation_status"] == "permanent_block":
            reports_row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM reports
                WHERE reported_id = %s
                AND created_at >= NOW() - (%s * INTERVAL '1 hour')
                """,
                (reported_id, REPORTS_DAILY_WINDOW_HOURS),
            ).fetchone()

            blocks_row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM profile_moderation_events
                WHERE telegram_id = %s
                AND event_type = 'temporary_block'
                AND created_at >= NOW() - (%s * INTERVAL '1 day')
                """,
                (reported_id, REPORTS_WEEKLY_WINDOW_DAYS),
            ).fetchone()

            connection.commit()

            result["reports_24h"] = int(reports_row["count"])
            result["temporary_blocks_7d"] = int(blocks_row["count"])
            return result

        reports_row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM reports
            WHERE reported_id = %s
            AND created_at >= NOW() - (%s * INTERVAL '1 hour')
            """,
            (reported_id, REPORTS_DAILY_WINDOW_HOURS),
        ).fetchone()

        reports_24h = int(reports_row["count"])
        result["reports_24h"] = reports_24h

        if reports_24h < REPORTS_DAILY_LIMIT:
            blocks_row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM profile_moderation_events
                WHERE telegram_id = %s
                AND event_type = 'temporary_block'
                AND created_at >= NOW() - (%s * INTERVAL '1 day')
                """,
                (reported_id, REPORTS_WEEKLY_WINDOW_DAYS),
            ).fetchone()

            result["temporary_blocks_7d"] = int(blocks_row["count"])

            connection.commit()
            return result

        recent_temp_event = connection.execute(
            """
            SELECT id
            FROM profile_moderation_events
            WHERE telegram_id = %s
            AND event_type = 'temporary_block'
            AND created_at >= NOW() - (%s * INTERVAL '1 hour')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (reported_id, REPORTS_DAILY_WINDOW_HOURS),
        ).fetchone()

        if recent_temp_event is None and profile["moderation_status"] != "temporary_block":
            blocked_row = connection.execute(
                """
                UPDATE profiles
                SET
                    moderation_status = 'temporary_block',
                    blocked_until = NOW() + (%s * INTERVAL '1 hour'),
                    updated_at = NOW()
                WHERE telegram_id = %s
                RETURNING blocked_until
                """,
                (TEMPORARY_PROFILE_BLOCK_HOURS, reported_id),
            ).fetchone()

            blocked_until = blocked_row["blocked_until"] if blocked_row else None

            connection.execute(
                """
                INSERT INTO profile_moderation_events (
                    telegram_id,
                    event_type,
                    reason,
                    expires_at
                )
                VALUES (%s, 'temporary_block', %s, %s)
                """,
                (
                    reported_id,
                    (
                        f"Автоблокировка: {REPORTS_DAILY_LIMIT} жалоб "
                        f"за {REPORTS_DAILY_WINDOW_HOURS} часов."
                    ),
                    blocked_until,
                ),
            )

            result["temporary_block_applied"] = True
            result["blocked_until"] = blocked_until

        blocks_row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM profile_moderation_events
            WHERE telegram_id = %s
            AND event_type = 'temporary_block'
            AND created_at >= NOW() - (%s * INTERVAL '1 day')
            """,
            (reported_id, REPORTS_WEEKLY_WINDOW_DAYS),
        ).fetchone()

        temporary_blocks_7d = int(blocks_row["count"])
        result["temporary_blocks_7d"] = temporary_blocks_7d

        if temporary_blocks_7d >= REPORTS_WEEKLY_BLOCK_LIMIT:
            connection.execute(
                """
                UPDATE profiles
                SET
                    moderation_status = 'permanent_block',
                    blocked_until = NULL,
                    permanent_blocked_at = NOW(),
                    updated_at = NOW()
                WHERE telegram_id = %s
                AND moderation_status != 'permanent_block'
                """,
                (reported_id,),
            )

            permanent_event = connection.execute(
                """
                INSERT INTO profile_moderation_events (
                    telegram_id,
                    event_type,
                    reason
                )
                VALUES (%s, 'permanent_block', %s)
                RETURNING id
                """,
                (
                    reported_id,
                    (
                        f"Вечная блокировка: {REPORTS_WEEKLY_BLOCK_LIMIT} "
                        f"временных блокировок за {REPORTS_WEEKLY_WINDOW_DAYS} дней."
                    ),
                ),
            ).fetchone()

            if permanent_event is not None:
                result["permanent_block_applied"] = True

        connection.commit()

    return result


def report_user(
    reporter_id: int,
    reported_id: int,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Сохраняет жалобу на пользователя.

    После жалобы:
    - сохраняем запись в reports;
    - блокируем анкету для пожаловавшегося пользователя;
    - применяем автоматические правила модерации;
    - возвращаем данные для уведомления админов.
    """

    normalized_reason = normalize_report_reason(reason)

    with get_connection() as connection:
        report_row = connection.execute(
            """
            INSERT INTO reports (
                reporter_id,
                reported_id,
                reason,
                status
            )
            VALUES (%s, %s, %s, 'new')
            RETURNING
                id,
                reporter_id,
                reported_id,
                reason,
                status,
                created_at
            """,
            (reporter_id, reported_id, normalized_reason),
        ).fetchone()

        connection.commit()

    block_user(reporter_id, reported_id)

    moderation_result = apply_report_moderation_rules(reported_id)

    reported_profile = get_profile(reported_id)
    reporter_profile = get_profile(reporter_id)

    return {
        "report": dict(report_row) if report_row else None,
        "reporter_profile": reporter_profile,
        "reported_profile": reported_profile,
        "moderation": moderation_result,
    }


def get_reports_for_admin(
    status: str | None = "new",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Возвращает список жалоб для админского просмотра.

    status='new' — только новые жалобы.
    status=None — все жалобы.
    """

    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    params: list[Any] = []

    query = """
        SELECT
            reports.id,
            reports.reporter_id,
            reports.reported_id,
            reports.reason,
            reports.status,
            reports.reviewed_by,
            reports.reviewed_at,
            reports.created_at,

            reporter.username AS reporter_username,
            reporter.name AS reporter_name,

            reported.username AS reported_username,
            reported.name AS reported_name,
            reported.gender AS reported_gender,
            reported.age AS reported_age,
            reported.faculty AS reported_faculty,
            reported.course AS reported_course,
            reported.goal AS reported_goal,
            reported.about AS reported_about,
            reported.interests AS reported_interests,
            reported.photo_file_id AS reported_photo_file_id,
            reported.moderation_status AS reported_moderation_status,
            reported.blocked_until AS reported_blocked_until,
            reported.permanent_blocked_at AS reported_permanent_blocked_at
        FROM reports
        LEFT JOIN profiles AS reporter
            ON reporter.telegram_id = reports.reporter_id
        LEFT JOIN profiles AS reported
            ON reported.telegram_id = reports.reported_id
    """

    if status:
        query += " WHERE reports.status = %s"
        params.append(status)

    query += " ORDER BY reports.created_at DESC LIMIT %s"
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_report_by_id(report_id: int) -> dict[str, Any] | None:
    """
    Возвращает одну жалобу по ID.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                reports.id,
                reports.reporter_id,
                reports.reported_id,
                reports.reason,
                reports.status,
                reports.reviewed_by,
                reports.reviewed_at,
                reports.created_at,

                reporter.username AS reporter_username,
                reporter.name AS reporter_name,

                reported.username AS reported_username,
                reported.name AS reported_name,
                reported.gender AS reported_gender,
                reported.age AS reported_age,
                reported.faculty AS reported_faculty,
                reported.course AS reported_course,
                reported.goal AS reported_goal,
                reported.about AS reported_about,
                reported.interests AS reported_interests,
                reported.photo_file_id AS reported_photo_file_id,
                reported.moderation_status AS reported_moderation_status,
                reported.blocked_until AS reported_blocked_until,
                reported.permanent_blocked_at AS reported_permanent_blocked_at
            FROM reports
            LEFT JOIN profiles AS reporter
                ON reporter.telegram_id = reports.reporter_id
            LEFT JOIN profiles AS reported
                ON reported.telegram_id = reports.reported_id
            WHERE reports.id = %s
            """,
            (report_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def mark_report_reviewed(
    report_id: int,
    reviewed_by: int,
) -> bool:
    """
    Помечает жалобу как обработанную.

    Возвращает True, если жалоба найдена и обновлена.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE reports
            SET
                status = 'reviewed',
                reviewed_by = %s,
                reviewed_at = NOW()
            WHERE id = %s
            RETURNING id
            """,
            (reviewed_by, report_id),
        ).fetchone()

        connection.commit()

    return row is not None


def manually_block_profile(
    telegram_id: int,
    reason: str | None = None,
) -> bool:
    """
    Навсегда блокирует анкету вручную.

    Может использоваться админом позже.
    """

    normalized_reason = normalize_report_reason(reason)

    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE profiles
            SET
                moderation_status = 'permanent_block',
                blocked_until = NULL,
                permanent_blocked_at = NOW(),
                updated_at = NOW()
            WHERE telegram_id = %s
            RETURNING telegram_id
            """,
            (telegram_id,),
        ).fetchone()

        if row is not None:
            connection.execute(
                """
                INSERT INTO profile_moderation_events (
                    telegram_id,
                    event_type,
                    reason
                )
                VALUES (%s, 'permanent_block', %s)
                """,
                (telegram_id, normalized_reason),
            )

        connection.commit()

    return row is not None


def manually_unblock_profile(telegram_id: int) -> bool:
    """
    Снимает модерационную блокировку с анкеты вручную.

    Может использоваться админом позже.
    """

    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE profiles
            SET
                moderation_status = 'active',
                blocked_until = NULL,
                permanent_blocked_at = NULL,
                updated_at = NOW()
            WHERE telegram_id = %s
            RETURNING telegram_id
            """,
            (telegram_id,),
        ).fetchone()

        if row is not None:
            connection.execute(
                """
                INSERT INTO profile_moderation_events (
                    telegram_id,
                    event_type,
                    reason
                )
                VALUES (%s, 'manual_unblock', 'Анкета разблокирована администратором.')
                """,
                (telegram_id,),
            )

        connection.commit()

    return row is not None


def get_blocked_profiles(user_id: int) -> list[dict[str, Any]]:
    """
    Возвращает список пользователей, которых заблокировал текущий пользователь.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                profiles.telegram_id,
                profiles.username,
                profiles.name,
                profiles.gender,
                profiles.age,
                profiles.faculty,
                profiles.course,
                profiles.goal,
                profiles.about,
                profiles.interests,
                profiles.photo_file_id,
                profiles.moderation_status,
                profiles.blocked_until,
                profiles.permanent_blocked_at,
                profiles.created_at,
                profiles.updated_at
            FROM blocks
            JOIN profiles
                ON profiles.telegram_id = blocks.blocked_id
            WHERE blocks.blocker_id = %s
            ORDER BY blocks.created_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def unblock_all_users(user_id: int) -> None:
    """
    Удаляет все блокировки, которые сделал пользователь.

    Это удобно для тестирования.
    В реальном продукте лучше делать точечную разблокировку.
    """

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM blocks
            WHERE blocker_id = %s
            """,
            (user_id,),
        )

        connection.commit()


def get_project_stats() -> dict[str, int]:
    """
    Возвращает агрегированную статистику проекта.

    Эти данные нужны для демонстрации:
    сколько анкет, лайков, мэтчей, жалоб и блокировок есть в системе.
    """

    release_expired_profile_blocks()

    with get_connection() as connection:
        profiles_count = connection.execute(
            "SELECT COUNT(*) AS count FROM profiles"
        ).fetchone()["count"]

        active_profiles_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM profiles
            WHERE COALESCE(moderation_status, 'active') = 'active'
            """
        ).fetchone()["count"]

        temporary_blocked_profiles_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM profiles
            WHERE moderation_status = 'temporary_block'
            """
        ).fetchone()["count"]

        permanently_blocked_profiles_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM profiles
            WHERE moderation_status = 'permanent_block'
            """
        ).fetchone()["count"]

        likes_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM likes
            WHERE action = 'like'
            """
        ).fetchone()["count"]

        skips_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM likes
            WHERE action = 'skip'
            """
        ).fetchone()["count"]

        matches_count = connection.execute(
            "SELECT COUNT(*) AS count FROM matches"
        ).fetchone()["count"]

        reports_count = connection.execute(
            "SELECT COUNT(*) AS count FROM reports"
        ).fetchone()["count"]

        new_reports_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM reports
            WHERE status = 'new'
            """
        ).fetchone()["count"]

        blocks_count = connection.execute(
            "SELECT COUNT(*) AS count FROM blocks"
        ).fetchone()["count"]

    return {
        "profiles_count": int(profiles_count),
        "active_profiles_count": int(active_profiles_count),
        "temporary_blocked_profiles_count": int(temporary_blocked_profiles_count),
        "permanently_blocked_profiles_count": int(permanently_blocked_profiles_count),
        "likes_count": int(likes_count),
        "skips_count": int(skips_count),
        "matches_count": int(matches_count),
        "reports_count": int(reports_count),
        "new_reports_count": int(new_reports_count),
        "blocks_count": int(blocks_count),
    }