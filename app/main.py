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
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

# Add CORS middleware - keeping it permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_platform_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Platform-Support"] = ",".join(settings.supported_platforms)
    return response


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.user_name == form_data.username)
        .first()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = (
        db.query(models.User).filter(models.User.user_name == user.user_name).first()
    )
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        user_name=user.user_name, email=user.email, password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/me/", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/posts/", response_model=Post)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_post = models.Post(**post.dict(), author_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/", response_model=List[Post])
def read_posts(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    posts = db.query(models.Post).offset(skip).limit(limit).all()
    return posts


@app.get("/posts/{post_id}", response_model=Post)
def read_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
    else:
        post.liked_by.append(current_user)
    db.commit()
    return {"message": "Like toggled successfully"}


@app.post("/posts/{post_id}/comments/", response_model=Comment)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_comment = models.Comment(
        **comment.dict(), author_id=current_user.id, post_id=post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@app.get("/posts/{post_id}/comments/", response_model=List[Comment])
def read_comments(
    post_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return comments


@app.get("/posts/{post_id}/likes")
def get_likes(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return [{"post_id": post_id, "user_id": user.id} for user in post.liked_by]


@app.put("/comments/{comment_id}", response_model=Comment)
def update_comment(
    comment_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_comment = (
        db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    )
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this comment"
        )

    for key, value in comment.dict().items():
        setattr(db_comment, key, value)

    db.commit()
    db.refresh(db_comment)
    return db_comment


@app.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_comment = (
        db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    )
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this comment"
        )

    db.delete(db_comment)
    db.commit()
    return {"message": "Comment deleted successfully"}


@app.put("/posts/{post_id}", response_model=Post)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this post"
        )

    for key, value in post.dict().items():
        setattr(db_post, key, value)

    db.commit()
    db.refresh(db_post)
    return db_post


@app.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this post"
        )

    db.delete(db_post)
    db.commit()
    return {"message": "Post deleted successfully"}


# New endpoints for platform capabilities and file upload
@app.get("/api/platform/capabilities")
async def get_platform_capabilities():
    return {
        "features": {
            "file_upload": True,
            "camera": True,
            "location": True,
            "notifications": True,
        },
        "max_upload_size": settings.max_upload_size,
        "supported_image_formats": ["jpg", "png", "webp"],
        "supported_video_formats": ["mp4", "webm"],
    }


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    if not is_valid_file_type(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported types: jpg, png, gif, webp, mp4, webm",
        )

    file_path = await save_upload_file(file, current_user.id)
    return {"filename": file.filename, "location": file_path}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str, db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(token, db)
        await manager.connect(websocket, user.id)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(f"Message from {user.user_name}: {data}")
        except:
            await manager.disconnect(websocket, user.id)
    except:
        await websocket.close()


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "platform": request.headers.get("X-Platform", "unknown"),
            "error_type": "validation_error",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
