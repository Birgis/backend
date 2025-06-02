import os
import aiofiles
from fastapi import UploadFile
from app.config import settings
from datetime import datetime


async def save_upload_file(upload_file: UploadFile, user_id: int) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = os.path.join(settings.upload_dir, str(user_id), filename)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await upload_file.read()
        await out_file.write(content)

    return file_path


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_valid_file_type(filename: str) -> bool:
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm"}
    return get_file_extension(filename) in allowed_extensions
