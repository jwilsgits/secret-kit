# Secret Kit — multi-platform pocket-executable release spine

**Decision (2026-08-22):** Ship packaging first. Feature work waits. Every later enhancement ships a build for every target that is ready; unfinished targets stay listed here as not-yet.

One engine (`engine/` + `app.py`), one UI (`ui/`), four wrappers. Nothing saved. No vault. No network share of this project. Loopback-only on the host. CSPRNG stays in Python (`os.urandom`); optional user entropy cannot replace it.

How-to for each runtime lives in [PACKAGING.md](PACKAGING.md). This file is the **release order and definition of done**.

---

## Strategy

| Priority | Target | Why this order |
| --- | --- | --- |
| 1 | **Docker** (local image + air-gap `docker save`) | Already works; tighten and freeze as the reference loopback HTTP path |
| 2 | **Linux AppImage** | Script + helpers exist; produce and verify the first `dist/` artifact |
| 3 | **macOS** app bundle (+ notarization path) | Today: pywebview + `.command`; next: double-clickable bundle others can run offline |
| 4 | **Windows** portable (`.exe` + WebView2) | Greenfield; same engine/UI, native window via WebView2 |

Docker and AppImage share loopback HTTP. macOS and Windows aim for a native window (same air-gap rules).

---

## Current state vs target (honest)

| Target | Today | Target |
| --- | --- | --- |
| **Docker** | `Dockerfile`, `docker-compose.yml` exist; host publish is `127.0.0.1:8765`; `--read-only` + `/tmp` tmpfs; tag `secret-kit:local` | Documented harden checklist below; versioned air-gap tarball name; no public registry ever |
| **AppImage** | First `dist/SecretKit-x86_64.AppImage` built 2026-08-22 via Podman (`linux/amd64` on Apple Silicon); SHA-256 sidecar present; containerized HTTP smoke OK | Reproducible `dist/SecretKit-<arch>.AppImage` (or versioned name below); full desktop launch smoke-tested on Linux x86_64 (and aarch64 when needed) |
| **macOS** | `scripts/build-macos.sh` → ad-hoc `dist/Secret Kit.app` + versioned zip/SHA-256 (arm64 smoke 2026-08-22); window mode (pywebview); **notarization blocked on identity** (0 Developer ID certs); still needs host Python 3.9; `vendor/` wheels filled on the build host (not a git requirement) | Signed/notarized `.app` (or `.dmg`) that runs without a separate pip install; optional embedded CPython later |
| **Windows** | **Recipe-ready / not-yet built** (`scripts/build-windows.md` + `build-windows.ps1` + `requirements-desktop-windows.txt`); no `.exe` from a macOS host; needs Win10/11 x64/arm64 VM | Portable `secret-kit-<VERSION>-windows-x64.zip` (WebView2); SHA-256; smoke on real Windows |
| **Source / Mac PoC** | Works with pinned `pywebview==5.3.2` / `pyobjc==11.1` | Remains the developer path; pocket builds are what we hand to others |

---

## Definition of done (per target)

### 1. Docker — tighten what exists

**Done when:**

- [x] Image build succeeds from a clean tree (`bash scripts/build-docker.sh` / Podman; tags `secret-kit:local` + version)
- [x] `podman compose up --build` verified (Homebrew `docker-compose` 5.5.0 as Podman compose provider; FOSS Apache-2.0)
- [x] Host bind is always `127.0.0.1:8765:8765` (never bare `8765:8765`) — `docker-compose.yml`
- [x] Container stays `--read-only` with `tmpfs` for `/tmp`; runs as non-root (`nobody`) — compose + Dockerfile
- [x] Air-gap path works: `bash scripts/build-docker.sh` → save → run with same flags (smoke-verified 2026-08-22 via Podman; `docker load` / compose still optional)
- [x] Artifact naming for handoff: `dist/secret-kit-<VERSION>-docker.tar.gz` via `scripts/build-docker.sh` (loads as `secret-kit:local` + optional `secret-kit:<VERSION>`)
- [x] SHA-256 of the `.tar.gz` recorded next to the file (`.sha256` sidecar from the same script)
- [x] **Never** push to Docker Hub / GHCR / any public registry — script refuses `--push`; do not login/push by hand

### 2. Linux AppImage

**Done when:**

- [x] `bash scripts/build-appimage.sh` produces `dist/` output on Mac-via-Podman (verified 2026-08-22); native Linux path is in the same script (not re-run on a Linux host today)
- [ ] App launches loopback UI, opens browser, generates secrets, clears on exit; nothing written under the user’s home for persistence — **partial:** extracted payload serves loopback HTTP 200 inside `podman run --platform linux/amd64` (2026-08-22); full AppImage desktop launch / browser / generate / home-persistence not verifiable on macOS
- [x] FUSE-less fallback documented (`--appimage-extract-and-run`) — already in PACKAGING.md
- [x] No GPU stacks, OpenStack, or registry clients inside the image — audited AppDir site-packages (ecdsa + six only) on 2026-08-22 build
- [x] SHA-256 of the AppImage recorded; arch in the filename (`x86_64` / `aarch64`) — `dist/SecretKit-x86_64.AppImage` + `.sha256`; versioned handoff copy `dist/secret-kit-0.1.0-dev-linux-x86_64.AppImage`

### 3. macOS app bundle + notarization path

**Done when:**

- [x] Double-clickable `.app` (optionally wrapped in `.dmg`) embeds engine + UI + desktop deps; no PyPI at first run — `dist/Secret Kit.app` via `scripts/build-macos.sh` (2026-08-22); embeds site-packages from `vendor/`; still requires host **Python 3.9** (CLT) at launch (CPython not embedded yet); `.dmg` not produced (zip handoff instead)
- [x] Window mode preferred (pywebview or successor); HTTP loopback only if explicitly chosen — default launcher is window mode; `--http-fallback` opt-in only
- [x] Build script path documented (`scripts/build-macos.sh` + PACKAGING.md macOS section)
- [x] **Notarization path** written down: Developer ID sign → notarize → staple — checklist in PACKAGING.md; **blocked on identity** on the build host (`security find-identity -v -p codesigning` → 0 valid identities; ad-hoc sign only)
- [x] SHA-256 of the shipped archive; Gatekeeper-friendly distribution notes for air-gap copy — `dist/secret-kit-<VERSION>-macos-<arch>.zip` + `.sha256`; Gatekeeper / quarantine notes in PACKAGING.md

### 4. Windows portable (`.exe` + WebView2)

**Status: recipe-ready / not-yet built** (2026-08-22). Docs + `scripts/build-windows.ps1` landed from a macOS host; **no Windows binary produced** (cannot cross-build WebView2/pywebview reliably from macOS; Wine unsuitable).

**Done when:**

- [ ] Portable artifact runs without an MSI for v1 (single `.exe` or zip folder) — **blocked:** needs Windows 10/11 build host; recipe targets PyInstaller onedir → `secret-kit-<VERSION>-windows-x64.zip`
- [ ] Native UI via WebView2 (Evergreen runtime note if the machine lacks it) — **docs ready** (`scripts/build-windows.md`); runtime not smoke-tested
- [ ] Same engine behavior; secrets stay in memory; clipboard clear policy unchanged — **unchanged in `app.py`**; verify on Windows after first build
- [x] Build notes / script path documented — `scripts/build-windows.md` + `scripts/build-windows.ps1` (+ `requirements-desktop-windows.txt`, optional `scripts/secret-kit-windows.spec`); script marked **UNTESTED** until run on Windows
- [ ] SHA-256 of the zip/exe — sidecar will be written by `build-windows.ps1` when a Windows build runs

---

## Suggested build order (and why)

1. **Docker** — already the reference HTTP packaging; cheapest to freeze and use for AppImage cross-builds on macOS.
2. **AppImage** — script is present; closing the loop to a real `dist/` artifact proves “one file for Linux.”
3. **macOS bundle** — upgrades the current `.command` / venv story into something shippable; notarization is the long pole, so start the identity/path early.
4. **Windows** — new surface (WebView2); do last so engine/UI stay stable while learning the wrapper.

Do not block Docker/AppImage polish on Apple notarization or a Windows VM.

---

## Release cadence

- **Tag a VERSION** when shipping (see naming below).
- **Build every target that is ready** for that VERSION.
- Targets not ready yet stay in this doc as **not-yet** — do not pretend they shipped.
- After the spine exists: **each feature enhancement** (new tab behavior, new derive path, etc.) gets a rebuild of all ready targets in the same release. No “Mac-only” feature drops once packaging is live.
- Hand off via controlled copy (USB / private share you control). Do **not** publish this repo or images to GitHub/public registries as a distribution channel.

---

## Constraints / non-goals (packaging phase)

From README and PACKAGING — do not weaken these:

- **No vault.** Nothing saved to disk; closing the window/tab forgets secrets.
- **No `0.0.0.0` on a host you care about.** Container may listen on all interfaces *inside*; host publish stays `127.0.0.1`.
- **Do not** `docker run -p 8765:8765` without `127.0.0.1:`.
- **Do not** push `secret-kit` to Docker Hub / GHCR / public registries.
- **Do not** put this project on GitHub or a network share you do not control (README).
- **Do not** put member secrets in a volume.
- **AppImage:** do not pull in GPU stacks, OpenStack, or a public registry.
- **Entropy:** `os.urandom` remains authoritative; optional mouse/dice/card mix-in cannot replace the OS CSPRNG.
- **Clipboard:** clear-after-timeout policy stays.

---

## Explicitly out of scope for this packaging phase

Feature work waits until pocket executables exist for the ready platforms:

- BIP-85 and further derivation schemes
- Descriptor / extra wallet formats beyond what Derive already does
- In-app vault, cloud sync, accounts, telemetry
- Public download site or auto-updater
- Replacing the Python engine with another language
- Native WebKitGTK AppImage window (PACKAGING already: loopback + browser, not a native window)

Track features separately; when one ships, rebuild all ready pocket targets.

---

## Proposed layout

```
scripts/
  build-appimage.sh      # exists — Linux AppImage (Docker/Podman re-exec on macOS)
  appimage/              # exists — AppRun, .desktop
  build-docker.sh        # exists — build, tag, save → dist/secret-kit-<VERSION>-docker.tar.gz (+ .sha256)
  build-macos.sh         # exists — .app + zip + ad-hoc sign; notarize checklist in PACKAGING.md
  build-windows.md       # VM/CI recipe; WebView2 notes
  build-windows.ps1      # exists — PyInstaller onedir zip (UNTESTED on Windows)
  checksums.sh           # optional: SHA-256SUMS for everything in dist/
dist/                    # gitignored — release artifacts only
```

Keep `Start Secret Kit.command` and `Prepare Offline Wheels.command` as the Mac developer / offline-source path until the `.app` replaces that handoff story.

---

## Versioning / artifact naming sketch

Until a formal scheme is tagged in-repo, use calendar or semver **VERSION** strings consistently:

| Artifact | Suggested name |
| --- | --- |
| Docker save | `secret-kit-<VERSION>-docker.tar.gz` |
| AppImage x86_64 | `secret-kit-<VERSION>-linux-x86_64.AppImage` |
| AppImage aarch64 | `secret-kit-<VERSION>-linux-aarch64.AppImage` |
| macOS | `secret-kit-<VERSION>-macos.dmg` (or `.zip` of `.app`) |
| Windows | `secret-kit-<VERSION>-windows-x64.zip` (exe inside) |
| Checksums | `secret-kit-<VERSION>-SHA256SUMS` |

Existing PACKAGING name `SecretKit-x86_64.AppImage` may remain the **build script default**; release handoff can rename/copy to the versioned form above.

Image tag locally: `secret-kit:local` for day-to-day; optional `secret-kit:<VERSION>` at freeze time. Still never push.

---

## Checksums / signing intent

| Layer | Intent |
| --- | --- |
| **SHA-256** | Required for every shipped file in `dist/` (and air-gap docker tarballs) |
| **macOS** | Developer ID application signature + notarization + staple when identity is available |
| **Windows** | Optional Authenticode later; not a blocker for first portable zip |
| **AppImage / Docker tarball** | SHA-256 first; optional detached PGP signature later for recipients who already trust a key |
| **No secrets in artifacts** | Build outputs must not embed mnemonics, keys, or member data |

---

## Quick status legend for future updates

When updating this file after a build, mark each target:

- **ready** — definition of done met; ships every enhancement release
- **partial** — script or docs exist; artifact not yet verified
- **not-yet** — not started

As of 2026-08-22:

- Docker: **partial** (Podman smoke 2026-08-22: build+save+run OK; air-gap tarball + SHA-256 in `dist/`; compose via `podman compose` + brew `docker-compose` 5.5.0 verified same day)
- AppImage: **partial** (first `dist/SecretKit-x86_64.AppImage` via Podman 2026-08-22; HTTP smoke on extracted payload; full Linux desktop AppImage launch still unverified)
- macOS pocket `.app`: **partial** (ad-hoc `dist/Secret Kit.app` + zip/SHA-256 via `scripts/build-macos.sh` 2026-08-22 arm64; window smoke OK; notarization blocked on identity; host Python 3.9 still required)
- Windows: **recipe-ready / not-yet** (`scripts/build-windows.md` + `.ps1` 2026-08-22; no `.exe` until a Windows VM/host build)
