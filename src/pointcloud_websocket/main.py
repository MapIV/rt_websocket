import asyncio
from asyncio.log import logger
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.pointcloud_websocket.connection_manager import ConnectionManager
from src.pointcloud_websocket.middleware.timeout import TimeoutMiddleware
from src.pointcloud_websocket.services.ros_client import RosClient
from src.pointcloud_websocket.services.ros_client_trajectory import RosClientTrajectory
from src.pointcloud_websocket.services.ros_client_xyz import RosClientXYZ

#  fastAPIのinstanceを受け取る
async def read_root():
    return {"message": "Hello World!"}

def setup_websocket():
    """
    WebSocket エンドポイントを FastAPI に追加

    Args:
        app (FastAPI): FastAPI インスタンス
        path (str): WebSocket のエンドポイント
    """
    manager = ConnectionManager()
    return manager


async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager):
        await manager.connect(websocket)
        active_topics = {}  
        async def receive_messages():
            try:
                while True:
                    message = await websocket.receive_json()
                    logger.debug(f"Message received: {message}")

                    if message["type"] == "subscribe":
                        topic_name = message["topic"]

                        if topic_name not in active_topics:
                            if topic_name == '/scan/downsampled' or topic_name == '/map/3d/diff' or topic_name == '/map/3d/full':
                                ros_client = RosClientXYZ(topic_name)
                            elif topic_name == '/trajectory/diff':
                                ros_client = RosClientTrajectory(topic_name)
                            else:
                                ros_client = RosClient(topic_name)

                            thread = threading.Thread(target=ros_client.connect_subscription)
                            thread.daemon = True
                            thread.start()
                            active_topics[topic_name] = ros_client

                    elif message["type"] == "unsubscribe":
                        topic_name = message["topic"]
                        if topic_name in active_topics:
                            active_topics[topic_name].cleanup()
                            del active_topics[topic_name]

            except WebSocketDisconnect:
                    logger.info(f"Client disconnected during message receiving")
                    return  # 正常に終了
            except Exception as e:
                logger.error(f"Error in receive_messages: {str(e)}")
                return

        async def send_data():
            try:
                topics_to_remove = []
                while True:
                    for topic_name, ros_client in active_topics.items():
                        data = ros_client.get_data()
                        if data != None:
                            logger.debug(f"Data send for topic: {topic_name}")
                            await manager.send_bytes(data, websocket)

                            #  map/3d/full は一度データを送信したらクリアする
                            if topic_name == '/map/3d/full':
                                topics_to_remove.append(topic_name)

                    # マークされたトピックを削除
                    for topic_name in topics_to_remove:
                        if topic_name in active_topics:
                            active_topics[topic_name].cleanup()
                            del active_topics[topic_name]
                            topics_to_remove = []

                    await asyncio.sleep(0.01)

            except WebSocketDisconnect:
                    logger.info(f"Client disconnected during data sending")
                    return  # 正常に終了
            except Exception as e:
                logger.error(f"Error in send_data: {str(e)}")
                return

        try:
            # メッセージ受信と送信を並行して実行
            receive_task = asyncio.create_task(receive_messages())
            send_task = asyncio.create_task(send_data())

            # どちらかのタスクが完了するまで待機
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 残りのタスクをキャンセル
            for task in pending:
                task.cancel()

        except WebSocketDisconnect:
            # 切断時の処理
            for ros_client in active_topics.values():
                ros_client.cleanup()
            manager.disconnect(websocket)