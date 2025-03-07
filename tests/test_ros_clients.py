import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8080/ws"  # WebSocketサーバーのアドレス
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server.")

        # サブスクライブメッセージを送信 (video)
        subscribe_message = json.dumps({
            "type": "subscribe",
            "topic": "video_stream",
            "path" : "../src/sample_video/test_video1.mp4",
        })

        # サブスクライブメッセージを送信 (pcd)
        # subscribe_message = json.dumps({
        #     "type": "subscribe",
        #     "topic": "pcdfile",
        #     "path" : "../src/sample_pcdfile/map-18400_-93500_converted_converted.pcd",
        # })
        await websocket.send(subscribe_message)
        print(f"Sent: {subscribe_message}")

        try:
            while True:
                # メッセージを受信
                data = await websocket.recv()
                print(f"Received: {data}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(websocket_client())