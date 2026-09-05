[CmdletBinding()]
param(
    [string]$Model = "phi4-mini:3.8b-q4_K_M",
    [switch]$SkipModelPull
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $repoRoot "data"
$tokenFile = Join-Path $dataDir "bond001-token.txt"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "The project virtual environment is missing. Recreate .venv and install requirements-agent.txt first."
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Ollama is not installed and winget is unavailable. Install Ollama for Windows from https://ollama.com/download/windows."
    }
    Write-Host "Installing native Ollama for Windows" -ForegroundColor Cyan
    & $winget.Source install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollama) { throw "Ollama installed, but this terminal must be reopened so PATH can refresh." }
}

# Radeon 840M is gfx1153 (Krackan Point), which is outside Ollama's ROCm/rocBLAS
# supported-target list. Forcing it via HSA_OVERRIDE_GFX_VERSION was tested and
# crashes ("ROCm error: device kernel image is invalid") because the gfx1151
# kernels are not ISA-compatible with real gfx1153 hardware. Ollama's Vulkan
# backend correctly detects and drives this GPU; it only needs to be told not
# to drop integrated GPUs.
[Environment]::SetEnvironmentVariable("OLLAMA_IGPU_ENABLE", "1", "User")
[Environment]::SetEnvironmentVariable("HSA_OVERRIDE_GFX_VERSION", $null, "User")
[Environment]::SetEnvironmentVariable("OLLAMA_VULKAN", $null, "User")
# Registry writes above only reach brand-new process environment blocks, so also
# set it for this session in case this script has to launch "ollama serve" itself.
$env:OLLAMA_IGPU_ENABLE = "1"
Remove-Item Env:\HSA_OVERRIDE_GFX_VERSION -ErrorAction SilentlyContinue

try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3 | Out-Null
} catch {
    Start-Process -FilePath $ollama.Source -ArgumentList @("serve") -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

if (-not $SkipModelPull) {
    Write-Host "Pulling the initial Bond 001 model: $Model" -ForegroundColor Cyan
    & $ollama.Source pull $Model
    if ($LASTEXITCODE -ne 0) { throw "Ollama could not pull $Model." }
}

New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
if (-not (Test-Path $tokenFile)) {
    $token = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
    [IO.File]::WriteAllText($tokenFile, $token)
    Remove-Variable token
}

[Environment]::SetEnvironmentVariable("BOND001_MODEL", $Model, "User")

$existing = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object CommandLine -Match "agent.bond001"
if (-not $existing) {
    Start-Process -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "agent.bond001:app", "--host", "127.0.0.1", "--port", "8766") `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden
}

Start-Sleep -Seconds 3
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8766/health" -TimeoutSec 10
$health | Format-List | Out-Host

# schtasks.exe /TR re-tokenizes its whole command string by spaces even when
# PowerShell already quoted the python.exe path, which breaks on "Fady KHELLA"
# in this machine's user profile path -- a prior attempt to fix that by
# escaping the inner quotes still failed in real use (untestable here, since
# this sandbox has no Task Scheduler access). Register-ScheduledTask sidesteps
# the whole problem: -Execute and -Argument are separate parameters, so the
# path with spaces never has to survive being re-parsed out of one string.
$taskAction = New-ScheduledTaskAction -Execute $python -Argument "-m uvicorn agent.bond001:app --host 127.0.0.1 --port 8766" -WorkingDirectory $repoRoot
$taskTrigger = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName "Bond 001 Agent" -Action $taskAction -Trigger $taskTrigger -Description "Bond 001 local agent (FastAPI wrapper around Ollama)" -Force | Out-Null

Write-Host "Bond 001 is ready on http://127.0.0.1:8766" -ForegroundColor Green
Write-Host "Its bearer token is stored locally in data\bond001-token.txt and is excluded from Git."

