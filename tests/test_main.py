import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi import UploadFile
from app.main import app
from unittest.mock import AsyncMock, patch, MagicMock
import json
from starlette.websockets import WebSocketDisconnect


def test_platform_capabilities(client):
    response = client.get("/api/platform/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "max_upload_size" in data
    assert "supported_image_formats" in data
    assert "supported_video_formats" in data


def test_upload_file(authorized_client):
    with patch("app.main.save_upload_file", new_callable=AsyncMock) as mock_save:
        mock_save.return_value = "uploads/1/test.jpg"
        response = authorized_client.post(
            "/api/upload", files={"file": ("test.jpg", b"test content")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "location" in data


def test_upload_invalid_file(authorized_client):
    response = authorized_client.post(
        "/api/upload", files={"file": ("test.txt", b"test content")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_websocket_endpoint(authorized_client, test_user_token):
    mock_websocket = AsyncMock()
    mock_user = MagicMock(id=1, user_name="testuser")

    # Simulate one message, then disconnect
    mock_websocket.receive_text = AsyncMock(
        side_effect=["test message", WebSocketDisconnect()]
    )

    with patch("app.main.get_current_user", return_value=mock_user):
        with patch("app.main.manager.connect", new_callable=AsyncMock) as mock_connect:
            with patch(
                "app.main.manager.disconnect", new_callable=AsyncMock
            ) as mock_disconnect:
                with patch(
                    "app.main.manager.broadcast", new_callable=AsyncMock
                ) as mock_broadcast:
                    websocket_route = next(
                        route for route in app.routes if route.path == "/ws"
                    )
                    await websocket_route.endpoint(
                        mock_websocket, test_user_token, None
                    )
                    mock_connect.assert_called_once_with(mock_websocket, mock_user.id)
                    mock_broadcast.assert_called_once()
                    mock_disconnect.assert_called_once_with(
                        mock_websocket, mock_user.id
                    )


@pytest.mark.asyncio
async def test_websocket_endpoint_error_path(authorized_client, test_user_token):
    mock_websocket = AsyncMock()
    mock_user = MagicMock(id=1, user_name="testuser")
    # Simulate an exception before connection is established
    with patch("app.main.get_current_user", side_effect=Exception("auth fail")):
        with patch("app.main.manager.connect", new_callable=AsyncMock) as mock_connect:
            with patch(
                "app.main.manager.disconnect", new_callable=AsyncMock
            ) as mock_disconnect:
                with patch(
                    "app.main.manager.broadcast", new_callable=AsyncMock
                ) as mock_broadcast:
                    websocket_route = next(
                        route for route in app.routes if route.path == "/ws"
                    )
                    await websocket_route.endpoint(
                        mock_websocket, test_user_token, None
                    )
                    mock_websocket.close.assert_awaited()


def test_validation_error_handler(authorized_client):
    # Create a mock validation error
    mock_error = MagicMock()
    mock_error.errors = lambda: [{"loc": ["body", "field"], "msg": "field required"}]

    with patch("app.main.RequestValidationError", return_value=mock_error):
        response = authorized_client.post("/posts/", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "platform" in data
        assert "error_type" in data
