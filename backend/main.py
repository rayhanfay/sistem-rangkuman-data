import os
import uvicorn
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.database.database import engine, Base
from app.presentation.routes import web_api
from app.presentation.protocols.mcp_server import McpServer

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# --- Inisialisasi Tabel Database ---
try:
    Base.metadata.create_all(bind=engine)
    logging.info("Tabel database berhasil diperiksa/dibuat.")
except Exception as e:
    logging.error(f"Gagal membuat tabel database: {e}", exc_info=True)

# --- Inisialisasi Aplikasi FastAPI ---
app = FastAPI(
    title="PHR Data Summarization - Hybrid Server",
    version="8.2.0 (Azure-Optimized)",
    description="Backend API mendukung REST & WebSocket (MCP) - Serverless Ready."
)

# --- Konfigurasi CORS ---
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173"
)
origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# --- Registrasi Router ---
app.include_router(web_api.router) 
logging.info("REST API router berhasil didaftarkan di /api/web.")

# --- Endpoint Root ---
@app.get("/", tags=["Root"])
async def root():
    return {
        "status": "online",
        "service": "PHR Hybrid Server",
        "mode": "Serverless-Web"
    }

# --- Endpoint WebSocket untuk MCP ---
@app.websocket("/mcp")
async def mcp_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    mcp_server = McpServer()
    logging.info(f"Klien MCP terhubung dari: {websocket.client.host}")
    
    try:
        while True:
            request_data = await websocket.receive_json()
            response_data = await mcp_server.handle_request(request_data, websocket)
            if response_data:
                await websocket.send_json(response_data)
                
    except WebSocketDisconnect:
        logging.info(f"Klien MCP terputus: {websocket.client.host}")
    except Exception as e:
        logging.error(f"Terjadi error pada WebSocket: {e}", exc_info=True)
        if not websocket.client_state.DISCONNECTED:
            await websocket.send_json({
                "jsonrpc": "2.0", 
                "error": {"code": -32000, "message": "Terjadi error internal pada server."},
                "id": None
            })

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)