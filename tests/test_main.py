import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from pointcloud_websocket.middleware.timeout import TimeoutMiddleware
from pointcloud_websocket.main import setup_manager, websocket_endpoint
from fastapi import FastAPI, WebSocket

app = FastAPI()

# CORS 設定（必要に応じて）
app.add_middleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TimeoutMiddleware, timeout=10)
# WebSocket サーバーをセットアップ
ws_manager = setup_manager()

@app.websocket("/ws")
async def test_websocket(websocket: WebSocket):
    websocket_endpoint(websocket, ws_manager)

if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8080)