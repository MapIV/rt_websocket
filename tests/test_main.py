from rtWebsocket.middleware.timeout import TimeoutMiddleware
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import rtWebsocket

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

if __name__ == "__main__":
    
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8080)