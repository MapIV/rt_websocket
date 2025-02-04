import pytest
from fastapi import WebSocket
from ..src.pointcloud_websocket.connection_manager import ConnectionManager

@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect():
    manager = ConnectionManager()
    websocket = WebSocket(None, None)

    await manager.connect(websocket)
    assert len(manager.active_connections) == 1

    manager.disconnect(websocket)
    assert len(manager.active_connections) == 0