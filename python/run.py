"""Entry point for the Hexapod Inverse Kinematics & Workspace Calculator.

Run from source with:   python run.py
"""
import sys
import time


def main():
    import os
    # Persistent matplotlib cache dir for frozen builds, so the (slow) font cache
    # is built ONCE and reused, instead of being rebuilt into a fresh one-file
    # temp folder on every launch.
    if getattr(sys, "frozen", False):
        try:
            import tempfile
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~") or tempfile.gettempdir()
            mpldir = os.path.join(base, "HexapodCalculator", "mpl-cache")
            os.makedirs(mpldir, exist_ok=True)
            os.environ["MPLCONFIGDIR"] = mpldir
        except Exception:
            pass

    # High-DPI friendliness before the QApplication is created.
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon

    from hexapod import _startup_log as slog
    slog.start()
    slog.log("main() begin")

    # Native (bootloader) splash screen.  In a one-file build this image is
    # already on screen - shown by the C bootloader before Python even starts -
    # which is what removes the blank wait while the exe unpacks.  We just drive
    # its status text and close it once the window is ready.  It's absent when
    # running from source or when HEXAPOD_SPLASH=0.
    try:
        import pyi_splash                      # injected by the PyInstaller splash
    except Exception:
        pyi_splash = None
    slog.log(f"native splash: {'present' if pyi_splash else 'absent'}")

    # Windows: give the process an explicit AppUserModelID *before* the first
    # window is created so the taskbar shows the app's own icon (and groups its
    # windows under it) instead of the generic Python interpreter icon.
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "ca.uvic.hexapod-calculator")
        except Exception:
            pass

    app = QApplication(sys.argv)

    # App-wide icon so every window (main, dialogs, message boxes, 3D views)
    # shows it.
    from hexapod import config
    ipath = config.icon_path()
    if ipath:
        app.setWindowIcon(QIcon(ipath))

    # Compact UI font: the platform's native UI font at 8 pt (Segoe UI on
    # Windows, San Francisco on macOS, the system default on Linux) - keeps
    # labels/buttons from looking oversized and helps text fit the boxes.
    _f = app.font()
    _f.setPointSize(8)
    app.setFont(_f)

    # Qt splash: only when there is NO native splash (running from source, or the
    # native splash was disabled), so we never stack two splash windows.  When the
    # native splash is present it stays up and we just update its text.
    splash = None
    if pyi_splash is None:
        from hexapod.splash import SplashScreen
        splash = SplashScreen(ipath)
        splash.show()
        app.processEvents()
    splash_t0 = time.monotonic()

    def set_status(text):
        slog.log(f"status: {text}")
        if pyi_splash is not None:
            try:
                pyi_splash.update_text(str(text))
            except Exception:
                pass
        if splash is not None:
            splash.set_status(text)
        app.processEvents()

    def cancelled():
        app.processEvents()
        return bool(splash is not None and splash.cancelled)

    set_status("Loading components\u2026")
    if cancelled():
        return

    # Try to load the optional fast C kernel (falls back to the vectorised
    # NumPy kernel, which is already much faster than the MATLAB MEX build).
    try:
        from hexapod import kinematics
        set_status("Loading kinematics\u2026")
        kinematics.load_c_kernel(verbose=True)
    except Exception as exc:        # pragma: no cover
        print(f"(kernel probe skipped: {exc})")
    if cancelled():
        return

    set_status("Loading 3D / interface modules\u2026")
    slog.log("importing main_window (pulls in matplotlib / pyvista / vtk)")
    from hexapod.main_window import HexapodMainWindow
    slog.log("main_window imported")
    if cancelled():
        return

    # Pre-build matplotlib's font cache now, behind a clear message.  The first
    # time matplotlib renders text it scans every installed font; on a fresh
    # build/machine that can take 30-90 s and would otherwise look like a freeze
    # at "Building interface".  Doing it here (once; the cache above is
    # persistent) keeps the user informed and speeds up every later launch.
    set_status("Preparing fonts (first run may take a minute)\u2026")
    slog.log("building/loading matplotlib font cache")
    try:
        import matplotlib.font_manager  # noqa: F401  (import builds/loads the cache)
    except Exception as exc:
        slog.log(f"font cache step raised (non-fatal): {exc}")
    slog.log("font cache ready")
    if cancelled():
        return

    set_status("Building interface\u2026")
    slog.log("constructing HexapodMainWindow ...")
    win = HexapodMainWindow(status_cb=set_status)
    slog.log("HexapodMainWindow constructed")
    if cancelled():
        win.close()
        return

    set_status("Ready.")

    # If we're showing our OWN Qt splash (source run), keep it up for a minimum
    # dwell so it doesn't just flash by.  With the native splash there's no need -
    # the logo has already been visible throughout unpacking - so we skip the
    # wait and go straight to the window.
    if splash is not None:
        MIN_SPLASH_SEC = 2.5
        while time.monotonic() - splash_t0 < MIN_SPLASH_SEC:
            app.processEvents()
            if getattr(splash, "cancelled", False):
                break
            time.sleep(0.02)

    if pyi_splash is not None:
        try:
            pyi_splash.close()
        except Exception:
            pass
    win.show()
    if splash is not None:
        splash.finish(win)
    slog.log("window shown - entering event loop")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
