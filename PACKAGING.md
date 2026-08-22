# Packaging Secret Kit

Same engine, two ways to show the UI:

- **Desktop window** (this Mac): `python3 app.py` needs `requirements-desktop.txt`
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

On a networked machine:

```bash
docker save secret-kit:local | gzip > secret-kit.tar.gz
```

On the offline machine:

```bash
gzip -dc secret-kit.tar.gz | docker load
docker run --rm --read-only --tmpfs /tmp -p 127.0.0.1:8765:8765 secret-kit:local
```

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

One file for a friend’s Linux laptop. It bundles CPython 3.12 and `ecdsa`, then serves the same loopback UI and opens the browser. It is not a native window (no WebKitGTK).

On this Mac (Docker / OrbStack / Podman):

```bash
bash scripts/build-appimage.sh
```

If this Mac has no container runtime, the Linux laptop can build it from the git bundle instead (needs `curl` and `squashfs-tools`):

```bash
git clone secret-kit.bundle secret-kit
cd secret-kit
bash scripts/build-appimage.sh
```

On Linux x86_64, the same command builds natively. ARM laptops:

```bash
APPIMAGE_ARCH=aarch64 bash scripts/build-appimage.sh
```

Output: `dist/SecretKit-x86_64.AppImage` (about 25–35 MB). Send that file. They run:

```bash
chmod +x SecretKit-x86_64.AppImage
./SecretKit-x86_64.AppImage
```

If FUSE is missing: `./SecretKit-x86_64.AppImage --appimage-extract-and-run`. Close the status dialog (or kill the process) to stop. Nothing is saved.

Do not put GPU stacks, OpenStack, or a public registry in the AppImage.

## What not to do

- `--http 0.0.0.0:8765` on a laptop or member workstation
- `docker run -p 8765:8765` without `127.0.0.1:` (that publishes on all host interfaces)
- Pushing `secret-kit` to Docker Hub / GHCR
- Putting member secrets in a volume
