"""Low-latency Bond 001 runtime for the Dell ROCm edge node.

Run this inside the existing AMD Supervisor process or mount the exported
router into it. The model is loaded once and remains resident on the Radeon
GPU between requests; Kubernetes can supervise the service without adding a
per-message pod or notebook startup.
"""
from __future__ import annotations

import os
import threading
import time

import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

router = APIRouter(prefix="/api/bond", tags=["bond"])
MODEL_ID = os.getenv("AMD_BOND_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
MAX_NEW_TOKENS = int(os.getenv("AMD_BOND_MAX_NEW_TOKENS", "160"))
_lock = threading.Lock()
_tokenizer = None
_model = None
_loaded_at = None


class BondRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=12)


def _load() -> None:
    global _tokenizer, _model, _loaded_at
    if _model is not None:
        return
    if not torch.cuda.is_available():
        raise RuntimeError("ROCm GPU is unavailable")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float16, low_cpu_mem_usage=True
    ).eval().to("cuda")
    _loaded_at = time.time()


@router.get("/status")
def status() -> dict:
    return {
        "state": "ready" if _model is not None else "online",
        "model": MODEL_ID,
        "backend": "ROCm persistent edge",
        "loaded": _model is not None,
    }


@router.post("/warm")
def warm() -> dict:
    with _lock:
        _load()
    return status()


@router.post("/chat")
def chat(request: BondRequest) -> dict:
    started = time.perf_counter()
    try:
        with _lock:
            _load()
            messages = [{"role": "system", "content": "You are Bond 001, a concise AMD edge AI assistant."}]
            messages.extend(request.history[-12:])
            messages.append({"role": "user", "content": request.message})
            prompt = _tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = _tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.inference_mode():
                output = _model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW_TOKENS,
                    do_sample=False,
                    use_cache=True,
                    pad_token_id=_tokenizer.eos_token_id,
                )
            new_tokens = output[0, inputs.input_ids.shape[1]:]
            answer = _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)[:240]) from exc
    elapsed = max(time.perf_counter() - started, 0.001)
    return {"answer": answer, "model": MODEL_ID, "latency_ms": round(elapsed * 1000), "tokens_per_second": round(len(new_tokens) / elapsed, 1)}
