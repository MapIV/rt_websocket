import asyncio
from asyncio.log import logger
import threading
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
        async def receive_messages():
            try:
                while True:
                    message = await websocket.receive_json()
                    logger.debug(f"Message received: {message}")

                    if message["type"] == "subscribe":
                        topic_name = message["topic"]
                        if topic_name not in active_topics:
                            if topic_name == "bson":
                                sender = BsonSender(topic_name)
                        active_topics[topic_name] = sender

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
                while True:
                    for topic_name, sender in active_topics.items():
                        data = sender.get_data()
                        if data != None:
                            logger.debug(f"Data send for topic: {topic_name}")
                            await manager.send_bytes(data, websocket)

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
            for sender in active_topics.values():
                sender.cleanup()
            manager.disconnect(websocket)