import time
from io import BytesIO

import cloudinary
import cloudinary.uploader

from app.config import (
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_CLOUD_NAME,
)


CLOUDINARY_PREFIX = "cloudinary:"
PROFILE_PHOTOS_FOLDER = "finvichik/profile_photos"


def is_cloudinary_configured() -> bool:
    """
    Проверяет, настроен ли Cloudinary.
    """

    return all(
        [
            CLOUDINARY_CLOUD_NAME,
            CLOUDINARY_API_KEY,
            CLOUDINARY_API_SECRET,
        ]
    )


def configure_cloudinary() -> None:
    """
    Настраивает Cloudinary SDK.
    """

    if not is_cloudinary_configured():
        raise RuntimeError(
            "Cloudinary не настроен. Проверь переменные CLOUDINARY_* "
            "в .env или в Environment Variables на хостинге."
        )

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


def is_cloudinary_photo_id(photo_file_id: str) -> bool:
    """
    Проверяет, что photo_file_id указывает на Cloudinary.
    """

    return photo_file_id.startswith(CLOUDINARY_PREFIX)


def make_cloudinary_photo_id(public_id: str) -> str:
    """
    Превращает Cloudinary public_id в значение для хранения в базе.
    """

    return f"{CLOUDINARY_PREFIX}{public_id}"


def public_id_from_photo_id(photo_file_id: str) -> str:
    """
    Извлекает Cloudinary public_id из значения базы.
    """

    return photo_file_id.replace(CLOUDINARY_PREFIX, "", 1).strip()


def upload_profile_photo(
    telegram_id: int,
    content: bytes,
    filename: str | None,
    content_type: str | None,
) -> tuple[str, str]:
    """
    Загружает фото профиля в Cloudinary.

    Возвращает:
    - photo_file_id для базы;
    - публичный URL для frontend.
    """

    if not content:
        raise ValueError("Photo is empty")

    configure_cloudinary()

    timestamp = int(time.time())
    public_id = f"{PROFILE_PHOTOS_FOLDER}/{telegram_id}/{timestamp}"

    file_obj = BytesIO(content)

    try:
        upload_result = cloudinary.uploader.upload(
            file_obj,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            invalidate=True,
            folder=None,
        )
    except Exception as error:
        raise RuntimeError(f"Не удалось загрузить фото в Cloudinary: {error}") from error

    secure_url = upload_result.get("secure_url")
    uploaded_public_id = upload_result.get("public_id")

    if not secure_url or not uploaded_public_id:
        raise RuntimeError("Cloudinary не вернул secure_url или public_id.")

    photo_file_id = make_cloudinary_photo_id(uploaded_public_id)

    return photo_file_id, secure_url


def public_url_for_photo_id(photo_file_id: str) -> str | None:
    """
    Возвращает публичный URL по photo_file_id.
    """

    if not is_cloudinary_photo_id(photo_file_id):
        return None

    public_id = public_id_from_photo_id(photo_file_id)

    if not public_id:
        return None

    configure_cloudinary()

    return cloudinary.CloudinaryImage(public_id).build_url(
        secure=True,
        resource_type="image",
    )


def delete_profile_photo(photo_file_id: str | None) -> None:
    """
    Удаляет фото из Cloudinary, если оно хранится там.

    Ошибки удаления не должны ломать удаление анкеты.
    """

    if not photo_file_id:
        return

    if not is_cloudinary_photo_id(photo_file_id):
        return

    public_id = public_id_from_photo_id(photo_file_id)

    if not public_id:
        return

    try:
        configure_cloudinary()
        cloudinary.uploader.destroy(
            public_id,
            resource_type="image",
            invalidate=True,
        )
    except Exception as error:
        print(f"Не удалось удалить фото из Cloudinary: {error}")


# Алиасы для совместимости с уже обновлёнными web.py и handlers/profile.py.
# Раньше мы готовили R2, поэтому в коде остались имена is_r2_photo_id/public_url_for_photo_id.
# Чтобы не переписывать все файлы прямо сейчас, оставляем совместимые функции.
def is_r2_photo_id(photo_file_id: str) -> bool:
    """
    Совместимость: теперь это проверка Cloudinary photo_id.
    """

    return is_cloudinary_photo_id(photo_file_id)