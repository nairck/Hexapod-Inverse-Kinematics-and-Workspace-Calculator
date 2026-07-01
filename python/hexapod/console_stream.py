"""Mirror everything printed to stdout/stderr into the GUI.

The original MATLAB tool printed status to the MATLAB console with disp()/fprintf
(e.g. "configuration saved...", "quitting...", "working on reachable
workspace...", elapsed-time and limit summaries).  In this port every such
message is a normal print(), and this module tees stdout/stderr so the text
appears in BOTH a scrollable console window and a 3-line status bar, while still
going to the real terminal.
"""
from __future__ import annotations
import sys
from PySide6.QtCore import QObject, Signal


class StreamEmitter(QObject):
    """Carries text from any thread to the GUI thread via a queued signal."""
    text = Signal(str)


class TeeStream:
    """File-like object: forwards writes to the real stream AND to a signal."""

    def __init__(self, real_stream, emitter: StreamEmitter):
        self._real = real_stream
        self._emitter = emitter

    def write(self, s):
        if self._real is not None:
            try:
                self._real.write(s)
            except Exception:
                pass
        if s:
            self._emitter.text.emit(s)

    def flush(self):
        if self._real is not None:
            try:
                self._real.flush()
            except Exception:
                pass

    # so libraries that probe these don't choke
    def isatty(self):
        return False

    def fileno(self):
        if self._real is not None and hasattr(self._real, "fileno"):
            return self._real.fileno()
        raise OSError("no fileno")


def install(emitter: StreamEmitter):
    """Redirect stdout and stderr through the emitter. Returns a restore fn."""
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = TeeStream(old_out, emitter)
    sys.stderr = TeeStream(old_err, emitter)

    def restore():
        sys.stdout, sys.stderr = old_out, old_err

    return restore
