[CmdletBinding()]
param(
    [string]$ReleaseVersion = "2.0.1",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$valuesFile = Join-Path $repoRoot "deploy\kubernetes\aiwb-local-values.yaml"

function Resolve-Tool {
    param([Parameter(Mandatory)][string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw "$Name is not available in this PowerShell PATH. Open a terminal where $Name works, then run this script again."
}

function Assert-KubernetesResource {
    param([Parameter(Mandatory)][string[]]$Arguments, [Parameter(Mandatory)][string]$Description)
    & $script:kubectl @Arguments *> $null
    if ($LASTEXITCODE -ne 0) { throw "Missing prerequisite: $Description" }
}

$script:kubectl = Resolve-Tool "kubectl"
$helm = Resolve-Tool "helm"

Write-Host "[1/7] Auditing the existing cluster" -ForegroundColor Cyan
& $kubectl cluster-info | Out-Host
Assert-KubernetesResource @("get", "namespace", "aiwb") "namespace aiwb"
Assert-KubernetesResource @("get", "deployment", "aim-engine-controller-manager", "-n", "aim-system") "AIM Engine"
Assert-KubernetesResource @("get", "deployment", "kserve-controller-manager", "-n", "kserve") "KServe"
Assert-KubernetesResource @("get", "cluster", "aiwb-infra-cnpg-cnpg", "-n", "aiwb") "AIWB PostgreSQL"
Assert-KubernetesResource @("get", "service", "aiwb-minio", "-n", "aiwb") "AIWB MinIO"
Assert-KubernetesResource @("get", "service", "keycloak", "-n", "keycloak") "Keycloak"

Write-Host "[2/7] Verifying required credentials by name (values are never printed)" -ForegroundColor Cyan
Assert-KubernetesResource @("get", "secret", "aiwb-cnpg-user", "-n", "aiwb") "AIWB database credentials"
Assert-KubernetesResource @("get", "secret", "aiwb-ui-keycloak-secret", "-n", "aiwb") "AIWB Keycloak client secret"
Assert-KubernetesResource @("get", "secret", "aiwb-nextauth-secret", "-n", "aiwb") "AIWB NextAuth secret"

& $kubectl get secret minio-credentials -n aiwb *> $null
if ($LASTEXITCODE -ne 0) {
    & $kubectl get secret aiwb-minio -n aiwb *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Missing MinIO credentials: expected secret minio-credentials or aiwb-minio in namespace aiwb."
    }
    $accessKey = & $kubectl get secret aiwb-minio -n aiwb -o 'jsonpath={.data.rootUser}'
    $secretKey = & $kubectl get secret aiwb-minio -n aiwb -o 'jsonpath={.data.rootPassword}'
    if (-not $accessKey -or -not $secretKey) {
        throw "Secret aiwb-minio does not contain rootUser/rootPassword keys."
    }
    $manifest = [ordered]@{
        apiVersion = "v1"
        kind = "Secret"
        metadata = [ordered]@{ name = "minio-credentials"; namespace = "aiwb" }
        type = "Opaque"
        data = [ordered]@{ "minio-access-key" = $accessKey; "minio-secret-key" = $secretKey }
    } | ConvertTo-Json -Depth 5
    $manifest | & $kubectl apply -f - | Out-Host
}

& $kubectl get secret cluster-auth-admin-token -n aiwb *> $null
if ($LASTEXITCODE -ne 0) {
    $localToken = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
    & $kubectl create secret generic cluster-auth-admin-token -n aiwb --from-literal="value=$localToken" | Out-Host
    Remove-Variable localToken
}

if (-not $SkipDependencyInstall) {
    Write-Host "[3/7] Installing only missing Workbench operators" -ForegroundColor Cyan
    & $helm repo add kyverno https://kyverno.github.io/kyverno/ --force-update | Out-Host
    & $helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts --force-update | Out-Host
    & $helm repo update | Out-Host
    & $helm upgrade --install kyverno kyverno/kyverno --namespace kyverno --create-namespace --wait --timeout 10m | Out-Host
    & $helm upgrade --install opentelemetry-operator open-telemetry/opentelemetry-operator --namespace opentelemetry-operator-system --create-namespace --set manager.collectorImage.repository=otel/opentelemetry-collector-k8s --wait --timeout 10m | Out-Host
}

Write-Host "[4/7] Deploying AMD AI Workbench $ReleaseVersion" -ForegroundColor Cyan
& $helm upgrade --install aiwb oci://registry-1.docker.io/amdenterpriseai/aiwb-chart `
    --version $ReleaseVersion `
    --namespace aiwb `
    --values $valuesFile `
    --wait `
    --timeout 15m | Out-Host

if ($LASTEXITCODE -ne 0) { throw "AI Workbench Helm deployment failed." }

Write-Host "[5/7] Applying the local browser callback URL" -ForegroundColor Cyan
& $kubectl set env deployment/aiwb-ui -n aiwb NEXTAUTH_URL=http://127.0.0.1:8011 | Out-Host
& $kubectl rollout status deployment/aiwb-api -n aiwb --timeout=600s | Out-Host
& $kubectl rollout status deployment/aiwb-ui -n aiwb --timeout=600s | Out-Host

Write-Host "[6/7] Verifying Workbench health" -ForegroundColor Cyan
& $kubectl get pods,services -n aiwb | Out-Host
& $kubectl get deployment aiwb-api aiwb-ui -n aiwb | Out-Host

Write-Host "[7/7] Starting persistent local port forwards" -ForegroundColor Cyan
$forwardDir = Join-Path $env:TEMP "amd-eai-port-forwards"
New-Item -ItemType Directory -Path $forwardDir -Force | Out-Null
foreach ($item in @(
    @{ Name = "aiwb-ui"; Arguments = @("port-forward", "-n", "aiwb", "service/aiwb-ui", "8011:8000") },
    @{ Name = "aiwb-api"; Arguments = @("port-forward", "-n", "aiwb", "service/aiwb-api", "8012:8080") }
)) {
    Get-CimInstance Win32_Process -Filter "Name = 'kubectl.exe'" -ErrorAction SilentlyContinue |
        Where-Object CommandLine -Match "service/$($item.Name)" |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Process -FilePath $kubectl -ArgumentList $item.Arguments -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $forwardDir "$($item.Name).out.log") `
        -RedirectStandardError (Join-Path $forwardDir "$($item.Name).err.log")
}

Write-Host "AI Workbench is deployed." -ForegroundColor Green
Write-Host "UI:  http://127.0.0.1:8011"
Write-Host "API: http://127.0.0.1:8012/v1/health"
Write-Host "Keycloak must remain forwarded at http://127.0.0.1:8080 for browser login."

