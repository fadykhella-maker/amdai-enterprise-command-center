<#
.SYNOPSIS
    Installs AMD's ROCm-enabled PyTorch/torchvision/torchaudio into this project's
    .venv, using the exact pinned versions the AMD Edge Supervisor expects.

.DESCRIPTION
    These packages are not in requirements.txt / requirements-agent.txt because
    they come from AMD's own ROCm wheel index (repo.amd.com), not PyPI, and pip
    requirements files can't express a per-package --index-url. This script is
    the durable, repeatable replacement for that command living only in shell
    history, which is how the regression this script fixes actually happened:
    the .venv lost its torch install with no record of how to rebuild it.

    Root cause this addresses: the ROCm SDK's bundled rocBLAS kernel files are
    deeply nested (e.g. ...\_rocm_sdk_libraries\bin\rocblas\library\gfx90a\
    TensileLibrary_Type_..._gfx90a.co) and, combined with this repo's own long
    path, exceed Windows' legacy 260-character MAX_PATH during pip's install
    step -- confirmed directly: the same install succeeds unchanged under a
    shorter path. Enabling Windows' Long Paths support
    (HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled) fixes
    this permanently but requires Administrator elevation this script can't
    grant itself. Run the line below ONCE from an elevated PowerShell if you
    want that instead of relying on the fallback below:

        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord

    Whether or not that's ever done, this script is self-healing either way:
    it tries the install directly first, and only if that fails with exactly
    this long-path OSError does it fall back to a temporary `subst` virtual
    drive letter (no admin rights needed, removed again immediately after)
    to shorten the effective path just for the install.
#>
[CmdletBinding()]
param(
    [string]$TorchVersion = "2.12.0+rocm7.14.0",
    [string]$TorchVisionVersion = "0.27.0+rocm7.14.0",
    [string]$TorchAudioVersion = "2.11.0+rocm7.14.0",
    [string]$IndexUrl = "https://repo.amd.com/rocm/whl-multi-arch/"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "The project virtual environment is missing. Create .venv first (python -m venv .venv)."
}

# Best-effort, silent attempt at the permanent fix -- succeeds only when this
# shell is already elevated, harmlessly does nothing otherwise (the fallback
# below covers that case).
try {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord -ErrorAction Stop
    Write-Host "Windows Long Paths support enabled (this shell was elevated)." -ForegroundColor Green
} catch {
    Write-Host "Skipping the Long Paths registry fix (needs Administrator elevation) -- using the subst fallback instead if needed." -ForegroundColor Yellow
}

$packages = @(
    "torch[device-all]==$TorchVersion",
    "torchvision[device-all]==$TorchVisionVersion",
    "torchaudio==$TorchAudioVersion"
)

function Invoke-RocmInstall {
    param([string]$PythonExe)
    $output = & $PythonExe -m pip install --index-url $IndexUrl @packages 2>&1
    $output | ForEach-Object { Write-Host $_ }
    return @{ ExitCode = $LASTEXITCODE; Output = ($output | Out-String) }
}

Write-Host "Installing torch/torchvision/torchaudio $TorchVersion from $IndexUrl ..." -ForegroundColor Cyan
$result = Invoke-RocmInstall -PythonExe $python

$hitLongPathBug = $result.ExitCode -ne 0 -and $result.Output -match "No such file or directory" -and $result.Output -match "\.co'"

if ($hitLongPathBug) {
    Write-Host "`nHit the known long-path install failure. Falling back to a temporary short drive letter..." -ForegroundColor Yellow

    $driveLetter = 90..65 | ForEach-Object { [char]$_ } | Where-Object {
        -not (Get-PSDrive -Name $_ -ErrorAction SilentlyContinue) -and -not (Test-Path "${_}:\")
    } | Select-Object -First 1
    if (-not $driveLetter) { throw "No free drive letter available for the subst fallback." }

    subst "${driveLetter}:" $repoRoot
    try {
        $shortPython = "${driveLetter}:\.venv\Scripts\python.exe"
        $result = Invoke-RocmInstall -PythonExe $shortPython
    } finally {
        subst "${driveLetter}:" /D
    }

    if ($result.ExitCode -ne 0) {
        throw "ROCm/torch install failed even through the short-path fallback. See output above."
    }
} elseif ($result.ExitCode -ne 0) {
    throw "ROCm/torch install failed for a reason other than the known long-path bug. See output above."
}

Write-Host "`nVerifying..." -ForegroundColor Cyan
& $python -c "import torch; print('PyTorch:', torch.__version__); print('HIP:', torch.version.hip); print('Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'not detected')"

Write-Host "`nDone. Restart the AMD Edge Supervisor scheduled task to pick this up:" -ForegroundColor Green
Write-Host "  Stop-ScheduledTask -TaskName `"AMD Edge Supervisor`"; Start-ScheduledTask -TaskName `"AMD Edge Supervisor`""
