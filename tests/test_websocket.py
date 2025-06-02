import pytest
from fastapi import WebSocket
from app.websocket_manager import ConnectionManager
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_websocket():
    websocket = AsyncMock(spec=WebSocket)
    return websocket


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.mark.asyncio
async def test_connect(connection_manager, mock_websocket):
    user_id = 1
    await connection_manager.connect(mock_websocket, user_id)
    assert user_id in connection_manager.active_connections
    assert mock_websocket in connection_manager.active_connections[user_id]
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect(connection_manager, mock_websocket):
    user_id = 1
    await connection_manager.connect(mock_websocket, user_id)
    await connection_manager.disconnect(mock_websocket, user_id)
    assert user_id not in connection_manager.active_connections


@pytest.mark.asyncio
async def test_send_personal_message(connection_manager, mock_websocket):
    user_id = 1
    message = "Test message"
    await connection_manager.connect(mock_websocket, user_id)
    await connection_manager.send_personal_message(message, user_id)
    mock_websocket.send_text.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast(connection_manager):
    user1_websocket = AsyncMock(spec=WebSocket)
    user2_websocket = AsyncMock(spec=WebSocket)
    message = "Broadcast message"

    await connection_manager.connect(user1_websocket, 1)
    await connection_manager.connect(user2_websocket, 2)

    await connection_manager.broadcast(message)

    user1_websocket.send_text.assert_called_once_with(message)
    user2_websocket.send_text.assert_called_once_with(message)
