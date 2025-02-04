from fastapi.testclient import TestClient
from src.pointcloud_websocket.main import setup_websocket, websocket_endpoint
from fastapi import FastAPI, WebSocket

app = FastAPI()

# CORS 設定（必要に応じて）
app.add_middleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket サーバーをセットアップ
ws_manager = setup_websocket()

@app.websocket("/ws")
async def test_websocket(websocket: WebSocket):
    websocket_endpoint(websocket, ws_manager)

if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8080)