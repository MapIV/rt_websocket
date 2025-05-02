import asyncio
import websockets
import cv2
import json
import time
import struct

class WebCameraClient:
    def __init__(self, uri):
        self.uri = uri
        self.cap = cv2.VideoCapture(0)  # 0番のカメラを使用
        if not self.cap.isOpened():
            print("カメラが開けませんでした")
            return

    async def connect(self):
        async with websockets.connect(self.uri) as websocket:
            await self.send_frame(websocket)
            print("接続しました")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15)
                    await self.handle_message(websocket, message)
                except Exception as e:
                    print("Error:", e)  
                    break
                except KeyboardInterrupt:
                    print("KeyboardInterrupt")
                    break
                except websockets.ConnectionClosed:
                    print("Connection closed")
                    break

    async def handle_message(self, websocket, message):
        msg = json.loads(message)
        if msg["type"] == "request_data":
            print("get request_data")
            await self.send_frame(websocket)

    async def send_frame(self, websocket):
        # ret, frame = self.cap.read()
        # if not ret:
        #     return
        # ret, buffer = cv2.imencode(".jpg", frame)
        # if not ret:
        #     return

        # image_bytes = buffer.tobytes()
        # header = {
        #     "format": "jpeg",
        #     "send_timestamp": int(time.time() * 1000)
        # }
        # header_json = json.dumps(header).encode("utf-8")
        # header_len = struct.pack("<I", len(header_json))
        # payload = header_len + header_json + image_bytes

        # await websocket.send(payload)
        message = {
            "type": "text_send_test",
            "data": {
                "format": "jpeg",
                "send_timestamp": int(time.time() * 1000)
            }
        }
        await websocket.send(json.dumps(message))   

if __name__ == "__main__":
    uri = "ws://localhost:8888/ws/webcamera/sender"
    client = WebCameraClient(uri)
    asyncio.run(client.connect())
