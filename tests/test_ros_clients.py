import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8080/ws"  # WebSocketサーバーのアドレス
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server.")

        # サブスクライブメッセージを送信
        subscribe_message = json.dumps({
            "type": "subscribe",
            "topic": "/scan/downsampled"
        })
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