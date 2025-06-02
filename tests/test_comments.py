import pytest
from fastapi import status
from sqlalchemy.orm import Session
from app.models import User
from app.auth import get_password_hash


def test_create_comment(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"content": "This is a test post"}
    ).json()

    response = authorized_client.post(
        f"/posts/{post['id']}/comments/", json={"content": "This is a test comment"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "This is a test comment"
    assert data["post_id"] == post["id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "author_id" in data


def test_create_comment_unauthorized(client):
    response = client.post(
        "/posts/1/comments/", json={"content": "This is a test comment"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_comment_nonexistent_post(authorized_client):
    response = authorized_client.post(
        "/posts/999/comments/", json={"content": "This is a test comment"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_get_comments(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"title": "Test Post", "content": "This is a test post"}
    ).json()

    # Create a comment
    authorized_client.post(
        f"/posts/{post['id']}/comments/", json={"content": "This is a test comment"}
    )

    response = authorized_client.get(f"/posts/{post['id']}/comments/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["content"] == "This is a test comment"
    assert data[0]["post_id"] == post["id"]


def test_get_comments_nonexistent_post(authorized_client):
    response = authorized_client.get("/posts/999/comments/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Post not found"


def test_update_comment(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"title": "Test Post", "content": "This is a test post"}
    ).json()

    # Create a comment
    comment = authorized_client.post(
        f"/posts/{post['id']}/comments/", json={"content": "This is a test comment"}
    ).json()

    response = authorized_client.put(
        f"/comments/{comment['id']}", json={"content": "This is an updated comment"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "This is an updated comment"


def test_update_nonexistent_comment(authorized_client):
    response = authorized_client.put(
        "/comments/999", json={"content": "This is an updated comment"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Comment not found"


def test_delete_comment(authorized_client):
    # Create a post first
    post = authorized_client.post(
        "/posts/", json={"title": "Test Post", "content": "This is a test post"}
    ).json()

    # Create a comment
    comment = authorized_client.post(
        f"/posts/{post['id']}/comments/", json={"content": "This is a test comment"}
    ).json()

    response = authorized_client.delete(f"/comments/{comment['id']}")
    assert response.status_code == status.HTTP_200_OK

    # Verify comment is deleted
    response = authorized_client.get(f"/posts/{post['id']}/comments/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_delete_nonexistent_comment(authorized_client):
    response = authorized_client.delete("/comments/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Comment not found"


def test_update_comment_unauthorized(
    authorized_client, other_authorized_client, test_post
):
    # Create a comment as the authorized user
    comment = authorized_client.post(
        f"/posts/{test_post.id}/comments/", json={"content": "This is a test comment"}
    ).json()

    # Try to update the comment as the other user
    response = other_authorized_client.put(
        f"/comments/{comment['id']}", json={"content": "This is an updated comment"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authorized to update this comment"


def test_delete_comment_unauthorized(
    authorized_client, other_authorized_client, test_post
):
    # Create a comment as the authorized user
    comment = authorized_client.post(
        f"/posts/{test_post.id}/comments/", json={"content": "This is a test comment"}
    ).json()

    # Try to delete the comment as the other user
    response = other_authorized_client.delete(f"/comments/{comment['id']}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authorized to delete this comment"
