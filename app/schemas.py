from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    user_name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    password_hash: Optional[str] = None

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    content: str
    image_url: Optional[str] = None


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    author: User
    likes_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime
    author: User

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_name: Optional[str] = None
