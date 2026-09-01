#!/usr/bin/env bash
# Write dist/secret-kit-<VERSION>-SHA256SUMS for versioned artifacts.
# macOS bash 3.2+ / Linux bash. Never uploads.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

die() {
  echo "error: $*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: bash scripts/checksums.sh [VERSION]

  VERSION   default: $VERSION env, else VERSION file, else 0.1.0-dev

Writes:
  dist/secret-kit-<VERSION>-SHA256SUMS

Hashes every dist/secret-kit-<VERSION>-* file except *.sha256 and the SUMS file itself.
USAGE
}

POS_VERSION=""
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --push|push|--publish|publish)
      die "refusing '$arg' — checksums stay local (see RELEASE.md)"
      ;;
    -*)
      die "unknown option: $arg (try --help)"
      ;;
    *)
      [ -z "$POS_VERSION" ] || die "unexpected extra argument: $arg"
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

mkdir -p "$ROOT/dist"
OUT="$ROOT/dist/secret-kit-${VERSION}-SHA256SUMS"
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

found=0
# shellcheck disable=SC2045
for f in "$ROOT/dist"/secret-kit-"${VERSION}"-*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  case "$base" in
    *.sha256|*-SHA256SUMS) continue ;;
  esac
  [ -f "$f" ] || continue
  found=1
  if command -v sha256sum >/dev/null 2>&1; then
    (cd "$ROOT/dist" && sha256sum "$base") >> "$TMP"
  elif command -v shasum >/dev/null 2>&1; then
    (cd "$ROOT/dist" && shasum -a 256 "$base") >> "$TMP"
  else
    die "need sha256sum or shasum"
  fi
done

[ "$found" = 1 ] || die "no dist/secret-kit-${VERSION}-* artifacts to hash"

sort -k2 "$TMP" > "$OUT"
echo "Wrote $OUT"
cat "$OUT"
