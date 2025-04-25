import asyncio
from asyncio.log import logger
import json
import os
import time
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from rtWebsocket.connection_manager import ConnectionManager
from rtWebsocket.services.bson_sender import BsonSender
from rtWebsocket.services.flatten_sender import FlattenSender
from rtWebsocket.services.text_sender import TextSender
from rtWebsocket.services.video_v9_sender import VideoV9Sender
from rtWebsocket.services.video_sender import VideoSender

TIMEOUT_SECONDS = 10  # 5秒以上リクエストが来なかったら切断

class MessageReceiver:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.latest_message = None
        self.lock = asyncio.Lock()
        self.running = True
        self.receive_task = asyncio.create_task(self._receiver())

    async def _receiver(self):
        try:
            while self.running:
                if self.websocket.client_state != WebSocketState.CONNECTED:
                    print("WebSocket disconnected in _received")
                    break
                try:
                    message = await self.websocket.receive()
                    async with self.lock:
                        self.latest_message = message
                except asyncio.CancelledError:
                    print("Receiver got CancelledError")
                    self.running = False
                    raise

                except RuntimeError as e:
                    print(f"RuntimeError in receiver: {e}")
                    self.running = False
                    break
        except asyncio.CancelledError:
                print("Receiver got CancelledError")
                raise
        except Exception as e:
            print(f"Receiver error: {e}")
        finally:
            print(">>> finally called <<<")
            self.running = False

    async def get_latest(self):
        async with self.lock:
            msg = self.latest_message
            self.latest_message = None
            return msg

    async def close(self):
        print("Starting receiver close procedure")
        self.running = False
        
        if not self.receive_task.done():
            print("Cancelling receive task")
            self.receive_task.cancel()
            
            try:
                print("Awaiting cancelled task")
                await asyncio.wait_for(self.receive_task, timeout=1.0)
                print("Task await completed")
            except asyncio.TimeoutError:
                print("Timeout waiting for task to cancel")
            except asyncio.CancelledError:
                print("Receiver task was cancelled as expected")
            except Exception as e:
                print(f"Error awaiting cancelled task: {e}")
        else:
            print("Receive task was already done")
            
        print("Receiver closed")
        print("Receiver perfectly closed")

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
        try:
            await asyncio.sleep(1)  # 1秒ごとにチェック
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            print (f"os.getloadavg(): {os.getloadavg()}")
            print(f"time: {time.time()}")
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
        except RuntimeError as e:
            print(f"WebSocket already closed or in closing state: {e}")
        
async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager,is_sender: bool = False):
    await manager.connect(websocket)
    receiver = MessageReceiver(websocket)
    
    active_topics = {}  
    last_request_time = {"time": time.time()} 
    
    if is_sender:
        # タイムアウトチェックのタスクを開始
        timeout_task = asyncio.create_task(_check_timeout(websocket, last_request_time, manager, active_topics))

    try:
        while (websocket.client_state == WebSocketState.CONNECTED):
            try:
                # message = await websocket.receive()
                message = await receiver.get_latest()
                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                if "text" in message:
                    message = json.loads(message["text"])
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

                            if topic_name == "video_v9_stream":
                                video_path = os.path.abspath(path)
                                print(f'video_path: {video_path}')
                                sender = VideoV9Sender(topic_name, video_path)

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
                        if is_sender:
                            last_request_time["time"] = time.time()

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

                    elif message["type"] == "send_data":
                        topic = message["topic"]
                        data_type = message["data_type"]
                        data = message["data"]

                        await manager.broadcast(topic, data)


                elif "bytes" in message:
                    if is_sender:
                        last_request_time["time"] = time.time()
                        print(f"received  time: {last_request_time['time']}")
                    # print(f"Received raw bytes of size: {len(message['bytes'])}")
                    # await manager.broadcast_bytes(message["bytes"])
                    # asyncio.create_task(manager.broadcast_bytes(message["bytes"])) #並行処理？
                    data = message["bytes"]
                    try:
                        header_len = int.from_bytes(data[:4], byteorder='little')
                        header_bytes = data[4:4+header_len]
                        body = data[4+header_len:]

                        header = json.loads(header_bytes.decode("utf-8"))
                        header["receive_timestamp"] = int(time.time() * 1000)

                        new_header_bytes = json.dumps(header).encode("utf-8")
                        new_header_len = len(new_header_bytes).to_bytes(4, byteorder='little')

                        new_data = new_header_len + new_header_bytes + body
                        # print("websocket manager:", manager.active_connections)
                        # print("is_sender: ", is_sender) 
                        await manager.broadcast_bytes(new_data)

                    except Exception as e:
                        print("Failed to parse or broadcast video message:", e)

            except Exception as inner_e:
                print(f"Unexpected error inside loop: {inner_e}")
                break
    
    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        if is_sender:
            timeout_task.cancel()

        print("WebSocket disconnected")
        print("Running cleanup...")
        await receiver.close()
        manager.disconnect(websocket)
        print("Receiver closed")
                
    finally:
        logger.info("Cleaning up...")
        await receiver.close()
        logger.info("Cleaning receiver")
        if is_sender:
            timeout_task.cancel()
            try:
                await timeout_task
            except asyncio.CancelledError:
                print("Timeout task was cancelled")
        for paths in active_topics.values():
            for sender in paths.values():
                sender.cleanup()
        manager.disconnect(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
