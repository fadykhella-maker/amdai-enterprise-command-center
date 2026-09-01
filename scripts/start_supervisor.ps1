$ErrorActionPreference = "Stop"

$projectFolder = Split-Path -Parent $PSScriptRoot
$tokenFolder = Join-Path $projectFolder "data"
$tokenFile = Join-Path $tokenFolder "supervisor-token.txt"
$pythonPath = "C:\AI\AMD-Enterprise-AI\.venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "The AMD ROCm Python environment was not found at C:\AI\AMD-Enterprise-AI\.venv"
}

New-Item -ItemType Directory -Path $tokenFolder -Force | Out-Null
$tokenMissingOrInvalid = (-not (Test-Path -LiteralPath $tokenFile))
if (-not $tokenMissingOrInvalid) {
    $tokenMissingOrInvalid = ((Get-Content -Raw -LiteralPath $tokenFile).Trim().Length -lt 32)
}
if ($tokenMissingOrInvalid) {
    $bytes = New-Object byte[] 48
    $randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $randomGenerator.GetBytes($bytes)
    }
    finally {
        $randomGenerator.Dispose()
    }
    [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $tokenFile -NoNewline
}

$env:AMD_SUPERVISOR_TOKEN = (Get-Content -Raw -LiteralPath $tokenFile).Trim()
Set-Location -LiteralPath $projectFolder
& $pythonPath -m uvicorn agent.supervisor:app --host 127.0.0.1 --port 8765
