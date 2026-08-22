#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required."
  read -r _
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Creating local virtualenv…"
  python3 -m venv .venv || { echo "Could not create .venv"; read -r _; exit 1; }
  if ls vendor/*.whl >/dev/null 2>&1; then
    .venv/bin/pip install --no-index --find-links vendor -r requirements.txt || {
      echo "Offline wheel install failed. On a networked Mac run Prepare Offline Wheels.command first."
      read -r _
      exit 1
    }
  else
    .venv/bin/pip install -r requirements.txt || {
      echo "pip install failed."
      read -r _
      exit 1
    }
  fi
fi

exec .venv/bin/python app.py
