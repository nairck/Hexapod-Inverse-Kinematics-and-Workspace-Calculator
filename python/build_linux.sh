#!/usr/bin/env bash
# ============================================================
#  Build on Linux  ->  dist/HexapodCalculator
#  Needs system OpenGL libs for VTK, e.g.:
#     sudo apt install libgl1 libegl1 libxkbcommon0 libdbus-1-3
# ============================================================
set -e

echo "[1/4] Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "[2/4] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[3/4] Building executable with PyInstaller..."
python -m PyInstaller --clean --noconfirm hexapod.spec

echo "[4/4] Done."
echo
echo "Your program is here:  dist/HexapodCalculator"
echo "(Copy formdata.txt next to it to start from your saved settings.)"
