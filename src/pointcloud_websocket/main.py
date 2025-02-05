import asyncio
from asyncio.log import logger
from fastapi import WebSocket, WebSocketDisconnect
from pointcloud_websocket.connection_manager import ConnectionManager
from pointcloud_websocket.services.bson_sender import BsonSender

#  fastAPIのinstanceを受け取る
async def read_root():
    return {"message": "Hello World!"}

def setup_manager():
    """
    managerを作成して返す
    """
    manager = ConnectionManager()
    return manager


async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager):
    await manager.connect(websocket)
    active_topics = {}  
    try:
        while True:
            message = await websocket.receive_json()
            logger.debug(f"Message received: {message}")

            if message["type"] == "subscribe":
                topic_name = message["topic"]
                if topic_name not in active_topics:
                    sender = BsonSender(topic_name, "src/sample_video/test_video1.mp4")
                    active_topics[topic_name] = sender

            elif message["type"] == "unsubscribe":
                topic_name = message["topic"]
                if topic_name in active_topics:
                    active_topics[topic_name].cleanup()
                    del active_topics[topic_name]

            elif message["type"] == "request_data":
                topic_name = message["topic"]
                if topic_name in active_topics:
                    sender = active_topics[topic_name]
                    data = sender.get_data()
                    if data:
                        await manager.send_bytes(data, websocket)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        for sender in active_topics.values():
            sender.cleanup()
        manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error: {str(e)}")