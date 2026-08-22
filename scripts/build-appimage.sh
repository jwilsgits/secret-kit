#!/usr/bin/env bash
# Build a Linux AppImage: bundled CPython + ecdsa + Secret Kit, loopback HTTP UI.
# On Linux this runs natively. On macOS it re-execs inside Docker/Podman.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
ARCH=${APPIMAGE_ARCH:-x86_64}
PY_TAG=20260814
PY_VER=3.12.14
PY_TRIPLE="${ARCH}-unknown-linux-gnu"
PY_TAR="cpython-${PY_VER}+${PY_TAG}-${PY_TRIPLE}-install_only_stripped.tar.gz"
PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_TAG}/${PY_TAR}"
TOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"

case "$ARCH" in
  x86_64)
    PY_SHA256=5acfa3e9ba26b51ae161c83aff278da915b590d22373a424b2ba55b8afe91fcc
    DOCKER_PLATFORM=linux/amd64
    ;;
  aarch64)
    PY_SHA256=2d8e17dfd732102cfeb18e0e1fa6769b24caa034e159981129590fe409c7157a
    DOCKER_PLATFORM=linux/arm64
    ;;
  *)
    echo "Unsupported APPIMAGE_ARCH=$ARCH (use x86_64 or aarch64)" >&2
    exit 1
    ;;
esac

docker_engine() {
  if command -v docker >/dev/null 2>&1; then
    echo docker
  elif command -v podman >/dev/null 2>&1; then
    echo podman
  else
    echo ""
  fi
}

if [ "${1:-}" != "--in-container" ]; then
  host=$(uname -s)
  machine=$(uname -m)
  if [ "$host" != "Linux" ] || [ "$machine" != "$ARCH" ]; then
    engine=$(docker_engine)
    if [ -z "$engine" ]; then
      echo "AppImage builds need Linux ($ARCH)." >&2
      echo "On this Mac, start Docker / OrbStack / Podman and re-run:" >&2
      echo "  bash scripts/build-appimage.sh" >&2
      exit 1
    fi
    echo "Building $ARCH AppImage in $engine ($DOCKER_PLATFORM)…"
    exec "$engine" run --rm --platform "$DOCKER_PLATFORM" \
      -v "$ROOT:/src" -w /src \
      debian:bookworm-slim \
      bash /src/scripts/build-appimage.sh --in-container
  fi
fi

if [ "$(uname -s)" != "Linux" ]; then
  echo "Inner build must run on Linux." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
if ! command -v curl >/dev/null 2>&1 || ! command -v mksquashfs >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl file squashfs-tools
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

echo "Downloading relocatable CPython ${PY_VER}…"
curl -fsSL -o python.tgz "$PY_URL"
echo "${PY_SHA256}  python.tgz" | sha256sum -c -
tar -xzf python.tgz

APPDIR="$WORK/SecretKit.AppDir"
mkdir -p "$APPDIR/usr" "$APPDIR/opt/secret-kit"
cp -a python/. "$APPDIR/usr/"
PY="$APPDIR/usr/bin/python3"

echo "Installing engine (ecdsa)…"
"$PY" -m pip install --no-compile --disable-pip-version-check -q -r "$ROOT/requirements-engine.txt"

echo "Copying Secret Kit…"
cp "$ROOT/app.py" "$APPDIR/opt/secret-kit/"
cp -R "$ROOT/engine" "$ROOT/ui" "$ROOT/data" "$APPDIR/opt/secret-kit/"
find "$APPDIR/opt/secret-kit" -type d -name __pycache__ -print0 | xargs -0r rm -rf

cp "$ROOT/scripts/appimage/AppRun" "$APPDIR/AppRun"
cp "$ROOT/scripts/appimage/secret-kit.desktop" "$APPDIR/secret-kit.desktop"
chmod +x "$APPDIR/AppRun"

export APPDIR
"$PY" - <<'PY'
import os, struct, zlib
from pathlib import Path

w = h = 256
bg, ink = (0xF4, 0xF1, 0xEA), (0x2B, 0x26, 0x1F)
rows = []
for y in range(h):
    row = bytearray()
    for x in range(w):
        dx, dy = x - 128, y - 128
        rgb = ink if dx * dx + dy * dy <= 62 * 62 else bg
        row.extend(rgb)
    rows.append(b"\x00" + bytes(row))

def chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

png = (
    b"\x89PNG\r\n\x1a\n"
    + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    + chunk(b"IEND", b"")
)
appdir = Path(os.environ["APPDIR"])
(appdir / "secret-kit.png").write_bytes(png)
(appdir / ".DirIcon").write_bytes(png)
PY

rm -rf "$APPDIR/usr/lib/python3.12/ensurepip" \
       "$APPDIR/usr/lib/python3.12/test" \
       "$APPDIR"/usr/lib/python3.12/site-packages/pip \
       "$APPDIR"/usr/lib/python3.12/site-packages/pip-*.dist-info \
       "$APPDIR"/usr/lib/python3.12/site-packages/setuptools* \
       "$APPDIR/usr/share"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp "$APPDIR/secret-kit.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/secret-kit.png"

echo "Packing AppImage…"
curl -fsSL -o appimagetool "$TOOL_URL"
chmod +x appimagetool
mkdir -p "$ROOT/dist"
OUT="$ROOT/dist/SecretKit-${ARCH}.AppImage"
ARCH="$ARCH" APPIMAGE_EXTRACT_AND_RUN=1 ./appimagetool \
  --no-appstream "$APPDIR" "$OUT"

chmod +x "$OUT"
ls -lh "$OUT"
echo "AppImage: $OUT"
