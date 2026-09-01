# Packaging Secret Kit

Multi-platform pocket-executable order, cadence, and definition of done: **[RELEASE.md](RELEASE.md)**.

After a feature change, rebuild every platform this machine can:

```bash
bash scripts/build-all.sh
# or: bash scripts/build-all.sh 0.1.0
```

That runs tests, then Docker / AppImage / macOS / Windows scripts as the host allows, then `scripts/checksums.sh`. Handoff `dist/secret-kit-<VERSION>-*`. Do not registry-push.

Same engine, two ways to show the UI:

- **Desktop window** (macOS): `python3 app.py` needs `requirements-desktop.txt`
- **Loopback HTTP** (containers, LXC, browsers): `python3 app.py --http 127.0.0.1:8765` needs only `requirements-engine.txt`

Do not bind `0.0.0.0` on a host you care about. Do not push the image to a registry.

## HTTP mode (any OS with Python)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-engine.txt
.venv/bin/python app.py --http 127.0.0.1:8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Closing the tab forgets secrets. File-folder hashing still needs a real filesystem (desktop app or LXC); single-file checksum in the browser uses an upload.

## Docker / OrbStack / Podman

OrbStack on macOS and Docker Desktop behave the same. On Linux, Podman is the usual equivalent.

```bash
docker build -t secret-kit:local .
docker run --rm --read-only --tmpfs /tmp \
  -p 127.0.0.1:8765:8765 \
  secret-kit:local
```

Or: `docker compose up --build`

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). The process inside the container listens on all interfaces; **the publish address is loopback on the host**.

Podman:

```bash
podman build -t secret-kit:local .
podman run --rm --read-only --tmpfs /tmp \
  -p 127.0.0.1:8765:8765 \
  secret-kit:local
```

### Air-gap copy of the image

Preferred (versioned artifact + SHA-256 sidecar):

```bash
bash scripts/build-docker.sh
# or: VERSION=0.1.0 bash scripts/build-docker.sh
# or: bash scripts/build-docker.sh 0.1.0
```

Writes `dist/secret-kit-<VERSION>-docker.tar.gz` and `.sha256` (VERSION from arg, `$VERSION`, `VERSION` file, or `0.1.0-dev`). Build-only: `bash scripts/build-docker.sh --skip-save`.

Manual equivalent:

```bash
docker save secret-kit:local | gzip > dist/secret-kit-<VERSION>-docker.tar.gz
# then record SHA-256 next to the file
```

On the offline machine:

```bash
gzip -dc secret-kit-<VERSION>-docker.tar.gz | docker load
docker run --rm --read-only --tmpfs /tmp -p 127.0.0.1:8765:8765 secret-kit:local
```

Do not `docker push` this image.

## LXC (no Docker)

Copy this folder into the guest. Then:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-engine.txt
.venv/bin/python app.py --http 127.0.0.1:8765
```

From the host, forward loopback:

```bash
ssh -L 8765:127.0.0.1:8765 user@guest
```

or, with Incus/LXC:

```bash
incus exec <name> -- python3 /path/to/app.py --http 127.0.0.1:8765
incus config device add <name> sk proxy listen=tcp:127.0.0.1:8765 connect=tcp:127.0.0.1:8765
```

Browse [http://127.0.0.1:8765](http://127.0.0.1:8765) on the host.

## AppImage (Linux desktop)

One file for a Linux desktop. It bundles CPython 3.12 and `ecdsa`, then serves the same loopback UI and opens the browser. It is not a native window (no WebKitGTK).

On macOS (prefer **Podman**; Docker / OrbStack also work). Start the Podman machine first if needed, then:

```bash
bash scripts/build-appimage.sh
```

The script re-execs inside `debian:bookworm-slim` for the target arch (`linux/amd64` by default). Override the engine with `CONTAINER_ENGINE=podman` or `CONTAINER_ENGINE=docker` if both are installed. On Apple Silicon building `x86_64`, packing may fall back to the type2 runtime + `mksquashfs` when `appimagetool` cannot exec under QEMU — that is expected and still produces a normal AppImage.

If the build host has no container runtime, a Linux machine can build it from the git bundle instead (needs `curl` and `squashfs-tools`):

```bash
git clone secret-kit.bundle secret-kit
cd secret-kit
bash scripts/build-appimage.sh
```

On Linux x86_64, the same command builds natively. ARM laptops:

```bash
APPIMAGE_ARCH=aarch64 bash scripts/build-appimage.sh
```

Output (script default): `dist/SecretKit-x86_64.AppImage` (about 25–35 MB) plus `dist/SecretKit-x86_64.AppImage.sha256`. For release handoff you may also copy/rename to the versioned form in RELEASE.md (`secret-kit-<VERSION>-linux-<arch>.AppImage`). Send the AppImage (and checksum). They run:

```bash
chmod +x SecretKit-x86_64.AppImage
./SecretKit-x86_64.AppImage
```

If FUSE is missing: `./SecretKit-x86_64.AppImage --appimage-extract-and-run`. Close the status dialog (or kill the process) to stop. Nothing is saved.

Do not put GPU stacks, OpenStack, or a public registry in the AppImage.

## macOS app bundle (pocket)

Double-clickable `Secret Kit.app` with embedded engine, UI, and desktop deps (pywebview window). No PyPI at first run. Build host and launch Mac need **Python 3.9** (Apple Command Line Tools) because desktop pins are `pywebview==5.3.2` / `pyobjc*==11.1` (cp39 wheels).

### Build

On macOS (networked once to fill `vendor/`, or already filled):

```bash
bash scripts/build-macos.sh
# or: VERSION=0.1.0 bash scripts/build-macos.sh
# or: bash scripts/build-macos.sh 0.1.0
```

Writes:

- `dist/Secret Kit.app`
- `dist/secret-kit-<VERSION>-macos-<arch>.zip` (arch is `arm64` or `x86_64`)
- `dist/secret-kit-<VERSION>-macos-<arch>.zip.sha256`

App-only (no zip): `bash scripts/build-macos.sh --skip-zip`.

Window mode is the default. HTTP loopback as the baked-in launch is opt-in only: `--http-fallback` (not recommended for handoff).

Developer / source path without the `.app` remains `Start Secret Kit.command` and `Prepare Offline Wheels.command`.

### Launch

```bash
open "dist/Secret Kit.app"
# or:
"dist/Secret Kit.app/Contents/MacOS/SecretKit"
```

### Air-gap copy / Gatekeeper

1. Copy the `.zip` and `.sha256` (USB / private share you control).
2. On the offline Mac: `shasum -a 256 -c secret-kit-<VERSION>-macos-<arch>.zip.sha256`
3. Unzip (Archive Utility or `ditto -x -k …`).
4. If Gatekeeper blocks an **ad-hoc / unsigned** build: right-click the `.app` → **Open** → confirm once. Or clear quarantine after you trust the checksum: `xattr -dr com.apple.quarantine "Secret Kit.app"`.
5. Still needs Python 3.9 on that Mac (CLT). The bundle does not embed a full CPython yet.

Do not publish the zip to a public download site.

### Notarization checklist (Developer ID)

**Status on a machine with no signing certs: blocked on identity.** Confirm with:

```bash
security find-identity -v -p codesigning
```

You need a line like `Developer ID Application: <Your Name/Org> (<TEAMID>)`. Apple Developer Program membership required. This repo's build script **never** uploads to Apple.

When an identity exists (run by hand, with explicit approval — do not put secrets or API keys in the repo):

1. **Sign** (replace identity string; prefer a secure timestamp):

   ```bash
   codesign --force --deep --options runtime \
     --sign "Developer ID Application: <Name> (<TEAMID>)" \
     "dist/Secret Kit.app"
   codesign --verify --verbose=2 "dist/Secret Kit.app"
   ```

2. **Package** for notarization (zip the signed app):

   ```bash
   ditto -c -k --keepParent "dist/Secret Kit.app" /tmp/secret-kit-notarize.zip
   ```

3. **Notarize** (App Store Connect API key or equivalent credentials stored in the keychain — not in git):

   ```bash
   xcrun notarytool submit /tmp/secret-kit-notarize.zip \
     --keychain-profile "<YOUR_NOTARY_PROFILE>" \
     --wait
   ```

4. **Staple** and spot-check:

   ```bash
   xcrun stapler staple "dist/Secret Kit.app"
   spctl --assess --type execute -vv "dist/Secret Kit.app"
   ```

5. Re-zip the stapled `.app` for handoff and refresh the `.sha256` sidecar.

Until step 0 (identity) is satisfied, ship the ad-hoc build and Gatekeeper notes above. Do **not** run `notarytool` / `altool` upload without an explicit go-ahead and certs on the build host.

## Windows portable (WebView2)

**Status: recipe-ready / not-yet built.** No native `.exe` has been produced from a macOS build host. Build on a Windows 10/11 x64 (or arm64) machine or VM. Wine is not a reliable path for pywebview + WebView2. Windows containers on Mac are not usable for this GUI artifact.

Native window via **pywebview → Edge WebView2** (same `app.py` engine). Portable **onedir zip** for v1 (no MSI). CPython is embedded by PyInstaller; recipients still need the **WebView2 Evergreen Runtime** on the OS (usually already present on Win11 / updated Win10).

### Build (on Windows)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build-windows.ps1
# or: .\scripts\build-windows.ps1 -Version 0.1.0
```

Full recipe, smoke tests, Authenticode notes: **[scripts/build-windows.md](scripts/build-windows.md)**.

Deps: install **`requirements-desktop-windows.txt`** (engine + `pywebview==5.3.2`). Do **not** use `requirements-desktop.txt` on Windows — it pulls macOS-only `pyobjc*`.

Writes:

- `dist\SecretKit\SecretKit.exe` (onedir)
- `dist\secret-kit-<VERSION>-windows-x64.zip` (or `windows-arm64`)
- matching `.sha256` sidecar

Window mode is the default. HTTP loopback opt-in at runtime: `SecretKit.exe --http 127.0.0.1:8765` (never `0.0.0.0` on a host you care about). Optional `-HttpFallback` bakes HTTP as default (not recommended for handoff).

### WebView2 missing

If the window fails to open, install Microsoft’s **WebView2 Evergreen Bootstrapper**, then retry. The portable zip does **not** bundle the runtime.

### Air-gap copy

1. Copy the `.zip` and `.sha256` (USB / private share you control).
2. Verify SHA-256; unzip; run `SecretKit\SecretKit.exe`.
3. Nothing is saved. Closing the window forgets secrets.

Do not publish the zip to a public download site or public GitHub Releases. Authenticode signing is optional later (see `scripts/build-windows.md`) — same class of “blocked on identity” as Mac notarization.

## What not to do

- `--http 0.0.0.0:8765` on a laptop or member workstation
- `docker run -p 8765:8765` without `127.0.0.1:` (that publishes on all host interfaces)
- Pushing `secret-kit` to Docker Hub / GHCR
- Putting member secrets in a volume
