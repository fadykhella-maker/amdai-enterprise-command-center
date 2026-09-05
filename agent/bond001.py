"""Bond 001: a guarded local agent interface backed by Ollama."""

from __future__ import annotations

import json
import os
import re
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
state that human approval and a dedicated allow-listed tool are required before execution.

You do have one read-only tool: web_search. Use it whenever a question needs current, real-world, or
time-sensitive information you can't be certain of from memory -- prices, news, scores, current events, specific facts
you're not fully sure of. Don't guess when you can look it up. For anything else (math, general knowledge,
conversation), answer directly without using the tool."""

# web_search(query) -- DuckDuckGo via ddgs: free, keyless, no signup, nothing to
# substitute at push time. Bond's own model decides when to call it and writes
# the final answer from the raw result snippets; there's no synthesized
# "answer" field like a paid search API would provide, which is the deliberate
# trade-off for zero credentials/zero billing risk. Same tool, same rationale
# as the one already shipped on the NVIDIA/Kaggle side of this project.
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the live internet for current, real-world information -- news, prices, "
            "facts, anything that requires up-to-date knowledge beyond training data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for, as a natural search query."}
            },
            "required": ["query"],
        },
    },
}


def web_search(query: str) -> str:
    from ddgs import DDGS

    try:
        results = DDGS().text(query, max_results=5)
    except Exception as exc:
        return f"Search error: {exc}"
    if not results:
        return f"No results found for: {query}"
    parts = []
    for item in results:
        parts.append(
            f"- {item.get('title', '')} ({item.get('href', '')}): {item.get('body', '')[:300]}"
        )
    return "\n".join(parts)


BOND_TOOLS = {"web_search": web_search}

# Verified directly against this Ollama install: qwen2.5:1.5b never emits a
# tool call at all with a small model like this (tools_used stays empty even
# with tools= passed); phi4-mini DOES try, but leaks it as literal text
# ("<|tool_call|>{...}") instead of Ollama's structured message.tool_calls --
# its Modelfile template doesn't parse that shape back out for us. Rather than
# trust either model's template, the reply's plain content is always scanned
# for a tool-call-shaped JSON object as a fallback, same rationale as the
# tag-parsing fallback already shipped on the NVIDIA/Kaggle side of this
# project (there: Phi-3.5-mini drops the <tool_call> wrapper tags entirely).
_TOOL_CALL_MARKER = re.compile(r"<\|?tool_call\|?>\s*(\{)", re.IGNORECASE)


def _extract_balanced_json(text: str, start: int) -> dict | None:
    """text[start] must be '{'. Returns the parsed object at that position by
    counting braces (tolerates trailing junk after the closing brace, which a
    plain regex with a non-greedy match can silently truncate on)."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _find_query(obj: object) -> str | None:
    if isinstance(obj, dict):
        value = obj.get("query")
        if isinstance(value, str):
            return value
        for v in obj.values():
            found = _find_query(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_query(v)
            if found:
                return found
    return None


def extract_fallback_tool_call(content: str) -> dict | None:
    """Best-effort recovery of a tool call a model wrote as plain text instead
    of Ollama's structured tool_calls field. Returns {"name", "arguments"} or
    None if nothing tool-call-shaped is present."""
    match = _TOOL_CALL_MARKER.search(content)
    start = match.start(1) if match else content.find('{"name"')
    if start == -1:
        return None
    call = _extract_balanced_json(content, start)
    if not isinstance(call, dict) or call.get("name") not in BOND_TOOLS:
        return None
    query = _find_query(call)
    return {"name": call["name"], "arguments": {"query": query} if query else {}}


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


@app.get("/api/models", dependencies=[Depends(require_token)])
def models() -> dict[str, object]:
    """List models actually pulled in the local Ollama runtime -- never a fabricated list."""
    try:
        tags = ollama_request("/api/tags")
        names = [m.get("name") for m in tags.get("models", []) if m.get("name")]
    except HTTPException:
        names = []
    return {"models": names, "default": MODEL}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = Field(default=None, max_length=200)


@app.post("/api/chat", dependencies=[Depends(require_token)])
def chat(body: ChatRequest) -> dict[str, object]:
    model = body.model or MODEL
    messages: list[dict[str, object]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": body.message},
    ]
    tools_used: list[str] = []
    response: dict[str, object] = {}

    # Up to 3 rounds: a tool-calling model can chain more than one lookup
    # (e.g. search, then a follow-up search) before giving a final answer.
    for _ in range(3):
        response = ollama_request(
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "messages": messages,
                "tools": [WEB_SEARCH_TOOL],
                "options": {"num_ctx": 8192, "temperature": 0.2},
            },
            timeout=300,
        )
        message = response.get("message", {}) or {}
        content = message.get("content", "") or ""
        calls = message.get("tool_calls") or []
        used_fallback = False
        if not calls:
            fallback = extract_fallback_tool_call(content)
            if fallback:
                calls = [{"function": fallback}]
                used_fallback = True
        if not calls:
            break
        # A genuine structured tool_calls message can go straight back as the
        # "assistant" turn Ollama itself produced, followed by "tool" role
        # results. A fallback-recovered call has no such structured message --
        # its raw leaked text goes back as an ordinary assistant turn, and the
        # result as an ordinary user turn, since a model whose own template
        # doesn't correctly emit tool_calls can't be trusted to understand a
        # "tool" role turn either.
        messages.append({"role": "assistant", "content": content} if used_fallback else message)
        for call in calls:
            fn = call.get("function", {}) or {}
            name = fn.get("name")
            args = fn.get("arguments") or {}
            tool_fn = BOND_TOOLS.get(name)
            if tool_fn is None:
                result = f"Unknown tool: {name}"
            else:
                try:
                    result = tool_fn(**args)
                except Exception as exc:
                    result = f"Tool error: {exc}"
                else:
                    tools_used.append(name)
            if used_fallback:
                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool result for {name}:\n{result}\n\n"
                        "Now answer my original question using this information. "
                        "Reply in plain language -- don't call the tool again."
                    ),
                })
            else:
                messages.append({"role": "tool", "content": str(result)})

    return {
        "agent": "Bond 001",
        "model": response.get("model", model),
        "message": response.get("message", {}).get("content", ""),
        "tools_used": tools_used,
        "done": response.get("done", False),
        "total_duration_ns": response.get("total_duration"),
        "load_duration_ns": response.get("load_duration"),
        "prompt_tokens": response.get("prompt_eval_count"),
        "response_tokens": response.get("eval_count"),
    }

