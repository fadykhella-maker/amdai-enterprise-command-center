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

[Environment]::SetEnvironmentVariable("OLLAMA_VULKAN", "1", "User")

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

$taskCommand = "`"$python`" -m uvicorn agent.bond001:app --host 127.0.0.1 --port 8766"
& schtasks.exe /Create /TN "Bond 001 Agent" /SC ONLOGON /TR $taskCommand /F | Out-Host

Write-Host "Bond 001 is ready on http://127.0.0.1:8766" -ForegroundColor Green
Write-Host "Its bearer token is stored locally in data\bond001-token.txt and is excluded from Git."

