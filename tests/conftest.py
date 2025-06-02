import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User, Post, Comment
from app.auth import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    user = User(
        user_name="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_token(client, test_user):
    response = client.post(
        "/token", data={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def authorized_client(client, test_user_token):
    client.headers = {**client.headers, "Authorization": f"Bearer {test_user_token}"}
    return client


@pytest.fixture(scope="function")
def test_post(db, test_user):
    post = Post(content="Test post content", author_id=test_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@pytest.fixture(scope="function")
def other_authorized_client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        # Create another user
        other_user = User(
            user_name="otheruser",
            email="other@example.com",
            password_hash=get_password_hash("testpass123"),
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Get token for the other user
        response = test_client.post(
            "/token", data={"username": "otheruser", "password": "testpass123"}
        )
        other_token = response.json()["access_token"]

        # Set the token in the headers
        test_client.headers = {
            **test_client.headers,
            "Authorization": f"Bearer {other_token}",
        }
        yield test_client
    app.dependency_overrides.clear()
