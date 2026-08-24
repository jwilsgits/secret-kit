# Build Secret Kit — Windows portable (WebView2)

**Status: recipe-ready / not-yet built on a macOS host.**  
A native Windows `.exe` cannot be produced reliably from macOS (arm64).  
Wine is **not** a reliable path for pywebview + Edge WebView2.  
Windows containers on Mac/Podman are **not** a thing for this GUI stack.

You need a **Windows 10/11** machine or VM (**x64** preferred; arm64 Windows is OK if you name the artifact accordingly) with:

- Python **3.11 or 3.12** x64 (3.9+ works; prefer 3.11/3.12 for current PyInstaller wheels)
- `pip` / venv
- Network once to install deps (or a pre-filled wheel cache you control)
- **Microsoft Edge WebView2 Runtime** (Evergreen) — usually present on Win11 and updated Win10

Do **not** publish this repo to public GitHub for CI. If you automate builds, use a **private/local Windows runner** (or Origin / internal CI you control) — never push Secret Kit to a public registry or public GitHub as a distribution channel.

---

## Why PyInstaller (not Briefcase / custom launcher)

| Option | Verdict for v1 |
| --- | --- |
| **PyInstaller onedir → zip** | **Chosen.** FOSS; embeds CPython so recipients need no Python; pywebview has a Windows PyInstaller hook; matches “portable zip folder” DoD. |
| PyInstaller onefile | Optional; slower cold start; sometimes flaky with WebView2 assets. Prefer onedir zip for v1. |
| Briefcase (BeeWare) | Heavier toolchain; more moving parts than we need for one window + loopback fallback. |
| Custom folder + host Python (like current macOS `.app`) | Worse UX on Windows; recipients should not need a Python install. |
| Cross-build from macOS / Wine | **Blocked.** No trustworthy WebView2 runtime under Wine; no useful Windows GUI containers on macOS. |

---

## Prerequisites (build PC)

1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/windows/) (check “Add python.exe to PATH”).
2. Confirm:

   ```powershell
   python --version
   python -c "import sys; print(sys.platform, sys.maxsize > 2**32)"
   ```

3. **WebView2 Evergreen Runtime** (build *and* run machines):

   - Most Win10/11 boxes already have it (ships with Edge / Windows Update).
   - If missing, install the **Evergreen Bootstrapper** from Microsoft’s WebView2 page  
     (`MicrosoftEdgeWebview2Setup.exe` — Evergreen, not Fixed Version unless you have a reason).
   - The portable app does **not** bundle the runtime (keeps the zip small; matches Evergreen updates). Document for recipients: if the window fails to open with a WebView2 error, run the Evergreen bootstrapper once (admin may be required on locked-down images).

4. Clone/copy this repo onto the Windows box (USB / private share). Do not put it on public GitHub.

---

## One-shot build (recommended)

From an elevated-or-normal PowerShell in the repo root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build-windows.ps1
# or pin version:
.\scripts\build-windows.ps1 -Version 0.1.0
```

**Untested on a real Windows host as of the recipe date** — script written to mirror `scripts/build-macos.sh` / `build-docker.sh` quality; run and fix locally if needed.

### What it writes

Under `dist\`:

| Artifact | Notes |
| --- | --- |
| `SecretKit\` | Onedir folder: `SecretKit.exe` + deps |
| `secret-kit-<VERSION>-windows-x64.zip` | Portable handoff (folder zipped) |
| `secret-kit-<VERSION>-windows-x64.zip.sha256` | SHA-256 sidecar (`HASH  filename`) |

Arch tag is `x64` or `arm64` from the build host (`windows-arm64` if you build on WoA).

Optional flags:

```powershell
.\scripts\build-windows.ps1 -SkipZip          # folder only
.\scripts\build-windows.ps1 -OneFile          # also try a single .exe (experimental)
.\scripts\build-windows.ps1 -Console         # show console for debugging
.\scripts\build-windows.ps1 -HttpFallback    # bake default --http 127.0.0.1:8765 (not recommended)
```

Window mode (pywebview → Edge WebView2) is the **default**. HTTP loopback remains available at runtime:

```powershell
.\dist\SecretKit\SecretKit.exe --http 127.0.0.1:8765
```

Air-gap rules unchanged: nothing saved; if using HTTP, bind loopback only.

---

## Manual recipe (if you prefer not to run the script)

```powershell
cd <repo-root>
python -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Windows-appropriate pins (skips macOS pyobjc*):
python -m pip install -r requirements-desktop-windows.txt
python -m pip install "pyinstaller>=6.3,<7"
python -m pip install -r requirements-engine.txt  # already via -r above

# Clean previous
Remove-Item -Recurse -Force build, dist\SecretKit -ErrorAction SilentlyContinue

pyinstaller `
  --noconfirm --clean --windowed --onedir `
  --name SecretKit `
  --collect-all webview `
  --hidden-import webview.platforms.edgechromium `
  --hidden-import ecdsa `
  --add-data "ui;ui" `
  --add-data "engine;engine" `
  --add-data "VERSION;." `
  --exclude-module objc `
  --exclude-module AppKit `
  app.py

$ver = (Get-Content VERSION -Raw).Trim()
$zip = "dist\secret-kit-$ver-windows-x64.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "dist\SecretKit" -DestinationPath $zip
Get-FileHash $zip -Algorithm SHA256 |
  ForEach-Object { "$($_.Hash.ToLower())  $(Split-Path $zip -Leaf)" } |
  Set-Content -Encoding ascii "$zip.sha256"
```

Notes:

- `--add-data` on Windows uses **`;`** as the path separator (not `:`).
- Do **not** `pip install -r requirements-desktop.txt` on Windows — that file pulls **pyobjc\*** for macOS and will fail or confuse the environment.
- Use `requirements-desktop-windows.txt` (engine + `pywebview==5.3.2` only).

Optional: `scripts/secret-kit-windows.spec` is a starting point if you outgrow the CLI flags; keep it in sync with the script.

---

## Smoke test (on the Windows build/run box)

1. Verify checksum:  
   `(Get-FileHash dist\secret-kit-*-windows-*.zip -Algorithm SHA256).Hash`
2. Unzip to a temp folder (or run `dist\SecretKit\SecretKit.exe` directly).
3. Double-click `SecretKit.exe` — native window should open (WebView2).
4. Generate a password / key; confirm Reveal / Copy; wait ~60s and confirm clipboard clear policy still holds.
5. Close the window — secrets must be gone (no vault files under `%APPDATA%` / the unzip dir beyond the app payload).
6. Optional HTTP path:  
   `.\SecretKit.exe --http 127.0.0.1:8765` → open `http://127.0.0.1:8765` in a browser. Do **not** bind `0.0.0.0`.
7. If the UI fails with a WebView2 / Edge error: install Evergreen Runtime bootstrapper, reboot if required, retry.

---

## Air-gap handoff

1. Copy `secret-kit-<VERSION>-windows-<arch>.zip` **and** `.sha256` via USB / private share you control.
2. Offline PC: verify SHA-256, unzip, run `SecretKit\SecretKit.exe`.
3. Recipients still need **WebView2 Evergreen** on the OS (not bundled). Point them at Microsoft’s bootstrapper if missing.
4. Do **not** upload the zip to a public download site or public GitHub Releases.

---

## Authenticode (optional later — like Mac notarization)

**Status: not required for v1 pocket builds; blocked until a code-signing cert exists.**

When you have an Authenticode cert (org store / USB token — **never** commit the PFX or password):

```powershell
# Example only — use your real thumbprint / timestamp URL
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  /sha1 <THUMBPRINT> dist\SecretKit\SecretKit.exe
signtool verify /pa dist\SecretKit\SecretKit.exe
```

Then re-zip and refresh the `.sha256` sidecar. SmartScreen reputation still accumulates over time; a fresh cert may show “unknown publisher” until reputation builds — same class of problem as Gatekeeper without notarization.

`build-windows.ps1` **refuses** `-Sign` / upload-style switches until you deliberately extend it with a local, non-repo cert workflow.

---

## Blockers / non-goals

- **Cannot** finish a real `.exe` from a macOS host alone — need Windows 10/11 x64 (or arm64) VM/hardware.
- **Wine**: unsuitable for WebView2 / Edge Chromium backend.
- **Podman/Docker on Mac**: Linux (or theoretical Windows) containers do not give you a shippable Win32 GUI + WebView2 artifact here.
- **Public GitHub Actions `windows-latest`**: README forbids putting this project on public GitHub. Prefer a local Windows VM, private runner, or internal CI (Origin, etc.) with a private checkout.
- No MSI / installer required for v1 (portable zip is enough).
- No secrets, member data, or signing keys in docs or the zip.

---

## Related

- Definition of done: `RELEASE.md` → Windows portable
- Packaging overview: `PACKAGING.md` → Windows section
- Mac analogue: `scripts/build-macos.sh` + `PACKAGING.md` (macOS app bundle)
- Engine/UI entry: `app.py` (window default; `--http 127.0.0.1:8765` fallback)
