
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status as http_status
from fastapi import Depends
from pathlib import Path
from typing import Optional
import os
import json

from . import status


def _verify_api_key(request: Request):
    expected = os.environ.get("JARVIS_API_KEY")
    if not expected:
        raise HTTPException(status_code=401, detail="API key not configured on server")
    auth = request.headers.get("Authorization") or request.headers.get("X-API-KEY")
    token = None
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
    elif auth:
        token = auth.strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    client = request.client
    if client and client.host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Access restricted to localhost")
    return True


app = FastAPI(title="Jarvis Status API")

_DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:3000,http://localhost:3000,"
    "http://127.0.0.1:5173,http://localhost:5173"
)
_CORS_ORIGINS = [
    origin.strip() for origin in os.environ.get(
        "JARVIS_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS
    ).split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-KEY"],
)

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "jarvis.log"


@app.get("/status")
def get_status(request: Request, _=Depends(_verify_api_key)):
    s = status.read_status()
    return JSONResponse(content=s or {"state": "unknown"})


@app.get("/logs")
def get_logs(request: Request, lines: Optional[int] = 200, _=Depends(_verify_api_key)):
    try:
        if not LOG_PATH.exists():
            return PlainTextResponse("", status_code=200)
        with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read().splitlines()
        out = "\n".join(data[-int(lines):])
        return PlainTextResponse(out, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_status")
def clear_status(request: Request, _=Depends(_verify_api_key)):
    try:
        status.clear_status()
        return JSONResponse(content={"ok": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
