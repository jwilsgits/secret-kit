#!/usr/bin/env bash
# Rebuild every pocket target this host can produce. Run after a feature lands.
# Never pushes to a registry. macOS bash 3.2+ / Linux bash.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

usage() {
  cat <<'USAGE'
Usage: bash scripts/build-all.sh [VERSION] [--skip-tests] [--only LIST]

  VERSION       default: $VERSION env, else VERSION file, else 0.1.0-dev
  --skip-tests  do not run python3 -m unittest first
  --only LIST   comma list: docker,appimage,macos,windows
                default: all targets this OS can build

After feature work:
  # optionally bump VERSION
  bash scripts/build-all.sh
  # hand off dist/secret-kit-<VERSION>-* (USB / private share you control)

Never docker/podman push. Never GitHub Releases.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

SKIP_TESTS=${SKIP_TESTS:-0}
ONLY=""
POS_VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --skip-tests)
      SKIP_TESTS=1
      ;;
    --only)
      shift
      ONLY=${1:-}
      [ -n "$ONLY" ] || die "--only requires a value (example: --only docker,macos)"
      ;;
    --only=*)
      ONLY=${1#--only=}
      ;;
    --push|push|--publish|publish)
      die "refusing '$1' — never push secret-kit to a registry (see RELEASE.md)"
      ;;
    -*)
      die "unknown option: $1 (try --help)"
      ;;
    *)
      if [ -n "$POS_VERSION" ]; then
        die "unexpected extra argument: $1"
      fi
      POS_VERSION=$1
      ;;
  esac
  shift
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
export VERSION

want() {
  local name=$1
  if [ -z "$ONLY" ]; then
    return 0
  fi
  case ",$ONLY," in
    *",$name,"*) return 0 ;;
    *) return 1 ;;
  esac
}

HOST=$(uname -s)
BUILT=""
SKIPPED=""
FAILED=""

note_skip() {
  SKIPPED="${SKIPPED} $1"
  echo "skip: $1 — $2"
}

note_built() {
  BUILT="${BUILT} $1"
}

note_fail() {
  FAILED="${FAILED} $1"
}

if [ "$SKIP_TESTS" != "1" ]; then
  echo "Running tests…"
  python3 -m unittest discover -s tests -v
fi

if want docker; then
  if command -v podman >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
    echo "=== docker ==="
    if bash "$ROOT/scripts/build-docker.sh" "$VERSION"; then
      note_built docker
    else
      note_fail docker
    fi
  else
    note_skip docker "no podman/docker on PATH"
  fi
fi

if want appimage; then
  if [ "$HOST" = Linux ] || command -v podman >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
    echo "=== appimage ==="
    ARCH=${APPIMAGE_ARCH:-x86_64}
    if bash "$ROOT/scripts/build-appimage.sh"; then
      SRC="$ROOT/dist/SecretKit-${ARCH}.AppImage"
      DST="$ROOT/dist/secret-kit-${VERSION}-linux-${ARCH}.AppImage"
      if [ -f "$SRC" ]; then
        cp "$SRC" "$DST"
        if command -v sha256sum >/dev/null 2>&1; then
          (cd "$ROOT/dist" && sha256sum "$(basename "$DST")") > "${DST}.sha256"
        elif command -v shasum >/dev/null 2>&1; then
          (cd "$ROOT/dist" && shasum -a 256 "$(basename "$DST")") > "${DST}.sha256"
        fi
      fi
      note_built appimage
    else
      note_fail appimage
    fi
  else
    note_skip appimage "need Linux or a container engine"
  fi
fi

if want macos; then
  if [ "$HOST" = Darwin ]; then
    echo "=== macos ==="
    if bash "$ROOT/scripts/build-macos.sh" "$VERSION"; then
      note_built macos
    else
      note_fail macos
    fi
  else
    note_skip macos "not Darwin"
  fi
fi

if want windows; then
  case "$HOST" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "=== windows ==="
      if command -v pwsh >/dev/null 2>&1; then
        PS=pwsh
      else
        PS=powershell.exe
      fi
      if "$PS" -File "$ROOT/scripts/build-windows.ps1" "$VERSION"; then
        note_built windows
      else
        note_fail windows
      fi
      ;;
    *)
      note_skip windows "run scripts/build-windows.ps1 on Windows 10/11 (see scripts/build-windows.md)"
      ;;
  esac
fi

echo
if [ -n "$BUILT" ]; then
  echo "=== checksums ==="
  bash "$ROOT/scripts/checksums.sh" "$VERSION"
fi

echo
echo "VERSION=$VERSION"
echo "built:  ${BUILT:- (none)}"
echo "skip:   ${SKIPPED:- (none)}"
echo "failed: ${FAILED:- (none)}"
echo
echo "Handoff: copy dist/secret-kit-${VERSION}-* via USB or a share you control."
echo "Do NOT docker push / publish to GitHub Releases."

[ -z "$FAILED" ] || exit 1
[ -n "$BUILT" ] || [ -n "$SKIPPED" ] || die "nothing selected"
# Succeed if we built something, or only skipped (e.g. --only windows on macOS).
if [ -z "$BUILT" ]; then
  echo "warning: no artifacts built on this host" >&2
  exit 2
fi
exit 0
