import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import ALLOW_DEV_AUTH, BOT_TOKEN
from app.database import init_db
from app.storage import (
    block_user,
    create_match,
    get_profile,
    get_profiles_for_viewer,
    get_project_stats,
    get_user_matches,
    is_mutual_like,
    remove_like_action,
    report_user,
    save_like_action,
    save_profile,
    undo_last_skip_action,
)


BASE_DIR = Path(__file__).resolve().parent
MINIAPP_DIR = BASE_DIR / "miniapp"
STATIC_DIR = MINIAPP_DIR / "static"
TEMPLATES_DIR = MINIAPP_DIR / "templates"

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROFILE_PHOTOS_DIR = UPLOADS_DIR / "profile_photos"


DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
PROFILE_PHOTOS_DIR.mkdir(exist_ok=True)


app = FastAPI(
    title="Финвичик Mini App Backend",
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


# Оставляем /uploads для обратной совместимости:
# старые ссылки могут ещё встречаться в кэше браузера или фронтенда.
# Но новые photo_url ниже будут идти через /api/photo/{telegram_id}.
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads",
)


templates = Jinja2Templates(directory=TEMPLATES_DIR)


class ProfileIn(BaseModel):
    name: str
    faculty: str
    course: str
    goal: str
    about: str
    interests: str
    photo_file_id: Optional[str] = None


class BrowseActionIn(BaseModel):
    target_user_id: int
    action: str


class UnlikeProfileIn(BaseModel):
    target_user_id: int


def validate_telegram_init_data(init_data: str) -> dict[str, Any]:
    """
    Проверяет подпись Telegram Web App initData.
    """

    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram hash",
        )

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=BOT_TOKEN.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram hash",
        )

    auth_date_raw = parsed_data.get("auth_date")

    if auth_date_raw:
        auth_date = int(auth_date_raw)
        now = int(time.time())

        max_age_seconds = 60 * 60 * 24

        if now - auth_date > max_age_seconds:
            raise HTTPException(
                status_code=401,
                detail="Telegram auth data is too old",
            )

    user_raw = parsed_data.get("user")

    if not user_raw:
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram user",
        )

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram user data",
        )

    if not user.get("id"):
        raise HTTPException(
            status_code=401,
            detail="Missing Telegram user id",
        )

    return user


def get_current_telegram_user(
    x_telegram_init_data: str | None,
) -> dict[str, Any]:
    """
    Возвращает текущего Telegram-пользователя.
    """

    if x_telegram_init_data:
        return validate_telegram_init_data(x_telegram_init_data)

    if ALLOW_DEV_AUTH:
        return {
            "id": 123456789,
            "first_name": "Локальный",
            "last_name": "Тест",
            "username": "local_test",
        }

    raise HTTPException(
        status_code=401,
        detail="Telegram initData is required",
    )


def get_safe_local_photo_path(photo_file_id: str) -> Path | None:
    """
    Возвращает безопасный путь к локальному фото.

    В базе локальные фото хранятся так:
    local:profile_photos/123456789.jpg

    Если файла нет или путь подозрительный, возвращаем None.
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


def is_telegram_file_id(photo_file_id: str) -> bool:
    """
    Проверяет, похоже ли значение на Telegram file_id.

    local:... — это локальный файл.
    http/https — это внешний URL.
    Всё остальное считаем Telegram file_id.
    """

    if photo_file_id.startswith("local:"):
        return False

    if photo_file_id.startswith(("http://", "https://")):
        return False

    return True


def get_photo_url(profile: dict[str, Any]) -> str | None:
    """
    Возвращает URL фотографии профиля для Mini App.

    Важно:
    больше не возвращаем прямой путь /uploads/profile_photos/...
    Вместо этого всегда отдаём /api/photo/{telegram_id}.

    Так backend сам решает:
    - отдать локальный файл;
    - сделать redirect на Telegram-файл;
    - вернуть 404, если фото уже исчезло.
    """

    photo_file_id = profile.get("photo_file_id")

    if not photo_file_id:
        return None

    telegram_id = profile.get("telegram_id")

    if not telegram_id:
        return None

    updated_at = profile.get("updated_at") or int(time.time())

    return f"/api/photo/{telegram_id}?v={updated_at}"


def profile_with_photo_url(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Добавляет в профиль поле photo_url.
    """

    result = dict(profile)
    result["photo_url"] = get_photo_url(result)

    return result


def profile_for_public_view(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Возвращает анкету для просмотра другими пользователями.

    Username скрываем до взаимного мэтча.
    """

    return {
        "telegram_id": profile["telegram_id"],
        "name": profile["name"],
        "faculty": profile["faculty"],
        "course": profile["course"],
        "goal": profile["goal"],
        "about": profile["about"],
        "interests": profile["interests"],
        "photo_file_id": profile.get("photo_file_id"),
        "photo_url": get_photo_url(profile),
    }


def get_telegram_file_url(file_id: str) -> str:
    """
    Получает прямую ссылку на файл Telegram по file_id.
    """

    import urllib.request

    get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"

    try:
        with urllib.request.urlopen(get_file_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"Не удалось получить Telegram file URL: {error}")
        raise HTTPException(
            status_code=404,
            detail="Telegram file not found",
        )

    if not data.get("ok"):
        raise HTTPException(
            status_code=404,
            detail="Telegram file not found",
        )

    file_path = data["result"]["file_path"]

    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"


def delete_old_local_profile_photos(telegram_id: int, keep_file_name: str) -> None:
    """
    Удаляет старые локальные фото пользователя с другими расширениями.

    Например, если было 123.png, а пользователь загрузил 123.jpg,
    старый файл удаляем, чтобы не копить мусор.
    """

    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        old_path = PROFILE_PHOTOS_DIR / f"{telegram_id}{extension}"

        if old_path.name == keep_file_name:
            continue

        if old_path.exists() and old_path.is_file():
            try:
                old_path.unlink()
            except OSError as error:
                print(f"Не удалось удалить старое фото {old_path}: {error}")


@app.on_event("startup")
def startup() -> None:
    """
    При запуске backend создаём таблицы базы данных.
    """

    init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Главная страница Mini App.
    """

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/api/me")
async def api_get_me(
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Возвращает текущего пользователя, которого видит backend.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)

    return {
        "id": telegram_user.get("id"),
        "first_name": telegram_user.get("first_name"),
        "last_name": telegram_user.get("last_name"),
        "username": telegram_user.get("username"),
        "is_dev_auth": not bool(x_telegram_init_data),
    }


@app.get("/api/profile/me")
async def api_get_my_profile(
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Получить анкету текущего Telegram-пользователя.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    telegram_id = int(telegram_user["id"])

    profile = get_profile(telegram_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    return profile_with_photo_url(profile)


@app.post("/api/profile")
async def api_save_my_profile(
    profile: ProfileIn,
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Сохранить анкету текущего Telegram-пользователя.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)

    telegram_id = int(telegram_user["id"])
    username = telegram_user.get("username")

    existing_profile = get_profile(telegram_id)

    profile_data = profile.model_dump()
    profile_data["telegram_id"] = telegram_id
    profile_data["username"] = username

    if existing_profile and not profile_data.get("photo_file_id"):
        profile_data["photo_file_id"] = existing_profile.get("photo_file_id")

    save_profile(
        user_id=telegram_id,
        profile=profile_data,
    )

    return {
        "ok": True,
        "message": "Profile saved",
    }


@app.post("/api/profile/photo")
async def api_upload_my_photo(
    photo: UploadFile = File(...),
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Загружает или обновляет фото профиля из Mini App.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    telegram_id = int(telegram_user["id"])

    profile = get_profile(telegram_id)

    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Create your profile first",
        )

    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only images are allowed",
        )

    extension = ".jpg"

    if photo.filename:
        filename_lower = photo.filename.lower()

        if filename_lower.endswith(".png"):
            extension = ".png"
        elif filename_lower.endswith(".webp"):
            extension = ".webp"
        elif filename_lower.endswith(".jpeg"):
            extension = ".jpg"
        elif filename_lower.endswith(".jpg"):
            extension = ".jpg"

    PROFILE_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    file_name = f"{telegram_id}{extension}"
    file_path = PROFILE_PHOTOS_DIR / file_name

    content = await photo.read()

    max_size_bytes = 5 * 1024 * 1024

    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail="Photo is too large",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Photo is empty",
        )

    file_path.write_bytes(content)
    delete_old_local_profile_photos(telegram_id, keep_file_name=file_name)

    local_photo_id = f"local:profile_photos/{file_name}"

    updated_profile = dict(profile)
    updated_profile["photo_file_id"] = local_photo_id
    updated_profile["username"] = telegram_user.get("username")

    save_profile(
        user_id=telegram_id,
        profile=updated_profile,
    )

    return {
        "ok": True,
        "message": "Photo uploaded",
        "photo_url": f"/api/photo/{telegram_id}?v={int(time.time())}",
    }


@app.get("/api/photo/{telegram_id}")
async def api_get_profile_photo(telegram_id: int):
    """
    Возвращает фото профиля.

    Если фото загружено из Mini App — отдаём локальный файл.
    Если фото загружено через Telegram-бота — перенаправляем на файл Telegram.
    """

    profile = get_profile(telegram_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    photo_file_id = profile.get("photo_file_id")

    if not photo_file_id:
        raise HTTPException(
            status_code=404,
            detail="Photo not found",
        )

    photo_file_id = str(photo_file_id).strip()

    if not photo_file_id:
        raise HTTPException(
            status_code=404,
            detail="Photo not found",
        )

    local_photo_path = get_safe_local_photo_path(photo_file_id)

    if local_photo_path:
        return FileResponse(local_photo_path)

    if photo_file_id.startswith("local:"):
        print(f"Локальное фото профиля отсутствует: {photo_file_id}")
        raise HTTPException(
            status_code=404,
            detail="Local photo not found",
        )

    if photo_file_id.startswith(("http://", "https://")):
        return RedirectResponse(photo_file_id)

    if is_telegram_file_id(photo_file_id):
        telegram_file_url = get_telegram_file_url(photo_file_id)
        return RedirectResponse(telegram_file_url)

    raise HTTPException(
        status_code=404,
        detail="Photo not found",
    )


@app.get("/api/browse/next")
async def api_get_next_profile(
    goal: str | None = None,
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Возвращает следующую анкету для просмотра в Mini App.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    viewer_id = int(telegram_user["id"])

    viewer_profile = get_profile(viewer_id)

    if not viewer_profile:
        raise HTTPException(
            status_code=400,
            detail="Create your profile first",
        )

    allowed_goals = ["Проект", "Дружба", "Отношения", "Нетворкинг"]

    if goal and goal not in allowed_goals:
        raise HTTPException(
            status_code=400,
            detail="Invalid goal filter",
        )

    profiles = get_profiles_for_viewer(
        viewer_id=viewer_id,
        goal_filter=goal,
    )

    if not profiles:
        return {
            "profile": None,
            "message": "No profiles available",
        }

    return {
        "profile": profile_for_public_view(profiles[0]),
    }


@app.post("/api/browse/action")
async def api_browse_action(
    action_data: BrowseActionIn,
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Выполняет действие над анкетой:
    like, skip, report, block.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    current_user_id = int(telegram_user["id"])
    target_user_id = int(action_data.target_user_id)

    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot interact with yourself",
        )

    target_profile = get_profile(target_user_id)

    if not target_profile:
        raise HTTPException(
            status_code=404,
            detail="Target profile not found",
        )

    if action_data.action == "like":
        save_like_action(
            from_user_id=current_user_id,
            to_user_id=target_user_id,
            action="like",
        )

        is_match = False

        if is_mutual_like(current_user_id, target_user_id):
            is_match = create_match(current_user_id, target_user_id)

        return {
            "ok": True,
            "action": "like",
            "match": is_match,
            "matched_profile": profile_with_photo_url(target_profile) if is_match else None,
        }

    if action_data.action == "skip":
        save_like_action(
            from_user_id=current_user_id,
            to_user_id=target_user_id,
            action="skip",
        )

        return {
            "ok": True,
            "action": "skip",
            "match": False,
        }

    if action_data.action == "report":
        report_user(
            reporter_id=current_user_id,
            reported_id=target_user_id,
            reason="Жалоба из Mini App",
        )

        return {
            "ok": True,
            "action": "report",
            "match": False,
        }

    if action_data.action == "block":
        block_user(
            blocker_id=current_user_id,
            blocked_id=target_user_id,
        )

        return {
            "ok": True,
            "action": "block",
            "match": False,
        }

    raise HTTPException(
        status_code=400,
        detail="Invalid action",
    )


@app.post("/api/profiles/undo-skip")
async def api_undo_last_skip(
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Возвращает последнюю случайно пропущенную анкету.

    Работает только для действия skip:
    - удаляет последний skip текущего пользователя;
    - возвращает эту анкету обратно в просмотр.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    current_user_id = int(telegram_user["id"])

    user_profile = get_profile(current_user_id)

    if not user_profile:
        raise HTTPException(
            status_code=400,
            detail="Create your profile first",
        )

    profile = undo_last_skip_action(current_user_id)

    if not profile:
        return {
            "ok": False,
            "message": "Нет предыдущей пропущенной анкеты",
            "profile": None,
        }

    return {
        "ok": True,
        "message": "Предыдущая анкета возвращена",
        "profile": profile_for_public_view(profile),
    }


@app.post("/api/profiles/unlike")
async def api_unlike_profile(
    unlike_data: UnlikeProfileIn,
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Убирает лайк текущего пользователя с другой анкеты.

    Если из-за этого был мэтч, он удаляется.
    Лайк второго пользователя не удаляем.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    current_user_id = int(telegram_user["id"])
    target_user_id = int(unlike_data.target_user_id)

    if current_user_id == target_user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot unlike yourself",
        )

    user_profile = get_profile(current_user_id)

    if not user_profile:
        raise HTTPException(
            status_code=400,
            detail="Create your profile first",
        )

    target_profile = get_profile(target_user_id)

    if not target_profile:
        raise HTTPException(
            status_code=404,
            detail="Target profile not found",
        )

    removed = remove_like_action(
        from_user_id=current_user_id,
        to_user_id=target_user_id,
    )

    if not removed:
        return {
            "ok": False,
            "message": "Лайк уже был убран или не найден",
        }

    return {
        "ok": True,
        "message": "Лайк убран",
    }


@app.get("/api/matches")
async def api_get_matches(
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Возвращает список мэтчей текущего пользователя для Mini App.
    """

    telegram_user = get_current_telegram_user(x_telegram_init_data)
    current_user_id = int(telegram_user["id"])

    user_profile = get_profile(current_user_id)

    if not user_profile:
        raise HTTPException(
            status_code=400,
            detail="Create your profile first",
        )

    matches = get_user_matches(current_user_id)

    return {
        "matches": [profile_with_photo_url(profile) for profile in matches],
    }


@app.get("/api/stats")
async def api_get_stats(
    x_telegram_init_data: str | None = Header(default=None),
):
    """
    Возвращает статистику проекта для демонстрации.
    """

    get_current_telegram_user(x_telegram_init_data)

    return get_project_stats()