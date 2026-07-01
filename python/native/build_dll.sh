#!/usr/bin/env bash
# Build the standalone kernel shared library from MATLAB Coder C sources.
# Place the regenerated standalone *.c files in this folder first (see README.md).
set -e
SRC=$(ls *.c 2>/dev/null || true)
if [ -z "$SRC" ]; then echo "No .c files here. See README.md."; exit 1; fi

UNAME=$(uname -s)
if [ "$UNAME" = "Darwin" ]; then
  OUT=libstew_inverse_ws.dylib
  cc -O2 -dynamiclib -o "$OUT" $SRC
else
  OUT=libstew_inverse_ws.so
  cc -O2 -fPIC -shared -o "$OUT" $SRC
fi
echo "Built $OUT — the app will load it automatically."
