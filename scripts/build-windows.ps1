# Build Secret Kit as a portable Windows onedir folder + zip (pywebview / WebView2).
# Embeds CPython + engine + UI via PyInstaller. Does not bundle WebView2 Runtime
# (Evergreen — see scripts/build-windows.md). Never uploads or Authenticode-signs.
#
# UNTESTED on a real Windows host as of authoring — written to mirror
# scripts/build-macos.sh. Run on Windows 10/11; fix locally if needed.
#
# Requires: Windows PowerShell 5.1+ or PowerShell 7+; Python 3.9+ on PATH.

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Version = "",

    [switch] $SkipZip,
    [switch] $OneFile,
    [switch] $Console,
    [switch] $HttpFallback,
    [switch] $Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-Usage {
    @"
Usage: .\scripts\build-windows.ps1 [VERSION] [-SkipZip] [-OneFile] [-Console] [-HttpFallback]

  VERSION          Artifact version (default: `$env:VERSION, else VERSION file, else 0.1.0-dev)
  -SkipZip         Build dist\SecretKit\ only; do not write zip + .sha256
  -OneFile         Also build a one-file exe (experimental; onedir zip remains primary)
  -Console         Show a console window (debug)
  -HttpFallback    Bake default launch as --http 127.0.0.1:8765 (not recommended;
                   window / WebView2 mode is the default and preferred)

Environment:
  VERSION          Same as positional VERSION
  SKIP_ZIP=1       Same as -SkipZip
  PYTHON           Python interpreter (default: python)

Writes:
  dist\SecretKit\SecretKit.exe          (onedir)
  dist\secret-kit-<VERSION>-windows-<arch>.zip
  dist\secret-kit-<VERSION>-windows-<arch>.zip.sha256

Does NOT Authenticode-sign or upload. WebView2 Evergreen must exist on the run PC.
"@
}

function Die([string] $Message) {
    Write-Host "error: $Message" -ForegroundColor Red
    exit 1
}

if ($Help) {
    Show-Usage
    exit 0
}

# Refuse signing / publish switches that might appear in muscle-memory CI copy-paste.
foreach ($arg in $args) {
    switch -Regex ($arg) {
        '^(--)?(sign|Sign|authenticode|Authenticode|upload|Upload|publish|Publish)$' {
            Die "refusing '$arg' — Authenticode/upload needs a code-signing cert on the build host and explicit approval; see scripts/build-windows.md"
        }
    }
}
if ($PSBoundParameters.ContainsKey('Sign') -or $PSBoundParameters.ContainsKey('Upload')) {
    Die "refusing Sign/Upload — see scripts/build-windows.md"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $Root

if (-not $Version) {
    if ($env:VERSION) {
        $Version = $env:VERSION.Trim()
    }
    elseif (Test-Path (Join-Path $Root "VERSION")) {
        $Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
    }
    else {
        $Version = "0.1.0-dev"
    }
}

if (-not $Version) { Die "VERSION is empty" }
if ($Version -match '[/\\:\*\?\"<>\|\s]' -or $Version.Contains("..")) {
    Die "VERSION looks unsafe: $Version"
}

if ($env:SKIP_ZIP -eq "1") { $SkipZip = $true }

$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
try {
    $pyVer = & $Py -c "import sys; print('%d.%d' % sys.version_info[:2])"
} catch {
    Die "Python not found ($Py). Install Python 3.9+ from python.org and re-run."
}
Write-Host "Using $Py ($pyVer)"

# Arch label for artifact names
$IsArm = $env:PROCESSOR_ARCHITECTURE -match 'ARM'
if (-not $IsArm -and $env:PROCESSOR_ARCHITEW6432 -match 'ARM') { $IsArm = $true }
# Prefer runtime check
try {
    $archCheck = & $Py -c "import platform; print(platform.machine())"
} catch {
    $archCheck = $env:PROCESSOR_ARCHITECTURE
}
switch -Regex ($archCheck) {
    'ARM64|aarch64' { $ArchTag = "arm64" }
    'AMD64|x86_64|x64' { $ArchTag = "x64" }
    default {
        # 64-bit Intel fallback
        if ([Environment]::Is64BitOperatingSystem) { $ArchTag = "x64" }
        else { Die "unsupported arch: $archCheck (need 64-bit Windows)" }
    }
}

foreach ($req in @(
        "app.py",
        "requirements-engine.txt",
        "requirements-desktop-windows.txt",
        "ui\index.html"
    )) {
    if (-not (Test-Path (Join-Path $Root $req))) {
        Die "missing $req — run from a complete Secret Kit tree"
    }
}

Write-Host "Building Windows portable ($ArchTag) version $Version…"

# --- venv ---
$VenvDir = Join-Path $Root ".venv-win-build"
$VenvPy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "Creating build venv at .venv-win-build …"
    & $Py -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Die "venv creation failed" }
}
$VenvPy = (Resolve-Path $VenvPy).Path

Write-Host "Installing Windows desktop deps + PyInstaller into build venv…"
& $VenvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Die "pip upgrade failed" }
& $VenvPy -m pip install -r (Join-Path $Root "requirements-desktop-windows.txt")
if ($LASTEXITCODE -ne 0) { Die "pip install requirements-desktop-windows.txt failed (do not use requirements-desktop.txt on Windows — it pulls pyobjc)" }
& $VenvPy -m pip install "pyinstaller>=6.3,<7"
if ($LASTEXITCODE -ne 0) { Die "pip install pyinstaller failed" }

# --- staging for optional HTTP launcher wrapper ---
$Stage = Join-Path $Root "build\windows"
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Path $Stage | Out-Null

$Entry = Join-Path $Root "app.py"
if ($HttpFallback) {
    Write-Host "WARNING: -HttpFallback bakes --http 127.0.0.1:8765 as default (window mode preferred)."
    $wrapper = Join-Path $Stage "secretkit_entry.py"
    @"
# Auto-generated by build-windows.ps1 — HTTP fallback entry (not recommended).
import sys
from pathlib import Path

# Ensure repo/bundle root is on sys.path when frozen or not.
if getattr(sys, "frozen", False):
    root = Path(sys._MEIPASS)
else:
    root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

sys.argv = [sys.argv[0], "--http", "127.0.0.1:8765"] + sys.argv[1:]
import app as _app
raise SystemExit(_app.main())
"@ | Set-Content -Encoding utf8 $wrapper
    $Entry = $wrapper
    # PyInstaller still needs app.py + packages from repo root on pathex:
    # add --paths $Root via amending $common below.
}

$DistDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
$OutName = "SecretKit"
$WorkPath = Join-Path $Stage "pyi-work"
$DistPyi = Join-Path $Stage "pyi-dist"

$windowedArgs = @()
if (-not $Console) { $windowedArgs += "--windowed" }

$common = @(
    "--noconfirm",
    "--clean",
    "--paths", $Root,
    "--onedir",
    "--name", $OutName,
    "--distpath", $DistPyi,
    "--workpath", $WorkPath,
    "--specpath", $Stage,
    "--collect-all", "webview",
    "--hidden-import", "webview.platforms.edgechromium",
    "--hidden-import", "ecdsa",
    "--add-data", "ui;ui",
    "--add-data", "engine;engine",
    "--add-data", "VERSION;.",
    "--exclude-module", "objc",
    "--exclude-module", "AppKit",
    "--exclude-module", "WebKit",
    "--exclude-module", "Cocoa",
    "--exclude-module", "Quartz"
) + $windowedArgs

Write-Host "Running PyInstaller (onedir)…"
& $VenvPy -m PyInstaller @common $Entry
if ($LASTEXITCODE -ne 0) { Die "PyInstaller onedir failed" }

$BuiltDir = Join-Path $DistPyi $OutName
if (-not (Test-Path (Join-Path $BuiltDir "$OutName.exe"))) {
    Die "expected $BuiltDir\$OutName.exe missing"
}

$FinalDir = Join-Path $DistDir $OutName
if (Test-Path $FinalDir) { Remove-Item -Recurse -Force $FinalDir }
Copy-Item -Recurse $BuiltDir $FinalDir

# README for recipients (no secrets)
$readmeOut = Join-Path $FinalDir "README-WINDOWS.txt"
@"
Secret Kit $Version (Windows portable)

- Double-click SecretKit.exe (needs Microsoft Edge WebView2 Evergreen Runtime).
- If the window fails to open: install WebView2 Evergreen Bootstrapper from Microsoft, then retry.
- Optional browser UI: SecretKit.exe --http 127.0.0.1:8765
- Nothing is saved to disk. Closing the window forgets secrets.
- Do not bind 0.0.0.0. Do not upload this build to a public site.
"@ | Set-Content -Encoding ascii $readmeOut

function Write-Sha256([string] $FilePath) {
    $hash = (Get-FileHash -Algorithm SHA256 -Path $FilePath).Hash.ToLower()
    $base = Split-Path $FilePath -Leaf
    $sidecar = "$FilePath.sha256"
    Set-Content -Encoding ascii -Path $sidecar -Value "$hash  $base"
    return $hash
}

$ZipOut = ""
if ($SkipZip) {
    Write-Host ""
    Write-Host "SKIP_ZIP — zip/checksum not written."
}
else {
    $ZipOut = Join-Path $DistDir "secret-kit-$Version-windows-$ArchTag.zip"
    Write-Host "Zipping → $ZipOut"
    if (Test-Path $ZipOut) { Remove-Item -Force $ZipOut }
    # Compress-Archive includes the SecretKit folder as the root entry
    Compress-Archive -Path $FinalDir -DestinationPath $ZipOut -CompressionLevel Optimal
    $null = Write-Sha256 $ZipOut
    Write-Host "  checksum: $ZipOut.sha256"
}

if ($OneFile) {
    Write-Host "Also building experimental onefile…"
    $oneDist = Join-Path $Stage "pyi-one"
    $oneWork = Join-Path $Stage "pyi-one-work"
    $oneArgs = @(
        "--noconfirm", "--clean", "--paths", $Root, "--onefile",
        "--name", $OutName,
        "--distpath", $oneDist,
        "--workpath", $oneWork,
        "--specpath", $Stage,
        "--collect-all", "webview",
        "--hidden-import", "webview.platforms.edgechromium",
        "--hidden-import", "ecdsa",
        "--add-data", "ui;ui",
        "--add-data", "engine;engine",
        "--add-data", "VERSION;.",
        "--exclude-module", "objc",
        "--exclude-module", "AppKit"
    ) + $windowedArgs
    & $VenvPy -m PyInstaller @oneArgs $Entry
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "onefile build failed (onedir zip is still the supported artifact)"
    }
    else {
        $oneExe = Join-Path $oneDist "$OutName.exe"
        $destExe = Join-Path $DistDir "secret-kit-$Version-windows-$ArchTag.exe"
        Copy-Item $oneExe $destExe -Force
        $null = Write-Sha256 $destExe
        Write-Host "  onefile: $destExe"
    }
}

Write-Host ""
Write-Host "Done."
Write-Host "  app folder: $FinalDir"
if ($ZipOut) {
    Write-Host "  artifact:  $ZipOut"
    Write-Host "  checksum:  $ZipOut.sha256"
}
Write-Host ""
Write-Host "Launch (this Windows host):  $FinalDir\$OutName.exe"
Write-Host "HTTP fallback:     $FinalDir\$OutName.exe --http 127.0.0.1:8765"
Write-Host ""
Write-Host "WebView2: if the native window fails, install Microsoft Evergreen WebView2 Runtime."
Write-Host "Air-gap: copy the .zip + .sha256; verify SHA-256; unzip; run SecretKit.exe."
Write-Host "Do NOT Authenticode-sign/upload without a code-signing cert on the build host and explicit approval."
Write-Host ""
Write-Host "NOTE: This script was authored cross-platform and marked UNTESTED until run on Windows."
