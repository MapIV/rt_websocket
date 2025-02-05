import asyncio
from asyncio.log import logger
import os
from fastapi import WebSocket, WebSocketDisconnect
from pointcloud_websocket.connection_manager import ConnectionManager
from pointcloud_websocket.services.video_sender import VideoSender

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
            print(f'message: {message}')

            if message["type"] == "subscribe":
                topic_name = message["topic"]
                print(f'topic_name: {topic_name}')
                if topic_name not in active_topics:
                    video_path = os.path.abspath("../src/sample_video/test_video1.mp4")
                    print(f'video_path: {video_path}')
                    sender = VideoSender(topic_name, video_path)
                    active_topics[topic_name] = sender
                    print(f"Subscribed to {topic_name}")
                print(f'active_topics: {active_topics}')

            elif message["type"] == "unsubscribe":
                topic_name = message["topic"]
                if topic_name in active_topics:
                    active_topics[topic_name].cleanup()
                    del active_topics[topic_name]

            elif message["type"] == "request_data":
                topic_name = message["topic"]
                print(f'topic_name: {topic_name}')
                if topic_name in active_topics:
                    print(f"topic name in active_topics")
                    sender = active_topics[topic_name]
                    print(f"sender: {sender}")
                    data = sender.get_data()
                    print(f"data: {type(data)}")
                    if data:
                        await manager.send_bytes(data, websocket)
                    print(f"Sent data to {topic_name}")

            print(f' finish message: {message}')

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        for sender in active_topics.values():
            sender.cleanup()
        manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")