import asyncio
from asyncio.log import logger
import os
import time
from fastapi import WebSocket, WebSocketDisconnect
from rtWebsocket.connection_manager import ConnectionManager
from rtWebsocket.services.bson_sender import BsonSender
from rtWebsocket.services.flatten_sender import FlattenSender
from rtWebsocket.services.text_sender import TextSender
from rtWebsocket.services.video_h264_sender import Videoh264Sender
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

async def _check_timeout(websocket: WebSocket, last_request_time: dict, manager: ConnectionManager, active_topics: dict):
    """ 
    一定時間リクエストが来なかったら WebSocket を閉じる
    """
    while True:
        await asyncio.sleep(1)  # 1秒ごとにチェック
        print (f"os.getloadavg(): {os.getloadavg()}")
        if time.time() - last_request_time['time'] > TIMEOUT_SECONDS:
            print(f"last_request_time: {last_request_time}")
            print(f"Timeout: No request_data for {TIMEOUT_SECONDS}s. Closing WebSocket.")
            logger.info("Client disconnected")
            for paths in active_topics.values():
                for sender in paths.values():
                        sender.cleanup()
            manager.disconnect(websocket)
            await websocket.close()
            break
        
async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager):
    await manager.connect(websocket)
    active_topics = {}  
    last_request_time = {"time": time.time()} 

    # タイムアウトチェックのタスクを開始
    asyncio.create_task(_check_timeout(websocket, last_request_time, manager, active_topics))

    try:
        while True:
            message = await websocket.receive_json()
            print(f'message: {message}')

            if message["type"] == "subscribe":
                topic_name = message["topic"]
                print(f'topic_name: {topic_name}')
                path = message["path"]  
                print(f"topic name not in active_topics: {topic_name not in active_topics}")

                if topic_name not in active_topics:
                    active_topics[topic_name] = {}
                    if topic_name == "video_stream":
                        # for testing, we are using a sample video
                        video_path = os.path.abspath(path)
                        print(f'video_path: {video_path}')
                        sender = VideoSender(topic_name, video_path)

                    if topic_name == "pcdfile":
                        # for testing, we are using a sample pcd file
                        pcd_path = os.path.abspath(path)
                        print(f'pcd_path: {pcd_path}')
                        # sender = BsonSender(topic_name, pcd_path)
                        sender = FlattenSender(topic_name, pcd_path)

                    if topic_name == "video_h264_stream":
                        video_path = os.path.abspath(path)
                        print(f'video_path: {video_path}')
                        sender = Videoh264Sender(topic_name, video_path)

                    if topic_name == "text":
                         sender = TextSender(topic_name)    

                    active_topics[topic_name][path] = sender
                    print(f"Subscribed to {topic_name}")

                print(f'active_topics: {active_topics}')

            elif message["type"] == "unsubscribe":
                topic_name = message["topic"]

                if topic_name in active_topics:
                    active_topics[topic_name][path].cleanup()
                    del active_topics[topic_name][path]

            elif message["type"] == "request_data":
                topic_name = message["topic"]
                last_request_time["time"] = time.time()
                print(f'topic_name: {topic_name}')

                if topic_name in active_topics:
                    sender = active_topics[topic_name][path]
                    print('sender: ', sender)
                    data = sender.get_data()
                    print(f"data: {type(data)}")
                    if data:
                        if topic_name == "text":
                            await manager.send_text(data, websocket)
                        else:
                            await manager.send_bytes(data, websocket)
                        print(f"Sent data to {topic_name}")

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        for paths in active_topics.values():
                for sender in paths.values():
                        sender.cleanup()
        manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")