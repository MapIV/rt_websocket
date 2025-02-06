import asyncio
from asyncio.log import logger
import os
import time
from fastapi import WebSocket, WebSocketDisconnect
from rtWebsocket.connection_manager import ConnectionManager
from rtWebsocket.services.video_sender import VideoSender

TIMEOUT_SECONDS = 5  # 5秒以上リクエストが来なかったら切断

#  fastAPIのinstanceを受け取る
async def read_root():
    return {"message": "Hello World!"}

def setup_manager():
    """
    managerを作成して返す
    """
    manager = ConnectionManager()
    return manager

async def check_timeout(websocket: WebSocket, last_request_time: dict, manager: ConnectionManager, active_topics: dict):
    """ 
    一定時間リクエストが来なかったら WebSocket を閉じる
    """
    while True:
        await asyncio.sleep(1)  # 1秒ごとにチェック
        if time.time() - last_request_time['time'] > TIMEOUT_SECONDS:
            print(f"last_request_time: {last_request_time}")
            print(f"Timeout: No request_data for {TIMEOUT_SECONDS}s. Closing WebSocket.")
            logger.info("Client disconnected")
            for sender in active_topics.values():
                sender.cleanup()
            manager.disconnect(websocket)
            await websocket.close()
            break
        
async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager):
    await manager.connect(websocket)
    active_topics = {}  
    last_request_time = {"time": time.time()} 

    # タイムアウトチェックのタスクを開始
    asyncio.create_task(check_timeout(websocket, last_request_time, manager, active_topics))

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
                last_request_time["time"] = time.time()
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