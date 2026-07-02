@echo off
REM Build stew_inverse_ws.dll from the STANDALONE MATLAB Coder C sources.
REM Run in the "x64 Native Tools Command Prompt for VS".
REM Place the regenerated standalone *.c files in this folder first (see README.md).

setlocal EnableDelayedExpansion
set SRC=
for %%f in (*.c) do set SRC=!SRC! %%f

if "!SRC!"=="" (
    echo No .c source files found in this folder. See README.md.
    pause
    exit /b 1
)

echo Compiling:!SRC!
cl /LD /O2 /DNDEBUG !SRC! /Fe:stew_inverse_ws.dll

echo.
echo If successful you now have stew_inverse_ws.dll in this folder.
echo The app will pick it up automatically next time it runs.
pause
