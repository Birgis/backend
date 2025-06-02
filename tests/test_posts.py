import pytest
from fastapi import status
from sqlalchemy.orm import Session
from app.models import User
from app.auth import get_password_hash


def test_create_post(authorized_client):
    response = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "This is a test post"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "author_id" in data


def test_create_post_unauthorized(client):
    response = client.post("/posts/", json={"content": "This is a test post"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_posts(authorized_client):
    # Create a post first
    authorized_client.post("/posts/", json={"content": "This is a test post"})

    response = authorized_client.get("/posts/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "content" in data[0]
    assert "author_id" in data[0]


def test_get_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    response = authorized_client.get(f"/posts/{post['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == post["id"]
    assert data["content"] == "This is a test post"


def test_get_nonexistent_post(authorized_client):
    response = authorized_client.get("/posts/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_update_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    response = authorized_client.put(
        f"/posts/{post['id']}",
        json={"content": "This is an updated post"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "This is an updated post"


def test_update_nonexistent_post(authorized_client):
    response = authorized_client.put(
        "/posts/999", json={"content": "This is an updated post"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_update_post_unauthorized(authorized_client, other_authorized_client):
    # Create a post as the authorized user
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    # Try to update the post as the other user
    response = other_authorized_client.put(
        f"/posts/{post['id']}", json={"content": "This is an updated post"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authorized to update this post"


def test_delete_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    response = authorized_client.delete(f"/posts/{post['id']}")
    assert response.status_code == status.HTTP_200_OK

    # Verify post is deleted
    response = authorized_client.get(f"/posts/{post['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_nonexistent_post(authorized_client):
    response = authorized_client.delete("/posts/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_delete_post_unauthorized(authorized_client, other_authorized_client):
    # Create a post as the authorized user
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    # Try to delete the post as the other user
    response = other_authorized_client.delete(f"/posts/{post['id']}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authorized to delete this post"
