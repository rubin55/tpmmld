#!/usr/bin/env bash

# Some globals.
export ROOT_DIR="$(cd "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 ; pwd -P)"

# Set PYTHONPATH based on where we are.
export PYTHONPATH="$ROOT_DIR/src:$PYTHONPATH"

# Get hostname.
HOSTNAME="$(hostname)"

# Find venv dir if existing.
[[ -e "$ROOT_DIR/.venv/bin/activate" ]] && VENV_DIR="$ROOT_DIR/.venv"
[[ -e "$ROOT_DIR/.venv/$HOSTNAME/bin/activate" ]] && VENV_DIR="$ROOT_DIR/.venv/$HOSTNAME"
[[ -e "$ROOT_DIR/venv/bin/activate" ]] && VENV_DIR="$ROOT_DIR/venv"
[[ -e "$ROOT_DIR/venv/$HOSTNAME/bin/activate" ]] && VENV_DIR="$ROOT_DIR/venv/$HOSTNAME"


# Activate venv if available.
[[ -n "$VENV_DIR" ]] && source "$VENV_DIR/bin/activate"

# Run module.
exec python3 -m tpmmld "$@"
