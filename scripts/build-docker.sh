#!/usr/bin/env bash
# Build Secret Kit Docker image locally and (optionally) write an air-gap tarball.
# Never pushes to a registry. macOS bash 3.2+ / Linux bash.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

usage() {
  cat <<'USAGE'
Usage: bash scripts/build-docker.sh [VERSION] [--skip-save]

  VERSION     Image/artifact version (default: $VERSION env, else VERSION file, else 0.1.0-dev)
  --skip-save Build and tag only; do not write dist/*.tar.gz

Environment:
  VERSION     Same as positional VERSION
  SKIP_SAVE=1 Same as --skip-save

Builds:
  secret-kit:local
  secret-kit:<VERSION>   (when VERSION is set / resolved)

Writes (unless --skip-save):
  dist/secret-kit-<VERSION>-docker.tar.gz
  dist/secret-kit-<VERSION>-docker.tar.gz.sha256

Never runs docker push / podman push / registry login.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

# Refuse anything that looks like a push / registry handoff.
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --push|push|--publish|publish)
      die "refusing '$arg' — never push secret-kit to a registry (see RELEASE.md / PACKAGING.md)"
      ;;
  esac
done

SKIP_SAVE=${SKIP_SAVE:-0}
POS_VERSION=""
for arg in "$@"; do
  case "$arg" in
    --skip-save)
      SKIP_SAVE=1
      ;;
    -h|--help)
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
  : # keep env VERSION
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

docker_engine() {
  # Prefer Podman when both exist (FOSS; matches RELEASE/PACKAGING guidance).
  if [ -n "${CONTAINER_ENGINE:-}" ]; then
    echo "$CONTAINER_ENGINE"
  elif command -v podman >/dev/null 2>&1; then
    echo podman
  elif command -v docker >/dev/null 2>&1; then
    echo docker
  else
    echo ""
  fi
}

ENGINE=$(docker_engine)
[ -n "$ENGINE" ] || die "docker/podman not found — install Docker Desktop, OrbStack, or Podman, then re-run"

write_sha256() {
  # $1 = file path; writes $1.sha256 in "HASH  basename" form (portable macOS/Linux)
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

echo "Building secret-kit:local and secret-kit:${VERSION} with ${ENGINE}…"
"$ENGINE" build -t secret-kit:local -t "secret-kit:${VERSION}" .

if [ "$SKIP_SAVE" = "1" ]; then
  echo
  echo "SKIP_SAVE=1 — image tagged; air-gap tarball not written."
  echo "Run without --skip-save to produce:"
  echo "  dist/secret-kit-${VERSION}-docker.tar.gz"
  echo "  dist/secret-kit-${VERSION}-docker.tar.gz.sha256"
  exit 0
fi

mkdir -p "$ROOT/dist"
OUT="$ROOT/dist/secret-kit-${VERSION}-docker.tar.gz"
echo "Saving air-gap artifact → ${OUT}"
# Prefer the local tag in the tarball so docker load yields secret-kit:local;
# version tag is also included for freeze-time naming.
"$ENGINE" save secret-kit:local "secret-kit:${VERSION}" | gzip -c > "$OUT"
write_sha256 "$OUT"

echo
echo "Done."
echo "  image:    secret-kit:local  and  secret-kit:${VERSION}"
echo "  artifact: $OUT"
echo "  checksum: ${OUT}.sha256"
echo
echo "Air-gap handoff (offline machine):"
echo "  gzip -dc secret-kit-${VERSION}-docker.tar.gz | docker load"
echo "  docker run --rm --read-only --tmpfs /tmp -p 127.0.0.1:8765:8765 secret-kit:local"
echo "  # or: docker compose up"
echo
echo "Do NOT docker push / podman push this image to any registry."
