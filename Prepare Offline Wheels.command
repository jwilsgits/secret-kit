#!/bin/bash
# Run this once on a networked Mac. It fills vendor/ so an offline Mac can install.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required."
  read -r _
  exit 1
fi
mkdir -p vendor
echo "Downloading wheels into vendor/…"
python3 -m pip download -r requirements.txt -d vendor
echo
echo "Done. Copy this whole folder to the offline Mac, then double-click Start Secret Kit.command."
read -r _
