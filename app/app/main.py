from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Request,
    UploadFile,
    File,
    WebSocket,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
import app.models as models
from app.database import SessionLocal, engine, get_db
from app.schemas import (
    User,
    UserCreate,
    Post,
    PostCreate,
    Comment,
    CommentCreate,
    Token,
)
from app.auth import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.config import settings
from app.file_handler import save_upload_file, is_valid_file_type
from app.websocket_manager import manager
from fastapi.exceptions import RequestValidationError

# ... rest of the file remains unchanged ...
