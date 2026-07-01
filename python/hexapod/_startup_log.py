"""Tiny append-only startup log.

Frozen GUI apps are hard to debug because a windowed (.exe) build has no console,
so if startup stalls there's nothing to look at.  This writes a handful of
timestamped lines to a predictable file as the program starts up, so if it ever
hangs you can just open the log and see the last step it reached.

Location (first that works):
    %LOCALAPPDATA%\\HexapodCalculator\\startup.log   (Windows)
    ~/.HexapodCalculator/startup.log                (macOS / Linux)
    <temp dir>/HexapodCalculator-startup.log        (fallback)

Override with the HEXAPOD_LOG environment variable.
"""
import os
import sys
import time
import tempfile

_LOG_PATH = None


def _default_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    try:
        d = os.path.join(base, "HexapodCalculator")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "startup.log")
    except Exception:
        return os.path.join(tempfile.gettempdir(), "HexapodCalculator-startup.log")


def start():
    """Begin a fresh log for this launch."""
    global _LOG_PATH
    _LOG_PATH = os.environ.get("HEXAPOD_LOG") or _default_path()
    try:
        with open(_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("=== Hexapod Calculator startup log ===\n")
            f.write(f"time      : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"frozen    : {getattr(sys, 'frozen', False)}\n")
            f.write(f"python    : {sys.version.split()[0]}\n")
            f.write(f"executable: {sys.executable}\n")
            f.write(f"argv0     : {sys.argv[0] if sys.argv else ''}\n")
            f.write(f"cwd       : {os.getcwd()}\n")
            f.write("-" * 40 + "\n")
    except Exception:
        _LOG_PATH = None


def log(msg):
    """Append one timestamped line (never raises)."""
    if _LOG_PATH is None:
        return
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            f.flush()
    except Exception:
        pass


def path():
    return _LOG_PATH
