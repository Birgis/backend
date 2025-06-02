import pytest
from fastapi import status


def test_create_user(client):
    response = client.post(
        "/users/",
        json={
            "user_name": "newuser",
            "email": "new@example.com",
            "password": "newpass123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_name"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "password" not in data


def test_create_user_duplicate_username(client, test_user):
    response = client.post(
        "/users/",
        json={
            "user_name": "testuser",
            "email": "different@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already taken" in response.json()["detail"]


def test_create_user_duplicate_email(client, test_user):
    response = client.post(
        "/users/",
        json={
            "user_name": "different",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post(
        "/token", data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/token", data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/token", data={"username": "nonexistent", "password": "testpass123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]


def test_get_current_user(authorized_client, test_user):
    response = authorized_client.get("/users/me/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_name"] == test_user.user_name
    assert data["email"] == test_user.email


def test_get_current_user_unauthorized(client):
    response = client.get("/users/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_access_token_without_expires():
    from app.auth import create_access_token

    token = create_access_token({"sub": "testuser"})
    assert token is not None


def test_get_current_user_invalid_token(authorized_client):
    response = authorized_client.get(
        "/users/me/", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_missing_sub(authorized_client):
    from app.auth import create_access_token

    # Create a token without 'sub' claim
    token = create_access_token({"other": "claim"})
    response = authorized_client.get(
        "/users/me/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_nonexistent_user(authorized_client):
    from app.auth import create_access_token

    # Create a token for a user that doesn't exist
    token = create_access_token({"sub": "nonexistent_user"})
    response = authorized_client.get(
        "/users/me/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
