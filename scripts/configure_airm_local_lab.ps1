# Applies the supported local-lab mode after installing the upstream AIRM chart.
# AMD's local-development guidance permits skipping Kaiwo on clusters without
# supported GPU nodes. The upstream chart hard-codes these workloads as enabled,
# so this reversible post-install step prevents a crash loop and idle CronJobs.
$ErrorActionPreference = "Stop"

$kubectl = (Get-Command kubectl.exe -ErrorAction SilentlyContinue).Source
if (-not $kubectl) {
    $kubectl = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\kubectl.exe"
}
if (-not (Test-Path -LiteralPath $kubectl)) {
    throw "kubectl.exe was not found. Start Docker Desktop and verify its installation."
}

& $kubectl scale deployment/airm-agent -n airm --replicas=0
& $kubectl patch cronjob/airm-heartbeat-agent -n airm --type merge -p '{"spec":{"suspend":true}}'
& $kubectl rollout status deployment/airm-agent -n airm --timeout=90s
& $kubectl get deployment/airm-agent cronjob/airm-heartbeat-agent -n airm
