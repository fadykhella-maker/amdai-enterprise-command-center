# Keeps a persistent kubectl port-forward alive for the AI Workbench UI.
# Mirrors the always-on pattern used by scripts/start_supervisor.ps1 /
# the "AMD Edge Supervisor" scheduled task. Auto-restarts on any exit
# (pod restart, transient network blip, kubectl reconnect, etc.).
$ErrorActionPreference = "Continue"
$kubectl = (Get-Command kubectl.exe -ErrorAction SilentlyContinue).Source
if (-not $kubectl) {
    $kubectl = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\kubectl.exe"
}
if (-not (Test-Path -LiteralPath $kubectl)) {
    throw "kubectl.exe was not found. Start Docker Desktop and verify its installation."
}
while ($true) {
    & $kubectl port-forward -n aiwb service/aiwb-ui 8011:8000
    Start-Sleep -Seconds 5
}
