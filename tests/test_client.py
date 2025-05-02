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
            print("接続しました")
            while True:
                message = await websocket.recv()
                await self.handle_message(websocket, message)

    async def handle_message(self, websocket, message):
        try:
            msg = json.loads(message)
            if msg["type"] == "request_data":
                await self.send_frame(websocket)
        except:
            pass

    async def send_frame(self, websocket):
        ret, frame = self.cap.read()
        if not ret:
            return
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            return

        image_bytes = buffer.tobytes()
        header = {
            "format": "jpeg",
            "send_timestamp": int(time.time() * 1000)
        }
        header_json = json.dumps(header).encode("utf-8")
        header_len = struct.pack("<I", len(header_json))
        payload = header_len + header_json + image_bytes

        await websocket.send(payload)

# async def send_camera_frames():
#     uri = "ws://localhost:8888/ws/webcamera/sender"
#     cap = cv2.VideoCapture(0)  # 0番のカメラを使用
#     if not cap.isOpened():
#         print("カメラが開けませんでした")
#         return

#     async with websockets.connect(uri) as websocket:
#         print("接続しました")
#         try:
#             while True:
#                 ret, frame = cap.read()
#                 if not ret:
#                     print("フレーム取得失敗")
#                     break

#                 # JPEGでエンコード
#                 ret, buffer = cv2.imencode(".jpg", frame)
#                 if not ret:
#                     print("エンコード失敗")
#                     continue

#                 image_bytes = buffer.tobytes()

#                 header = {
#                     "format": "jpeg",
#                     "send_timestamp": int(time.time() * 1000)
#                 }
#                 header_json = json.dumps(header).encode("utf-8")
#                 header_len = struct.pack("<I", len(header_json))  # 4バイトLittle Endian

#                 payload = header_len + header_json + image_bytes
#                 await websocket.send(payload)

#                 await asyncio.sleep(0.2)  # 200msごとに送信
#         finally:
#             cap.release()

if __name__ == "__main__":
    uri = "ws://localhost:8888/ws/webcamera/sender"
    client = WebCameraClient(uri)
    asyncio.run(client.connect())
