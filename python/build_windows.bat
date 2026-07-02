@echo off
REM ============================================================
REM  Build the single-file Windows .exe
REM  Run this in a Command Prompt. Uses the "py" launcher, which
REM  is what a standard python.org install puts on your system.
REM ============================================================

echo [1/4] Creating virtual environment...
py -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
REM After activation, "python" is the venv's interpreter (even if only the "py"
REM launcher is on PATH globally), so deps install into the venv, not globally.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo [3/4] Building executable with PyInstaller...
python -m PyInstaller --clean --noconfirm hexapod.spec

echo [4/4] Done.
echo.
echo Your program is here:  dist\HexapodCalculator.exe
echo (Copy formdata.txt next to the .exe to start from your saved settings.)
pause
