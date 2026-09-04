# Keeps a persistent kubectl port-forward alive for the AI Workbench API.
# Companion to start_workbench_ui_portforward.ps1 -- same always-on pattern.
$ErrorActionPreference = "Continue"
$kubectl = (Get-Command kubectl.exe -ErrorAction SilentlyContinue).Source
if (-not $kubectl) {
    $kubectl = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\kubectl.exe"
}
if (-not (Test-Path -LiteralPath $kubectl)) {
    throw "kubectl.exe was not found. Start Docker Desktop and verify its installation."
}
while ($true) {
    & $kubectl port-forward -n aiwb service/aiwb-api 8012:8080
    Start-Sleep -Seconds 5
}
