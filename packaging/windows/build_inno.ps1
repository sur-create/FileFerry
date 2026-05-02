Param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

function Get-Version {
    return (python -c "from fileferry import __version__; print(__version__)").Trim()
}

function Resolve-Iscc {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }

    throw "ISCC.exe not found. Install Inno Setup 6 first."
}

if (-not $Version) {
    $Version = Get-Version
}

if (-not (Test-Path "dist/fileferry/fileferry.exe")) {
    Write-Host "dist/fileferry missing. building PyInstaller binary..."
    python scripts/build_binary.py --clean
}

$iscc = Resolve-Iscc
$scriptPath = Join-Path $PSScriptRoot "fileferry.iss"

Write-Host "+ $iscc /DMyAppVersion=$Version $scriptPath"
& $iscc "/DMyAppVersion=$Version" "$scriptPath"
Write-Host "Windows installer created under dist/installer"
