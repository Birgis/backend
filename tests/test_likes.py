import pytest
from fastapi import status


def test_like_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"title": "Test Post", "content": "This is a test post"}
    ).json()

    response = authorized_client.post(f"/posts/{post['id']}/like")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Like toggled successfully"


def test_like_post_unauthorized(client):
    response = client.post("/posts/1/like")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_like_nonexistent_post(authorized_client):
    response = authorized_client.post("/posts/999/like")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_unlike_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    # Like the post
    authorized_client.post(f"/posts/{post['id']}/like")

    # Unlike the post
    response = authorized_client.post(f"/posts/{post['id']}/like")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Like toggled successfully"

    # Verify like is removed
    response = authorized_client.get(f"/posts/{post['id']}/likes")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_unlike_post_unauthorized(client):
    response = client.post("/posts/1/like")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_likes(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    # Like the post
    authorized_client.post(f"/posts/{post['id']}/like")

    response = authorized_client.get(f"/posts/{post['id']}/likes")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["post_id"] == post["id"]


def test_get_likes_nonexistent_post(authorized_client):
    response = authorized_client.get("/posts/999/likes")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_double_like_post(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    # Like the post
    response = authorized_client.post(f"/posts/{post['id']}/like")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Like toggled successfully"

    # Like again (should unlike)
    response = authorized_client.post(f"/posts/{post['id']}/like")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Like toggled successfully"

    # Verify like is removed
    response = authorized_client.get(f"/posts/{post['id']}/likes")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0
