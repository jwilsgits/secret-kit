#!/usr/bin/env bash
# Build Secret Kit as a double-clickable macOS .app (window mode via pywebview).
# Embeds engine + UI + desktop deps (no PyPI at first run). Uses host Python 3.9
# at launch (Apple CLT / matching 3.9). Ad-hoc codesign by default.
# Developer ID + notarization: see PACKAGING.md — blocked until an identity exists.
# Never uploads to Apple. macOS bash 3.2+.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

usage() {
  cat <<'USAGE'
Usage: bash scripts/build-macos.sh [VERSION] [--skip-zip] [--http-fallback]

  VERSION          Artifact version (default: $VERSION env, else VERSION file, else 0.1.0-dev)
  --skip-zip       Build .app under dist/ only; do not write the zip + .sha256
  --http-fallback  Bundle default launch as --http 127.0.0.1:8765 (not recommended;
                   window mode is the default and preferred)

Environment:
  VERSION          Same as positional VERSION
  SKIP_ZIP=1       Same as --skip-zip
  PYTHON           Python 3.9 interpreter used to stage site-packages (default: python3)

Writes:
  dist/Secret Kit.app
  dist/secret-kit-<VERSION>-macos-<arch>.zip   (unless --skip-zip)
  dist/secret-kit-<VERSION>-macos-<arch>.zip.sha256

Does NOT notarize or upload to Apple. Ad-hoc signs with codesign -s - when available.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

SKIP_ZIP=${SKIP_ZIP:-0}
HTTP_FALLBACK=0
POS_VERSION=""
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --skip-zip)
      SKIP_ZIP=1
      ;;
    --http-fallback)
      HTTP_FALLBACK=1
      ;;
    --notarize|--sign-developer-id|--upload)
      die "refusing '$arg' — notarization/upload needs a Developer ID on the build host and explicit approval; see PACKAGING.md"
      ;;
    -*)
      die "unknown option: $arg (try --help)"
      ;;
    *)
      if [ -n "$POS_VERSION" ]; then
        die "unexpected extra argument: $arg"
      fi
      POS_VERSION=$arg
      ;;
  esac
done

if [ -n "$POS_VERSION" ]; then
  VERSION=$POS_VERSION
elif [ -n "${VERSION:-}" ]; then
  :
elif [ -f "$ROOT/VERSION" ]; then
  VERSION=$(tr -d '[:space:]' < "$ROOT/VERSION")
else
  VERSION=0.1.0-dev
fi

[ -n "$VERSION" ] || die "VERSION is empty"
case "$VERSION" in
  */*|*..*|*' '*|*$'\t'*)
    die "VERSION looks unsafe: $VERSION"
    ;;
esac

ARCH=$(uname -m)
case "$ARCH" in
  arm64|x86_64) ;;
  *) die "unsupported arch: $ARCH" ;;
esac

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null 2>&1 || die "Python not found ($PY). Install Apple CLT Python 3.9+."

"$PY" - <<'PY' || die "build host needs Python 3.9 (pinned pyobjc 11.1 / pywebview 5.3.2 wheels are cp39)"
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)
PY

ensure_vendor() {
  if ls "$ROOT"/vendor/*.whl >/dev/null 2>&1; then
    echo "Using existing vendor/ wheels."
    return 0
  fi
  echo "vendor/ has no wheels — downloading with pip (networked macOS host)…"
  mkdir -p "$ROOT/vendor"
  "$PY" -m pip download -r "$ROOT/requirements.txt" -d "$ROOT/vendor"
}

write_sha256() {
  local file=$1
  local base
  base=$(basename "$file")
  local hash
  if command -v sha256sum >/dev/null 2>&1; then
    hash=$(sha256sum "$file" | awk '{print $1}')
  elif command -v shasum >/dev/null 2>&1; then
    hash=$(shasum -a 256 "$file" | awk '{print $1}')
  else
    die "need sha256sum or shasum to write checksum sidecar"
  fi
  printf '%s  %s\n' "$hash" "$base" > "${file}.sha256"
}

APP_NAME="Secret Kit.app"
STAGE_ROOT="$ROOT/build/macos"
STAGE="$STAGE_ROOT/$APP_NAME"
DIST_APP="$ROOT/dist/$APP_NAME"

echo "Building macOS app bundle (${ARCH}) version ${VERSION}…"
rm -rf "$STAGE_ROOT"
mkdir -p "$STAGE/Contents/MacOS" \
         "$STAGE/Contents/Resources/app" \
         "$STAGE/Contents/Resources/site-packages"

# --- app payload (engine + UI + entry) ---
cp "$ROOT/app.py" "$STAGE/Contents/Resources/app/app.py"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' \
    "$ROOT/engine/" "$STAGE/Contents/Resources/app/engine/"
  rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' \
    "$ROOT/ui/" "$STAGE/Contents/Resources/app/ui/"
else
  cp -R "$ROOT/engine" "$STAGE/Contents/Resources/app/engine"
  cp -R "$ROOT/ui" "$STAGE/Contents/Resources/app/ui"
  find "$STAGE/Contents/Resources/app" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
fi
printf '%s\n' "$VERSION" > "$STAGE/Contents/Resources/app/VERSION"

ensure_vendor

echo "Installing desktop deps into bundle site-packages (offline from vendor/)…"
"$PY" -m pip install --upgrade --no-compile --no-warn-script-location \
  --no-index --find-links "$ROOT/vendor" \
  -r "$ROOT/requirements.txt" \
  -t "$STAGE/Contents/Resources/site-packages"
rm -rf "$STAGE/Contents/Resources/site-packages"/pip* \
       "$STAGE/Contents/Resources/site-packages"/setuptools* \
       "$STAGE/Contents/Resources/site-packages"/pkg_resources* \
       "$STAGE/Contents/Resources/site-packages"/_distutils_hack \
       "$STAGE/Contents/Resources/site-packages"/distutils-precedence.pth \
       2>/dev/null || true

# --- Info.plist ---
cat > "$STAGE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>SecretKit</string>
  <key>CFBundleIdentifier</key>
  <string>local.secretkit.app</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>Secret Kit</string>
  <key>CFBundleDisplayName</key>
  <string>Secret Kit</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>${VERSION}</string>
  <key>CFBundleVersion</key>
  <string>${VERSION}</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>CFBundleDocumentTypes</key>
  <array/>
</dict>
</plist>
PLIST

# --- launcher (window mode default; optional HTTP) ---
if [ "$HTTP_FALLBACK" = "1" ]; then
  LAUNCH_ARGS='--http 127.0.0.1:8765'
else
  LAUNCH_ARGS=''
fi

cat > "$STAGE/Contents/MacOS/SecretKit" <<LAUNCH
#!/bin/bash
# Secret Kit macOS launcher — window mode (pywebview) unless --http was baked in.
set -euo pipefail
CONTENTS="\$(cd "\$(dirname "\$0")/.." && pwd)"
APP_HOME="\$CONTENTS/Resources/app"
SITE="\$CONTENTS/Resources/site-packages"
export PYTHONPATH="\$SITE\${PYTHONPATH:+:\$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

pick_python() {
  local c
  for c in python3.9 python3; do
    if command -v "\$c" >/dev/null 2>&1; then
      if "\$c" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 9) else 1)' 2>/dev/null; then
        echo "\$c"
        return 0
      fi
    fi
  done
  return 1
}

PY_BIN="\$(pick_python)" || {
  echo "Secret Kit: need Python 3.9 on PATH (Apple Command Line Tools)." >&2
  echo "Pinned desktop wheels (pyobjc 11.1 / pywebview 5.3.2) are cp39." >&2
  exit 1
}

cd "\$APP_HOME"
exec "\$PY_BIN" "\$APP_HOME/app.py" ${LAUNCH_ARGS} "\$@"
LAUNCH
chmod +x "$STAGE/Contents/MacOS/SecretKit"

printf 'APPL????' > "$STAGE/Contents/PkgInfo"

# --- ad-hoc sign (no Developer ID required) ---
SIGN_STATUS="unsigned"
if command -v codesign >/dev/null 2>&1; then
  echo "Ad-hoc codesigning (identity '-')…"
  if codesign --force --deep --sign - "$STAGE" 2>/dev/null; then
    SIGN_STATUS="ad-hoc"
  else
    echo "warning: codesign ad-hoc failed; leaving unsigned" >&2
  fi
else
  echo "warning: codesign not found; leaving unsigned" >&2
fi

echo
# Do not print `security find-identity` output — it can include personal names / Team IDs.
ID_OUT=$(security find-identity -v -p codesigning 2>/dev/null || true)
if echo "$ID_OUT" | grep -q "Developer ID Application"; then
  NOTARY_NOTE="identity available — follow PACKAGING.md checklist (not run by this script)"
else
  NOTARY_NOTE="blocked on identity — no Developer ID Application cert in keychain"
fi

mkdir -p "$ROOT/dist"
rm -rf "$DIST_APP"
ditto "$STAGE" "$DIST_APP"

echo
echo "App bundle: $DIST_APP"
echo "  sign:     $SIGN_STATUS"
echo "  notarize: $NOTARY_NOTE"
du -sh "$DIST_APP" || true

ZIP_OUT=""
if [ "$SKIP_ZIP" = "1" ]; then
  echo
  echo "SKIP_ZIP=1 — zip/checksum not written."
else
  ZIP_OUT="$ROOT/dist/secret-kit-${VERSION}-macos-${ARCH}.zip"
  echo "Zipping → $ZIP_OUT"
  rm -f "$ZIP_OUT"
  ditto -c -k --keepParent "$DIST_APP" "$ZIP_OUT"
  write_sha256 "$ZIP_OUT"
  echo "  checksum: ${ZIP_OUT}.sha256"
  ls -lh "$ZIP_OUT" "${ZIP_OUT}.sha256"
fi

echo
echo "Done."
echo "  app:      $DIST_APP"
if [ -n "$ZIP_OUT" ]; then
  echo "  artifact: $ZIP_OUT"
  echo "  checksum: ${ZIP_OUT}.sha256"
fi
echo
echo "Launch (this macOS host):  open \"$DIST_APP\""
echo "Or:                 \"$DIST_APP/Contents/MacOS/SecretKit\""
echo
echo "Air-gap recipient: copy the .zip + .sha256; verify SHA-256; unzip; right-click Open"
echo "once if Gatekeeper blocks (ad-hoc / unsigned). Full notarization needs Developer ID."
echo
echo "Do NOT run notarytool upload without a Developer ID on the build host and explicit approval."
