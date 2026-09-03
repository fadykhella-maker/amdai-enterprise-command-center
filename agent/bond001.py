"""Bond 001: a guarded local agent interface backed by Ollama."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "data" / "bond001-token.txt"
OLLAMA_URL = os.environ.get("BOND001_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("BOND001_MODEL", "phi4-mini:3.8b-q4_K_M")
STARTED = time.time()

SYSTEM_PROMPT = """You are Bond 001, the governed operations assistant for AMD Intelligent Cloud Control.
Explain evidence clearly, distinguish live services from plans, and never claim an action succeeded without runtime proof.
You currently have no operating-system or Kubernetes mutation tools. When an action is requested, propose a safe plan and
state that human approval and a dedicated allow-listed tool are required before execution."""

app = FastAPI(title="Bond 001", version="0.1.0")


def configured_token() -> str:
    token = os.environ.get("BOND001_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = configured_token()
    if not expected:
        raise HTTPException(status_code=503, detail="Bond 001 token is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def ollama_request(path: str, payload: dict | None = None, timeout: float = 5) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{OLLAMA_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=503, detail=f"Local Ollama runtime unavailable: {exc}") from exc


@app.get("/health")
def health() -> dict[str, object]:
    try:
        version = ollama_request("/api/version")
        runtime_state = "online"
    except HTTPException:
        version = {}
        runtime_state = "offline"
    return {
        "service": "bond-001",
        "state": "online",
        "runtime_state": runtime_state,
        "model": MODEL,
        "ollama_version": version.get("version", "unavailable"),
        "tools": "approval-gated",
        "uptime_seconds": int(time.time() - STARTED),
    }


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


@app.post("/api/chat", dependencies=[Depends(require_token)])
def chat(body: ChatRequest) -> dict[str, object]:
    response = ollama_request(
        "/api/chat",
        {
            "model": MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": body.message},
            ],
            "options": {"num_ctx": 8192, "temperature": 0.2},
        },
        timeout=300,
    )
    return {
        "agent": "Bond 001",
        "model": response.get("model", MODEL),
        "message": response.get("message", {}).get("content", ""),
        "done": response.get("done", False),
        "total_duration_ns": response.get("total_duration"),
        "load_duration_ns": response.get("load_duration"),
        "prompt_tokens": response.get("prompt_eval_count"),
        "response_tokens": response.get("eval_count"),
    }

