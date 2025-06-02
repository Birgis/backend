import os
import pytest
from fastapi import UploadFile
from app.file_handler import save_upload_file, get_file_extension, is_valid_file_type
from app.config import settings


@pytest.fixture
def test_upload_file():
    return UploadFile(filename="test.jpg", file=open("tests/test_files/test.jpg", "rb"))


@pytest.fixture
def test_upload_dir():
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield settings.upload_dir
    # Cleanup after tests
    for root, dirs, files in os.walk(settings.upload_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


@pytest.mark.asyncio
async def test_save_upload_file(test_upload_file, test_upload_dir):
    user_id = 1
    file_path = await save_upload_file(test_upload_file, user_id)
    assert os.path.exists(file_path)
    assert str(user_id) in file_path
    assert test_upload_file.filename in file_path


def test_get_file_extension():
    assert get_file_extension("test.jpg") == ".jpg"
    assert get_file_extension("test.PNG") == ".png"
    assert get_file_extension("test") == ""


def test_is_valid_file_type():
    assert is_valid_file_type("test.jpg")
    assert is_valid_file_type("test.png")
    assert is_valid_file_type("test.webp")
    assert is_valid_file_type("test.mp4")
    assert is_valid_file_type("test.webm")
    assert not is_valid_file_type("test.txt")
    assert not is_valid_file_type("test.pdf")
