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
    # receiver = MessageReceiver(websocket)
    
    active_topics = {}  
    last_request_time = {"time": time.time()} 
    
    if is_sender:
        #タイムアウトチェックのタスクを開始
        timeout_task = asyncio.create_task(_check_timeout(websocket, last_request_time, manager, active_topics))

    try:
        while (websocket.client_state == WebSocketState.CONNECTED):
            try:
                message = await websocket.receive()
                # message = await receiver.get_latest()
                if message is None:
                    await asyncio.sleep(0.01)
                    continue

                if "text" in message:
                    message = json.loads(message["text"])

                    if message["type"] == "request_data":
                        if is_sender:
                            last_request_time["time"] = time.time()
                        # print(f"message: {message}")
                        # 他のclientにrequest_dataを転送
                        await manager.broadcast(json.dumps(message), exclude=[websocket])

                    elif message["type"] == "send_data":
                        data = message["data"]

                        await manager.broadcast(json.dumps(message) , exclude=[websocket])


                elif "bytes" in message:
                    if is_sender:
                        last_request_time["time"] = time.time()
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
                        await manager.broadcast_bytes(new_data , exclude=[websocket])

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
        manager.disconnect(websocket)
        print("Receiver closed")
                
    finally:
        logger.info("Cleaning up...")
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
