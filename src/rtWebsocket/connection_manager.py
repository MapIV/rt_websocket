from fastapi import WebSocket
from typing import List
import logging

from fastapi.websockets import WebSocketState

logger = logging.getLogger("ConnectionManager")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected.")

    async def send_bytes(self, message: bytes, websocket: WebSocket):
        await websocket.send_bytes(message)

    async def send_text(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_bytes(self, message: bytes):
        for connection in self.active_connections:
            try:
            # if connection.client_state == WebSocketState.CONNECTED:
                await connection.send_bytes(message)  
            except Exception as e:
                logger.error(f"Error sending bytes to {connection}: {e}")
                self.disconnect(connection)  