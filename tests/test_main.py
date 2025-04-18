import os
from fastapi.responses import StreamingResponse
from rtWebsocket.middleware.timeout import TimeoutMiddleware
from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import rtWebsocket
# from aiortc import VideoStreamTrack, RTCPeerConnection, RTCSessionDescription
# from aiortc.contrib.media import MediaPlayer, MediaRecorder
app = FastAPI()

# CORS 設定（必要に応じて）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimeoutMiddleware, timeout=10)
ws_manager = rtWebsocket.setup_manager()
camera_manager = rtWebsocket.setup_manager()

async def video_streamer(file_path: str, chunk_size: int = 1024 * 1024):
    """動画をチャンクごとにストリーミングする"""
    with open(file_path, "rb") as video_file:
        # yield from video_file
        while chunk := video_file.read(chunk_size):
            yield chunk

@app.get("/")
async def read_root():
    return {"message": "Hello World!"}

@app.websocket("/ws")
async def test_websocket(websocket: WebSocket):
    try:
        print("test_websocket")
        await rtWebsocket.websocket_endpoint(websocket, ws_manager)
    except Exception as e:
        print(f"test_websocket error {e}")

@app.websocket("/ws/webcamera")
async def camera_websocket(websocket: WebSocket):
    try:
        print("camera_websocket")
        await rtWebsocket.websocket_endpoint(websocket, camera_manager)
    except Exception as e:
        print(f"test_websocket error {e}")

@app.get("/video")
async def video_feed(video_path: str = Query(..., description="Path to the video file")):
    if not os.path.exists(video_path):
        return {"error": "File not found"}
    return StreamingResponse(video_streamer(video_path),media_type="video/mp4")


if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8888)