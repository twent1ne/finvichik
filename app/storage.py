from typing import Any

from app.database import get_connection


def save_profile(user_id: int, profile: dict[str, Any]) -> None:
    """
    Сохраняет анкету пользователя в PostgreSQL.

    Если анкета уже есть, она обновляется.
    Если анкеты нет, она создаётся.
    """

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO profiles (
                telegram_id,
                username,
                name,
                faculty,
                course,
                goal,
                about,
                interests,
                photo_file_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = EXCLUDED.username,
                name = EXCLUDED.name,
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
                profile["faculty"],
                profile["course"],
                profile["goal"],
                profile["about"],
                profile["interests"],
                profile.get("photo_file_id"),
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
                faculty,
                course,
                goal,
                about,
                interests,
                photo_file_id,
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

    Дополнительно удаляем связанные лайки, мэтчи и блокировки.
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
    goal_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Возвращает анкеты для просмотра.

    Не показываем:
    - самого пользователя;
    - анкеты, которые пользователь уже лайкнул или пропустил;
    - анкеты, которые пользователь заблокировал;
    - анкеты пользователей, которые заблокировали текущего пользователя.

    Если goal_filter указан, показываем только анкеты с выбранной целью.
    """

    params: list[Any] = [viewer_id, viewer_id, viewer_id, viewer_id]

    query = """
        SELECT
            profiles.telegram_id,
            profiles.username,
            profiles.name,
            profiles.faculty,
            profiles.course,
            profiles.goal,
            profiles.about,
            profiles.interests,
            profiles.photo_file_id,
            profiles.created_at,
            profiles.updated_at
        FROM profiles
        WHERE profiles.telegram_id != %s
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

    if goal_filter:
        query += " AND profiles.goal = %s"
        params.append(goal_filter)

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
    любой из сторон.
    """

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                profiles.telegram_id,
                profiles.username,
                profiles.name,
                profiles.faculty,
                profiles.course,
                profiles.goal,
                profiles.about,
                profiles.interests,
                profiles.photo_file_id,
                profiles.created_at,
                profiles.updated_at
            FROM matches
            JOIN profiles
                ON profiles.telegram_id = CASE
                    WHEN matches.user1_id = %s THEN matches.user2_id
                    ELSE matches.user1_id
                END
            WHERE (matches.user1_id = %s OR matches.user2_id = %s)
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


def report_user(
    reporter_id: int,
    reported_id: int,
    reason: str | None = None,
) -> None:
    """
    Сохраняет жалобу на пользователя.

    После жалобы автоматически блокируем пользователя,
    чтобы его анкета больше не показывалась пожаловавшемуся.
    """

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reports (
                reporter_id,
                reported_id,
                reason
            )
            VALUES (%s, %s, %s)
            """,
            (reporter_id, reported_id, reason),
        )

        connection.commit()

    block_user(reporter_id, reported_id)


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
                profiles.faculty,
                profiles.course,
                profiles.goal,
                profiles.about,
                profiles.interests,
                profiles.photo_file_id,
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

    with get_connection() as connection:
        profiles_count = connection.execute(
            "SELECT COUNT(*) AS count FROM profiles"
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

        blocks_count = connection.execute(
            "SELECT COUNT(*) AS count FROM blocks"
        ).fetchone()["count"]

    return {
        "profiles_count": int(profiles_count),
        "likes_count": int(likes_count),
        "skips_count": int(skips_count),
        "matches_count": int(matches_count),
        "reports_count": int(reports_count),
        "blocks_count": int(blocks_count),
    }