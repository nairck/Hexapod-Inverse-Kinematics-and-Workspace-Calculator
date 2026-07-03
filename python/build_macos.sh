#!/usr/bin/env bash
# ============================================================
#  Build on macOS  ->  dist/HexapodCalculator.app
#  Requires Python 3.11 or 3.12 (python.org build recommended).
# ============================================================
set -e

echo "[1/4] Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "[2/4] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[3/4] Building app with PyInstaller..."
python -m PyInstaller --clean --noconfirm hexapod.spec

echo "[4/4] Done."
echo
echo "Your app is here:  dist/HexapodCalculator.app"
echo "(First launch: right-click the app -> Open, to get past Gatekeeper.)"
