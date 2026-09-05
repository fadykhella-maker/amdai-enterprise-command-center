# Keeps a persistent kubectl port-forward alive for the AIRM (Resource Manager) API.
# Mirrors start_workbench_api_portforward.ps1 -- same always-on pattern.
$ErrorActionPreference = "Continue"
$kubectl = (Get-Command kubectl.exe -ErrorAction SilentlyContinue).Source
if (-not $kubectl) {
    $kubectl = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\kubectl.exe"
}
if (-not (Test-Path -LiteralPath $kubectl)) {
    throw "kubectl.exe was not found. Start Docker Desktop and verify its installation."
}
while ($true) {
    & $kubectl port-forward -n airm service/airm-api 8090:80
    Start-Sleep -Seconds 5
}
