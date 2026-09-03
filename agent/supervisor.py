"""Local-only AMD edge supervisor for telemetry and controlled ROCm actions."""

from __future__ import annotations

import os
import platform
import subprocess
import time
from importlib import metadata
from urllib.error import URLError
from urllib.request import urlopen

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

try:
    import torch
    TORCH_IMPORT_ERROR = ""
except Exception as exc:
    torch = None
    TORCH_IMPORT_ERROR = str(exc)[:240]

app = FastAPI(title="AMD Edge Supervisor", version="0.1.1")
STARTED = time.time()


def local_service(url: str) -> dict[str, object]:
    """Return a small, non-sensitive health record for a localhost service."""
    try:
        with urlopen(url, timeout=1.5) as response:
            return {"state": "online" if response.status < 400 else "degraded", "status_code": response.status}
    except (OSError, URLError, TimeoutError):
        return {"state": "offline"}


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.environ.get("AMD_SUPERVISOR_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Supervisor token is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def device_details() -> tuple[bool, str, str]:
    if torch is None:
        return False, "AMD Radeon(TM) 840M Graphics", "gfx1153"
    available = bool(torch.cuda.is_available())
    if not available:
        return False, "AMD Radeon(TM) 840M Graphics", "gfx1153"
    properties = torch.cuda.get_device_properties(0)
    architecture = getattr(properties, "gcnArchName", "gfx1153")
    return True, torch.cuda.get_device_name(0), str(architecture)


def windows_gpu_memory() -> dict[str, object]:
    """Report adapter-dedicated memory without calling it total model memory."""
    if os.name != "nt":
        return {"dedicated_gb": None, "source": "unavailable"}
    command = (
        "$gpu=Get-CimInstance Win32_VideoController | "
        "Where-Object Name -Match 'AMD Radeon' | Select-Object -First 1; "
        "if($gpu){[Console]::Write($gpu.AdapterRAM)}"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        adapter_bytes = int(result.stdout.strip())
        return {
            "dedicated_gb": round(adapter_bytes / 1024**3, 2),
            "source": "Win32_VideoController.AdapterRAM",
        }
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"dedicated_gb": None, "source": "unavailable"}


@app.get("/health")
def health() -> dict[str, object]:
    gpu_available, _, _ = device_details()
    return {
        "service": "amd-edge-supervisor",
        "state": "online",
        "compute_state": "ready" if torch is not None and gpu_available else "blocked",
        "uptime_seconds": int(time.time() - STARTED),
    }


@app.get("/api/status", dependencies=[Depends(require_token)])
def status() -> dict[str, object]:
    gpu_available, gpu_name, architecture = device_details()
    memory = psutil.virtual_memory()
    gpu_memory = windows_gpu_memory()
    hip_version = (torch.version.hip or "not reported") if torch is not None else package_version("rocm")
    pytorch_version = torch.__version__ if torch is not None else package_version("torch")
    return {
        "state": "online",
        "compute_state": "ready" if torch is not None and gpu_available else "blocked",
        "compute_error": TORCH_IMPORT_ERROR,
        "hostname": platform.node(),
        "operating_system": platform.platform(),
        "processor": platform.processor(),
        "cpu_percent": psutil.cpu_percent(interval=0.25),
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / 1024**3, 2),
        "memory_total_gb": round(memory.total / 1024**3, 2),
        "memory_available_gb": round(memory.available / 1024**3, 2),
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "architecture": architecture,
        "gpu_memory_kind": "integrated/shared system memory",
        "gpu_dedicated_memory_gb": gpu_memory["dedicated_gb"],
        "gpu_dedicated_memory_source": gpu_memory["source"],
        "gpu_shared_memory_gb": None,
        "gpu_memory_note": "Shared GPU memory is borrowed from system RAM and is not physical VRAM usage.",
        "gpu_percent": 0,
        "gpu_utilization_available": False,
        "gpu_temperature_c": None,
        "hip_version": hip_version,
        "pytorch_version": pytorch_version,
        "libraries": {
            "torch": package_version("torch"),
            "rocm": package_version("rocm"),
            "rocm-sdk-core": package_version("rocm-sdk-core"),
            "rocm-sdk-libraries": package_version("rocm-sdk-libraries"),
            "amd-torch-device-gfx1153": package_version("amd-torch-device-gfx1153"),
        },
        "services": {
            "ollama": local_service("http://127.0.0.1:11434/api/version"),
            "bond001": local_service("http://127.0.0.1:8766/health"),
            "ai_workbench": local_service("http://127.0.0.1:8011/api/health"),
        },
        "uptime_seconds": int(time.time() - STARTED),
        "timestamp": time.time(),
    }


class BenchmarkRequest(BaseModel):
    matrix_size: int = Field(default=1024, ge=256, le=4096)


@app.post("/api/benchmark", dependencies=[Depends(require_token)])
def benchmark(request: BenchmarkRequest) -> dict[str, object]:
    if torch is None:
        raise HTTPException(status_code=503, detail=f"ROCm runtime is blocked by Windows Application Control: {TORCH_IMPORT_ERROR}")
    if not torch.cuda.is_available():
        raise HTTPException(status_code=503, detail="Radeon device is unavailable to PyTorch")
    size = request.matrix_size
    device = torch.device("cuda")
    left = torch.randn((size, size), device=device)
    right = torch.randn((size, size), device=device)
    torch.cuda.synchronize()
    started = time.perf_counter()
    result = left @ right
    torch.cuda.synchronize()
    duration = time.perf_counter() - started
    checksum = float(result[0, 0].item())
    return {
        "device": torch.cuda.get_device_name(0),
        "shape": f"{size} x {size}",
        "gpu_seconds": duration,
        "checksum": checksum,
    }
