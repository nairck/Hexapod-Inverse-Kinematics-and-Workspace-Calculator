"""A lightweight, instant-loading splash screen.

This module deliberately imports ONLY PySide6 (no matplotlib / pyvista / vtk) so
it can be shown immediately on startup - before the heavy modules load - giving
the user feedback that the program is opening.

It displays the splash artwork in ``assets/splash.png`` (which already contains
the title, subtitle and logo), overlays a live status line at the bottom-left,
and a small "X" button to cancel loading and quit early.
"""
from __future__ import annotations
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QApplication

from . import config

# Splash window size. This matches assets/splash_native.png (the image shown by
# the frozen build's bootloader splash), so the two look identical.
SPLASH_W = 540
SPLASH_H = 481


class SplashScreen(QWidget):
    def __init__(self, icon_path=None):
        super().__init__(None)
        self.cancelled = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setFixedSize(SPLASH_W, SPLASH_H)
        self.setObjectName("splash")
        # White fallback in case the artwork can't be found; the image (which has
        # its own border) fills the window on top of it.
        self.setStyleSheet("#splash{background-color:#ffffff;} QLabel{background:transparent;}")
        # icon_path is only used for the taskbar/window icon - NOT the artwork.
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Full splash artwork (title + subtitle + logo are all baked into it).
        # Loaded from the high-resolution PNG and scaled DOWN smoothly so it
        # stays crisp.
        self.image = QLabel(self)
        self.image.setGeometry(0, 0, SPLASH_W, SPLASH_H)
        self.image.setAlignment(Qt.AlignCenter)
        img_path = config.resource_path("assets", "splash.png")
        if not (img_path and os.path.exists(img_path)):
            img_path = config.resource_path("splash.png")
        pix = QPixmap(img_path) if img_path and os.path.exists(img_path) else QPixmap()
        if not pix.isNull():
            self.image.setPixmap(pix.scaled(SPLASH_W, SPLASH_H,
                                            Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Loading/status line: bottom-left, 12 px in from the left edge, sitting
        # in the clear band beneath the logo.
        self.status = QLabel("Starting up\u2026", self)
        self.status.setGeometry(18, SPLASH_H - 38, SPLASH_W - 30, 22)
        self.status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        stf = self.status.font(); stf.setPointSize(9); self.status.setFont(stf)
        self.status.setStyleSheet("color:#3a3a3a; background:transparent;")

        # "X" cancel button (top-right) - text X with a slightly larger hit box.
        self.close_btn = QPushButton("X", self)
        self.close_btn.setGeometry(SPLASH_W - 34, 8, 26, 26)
        bf = self.close_btn.font(); bf.setPointSize(11); bf.setBold(True); self.close_btn.setFont(bf)
        self.close_btn.setStyleSheet(
            "QPushButton{border:none; color:#888888; background:transparent;}"
            "QPushButton:hover{color:#ffffff; background:#c0392b; border-radius:4px;}")
        self.close_btn.setToolTip("Cancel loading and quit")
        self.close_btn.clicked.connect(self._on_cancel)

        # Keep the text and button painted above the artwork.
        self.status.raise_()
        self.close_btn.raise_()

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is not None:
            c = screen.availableGeometry().center()
            self.move(c.x() - SPLASH_W // 2, c.y() - SPLASH_H // 2)

    def _on_cancel(self):
        self.cancelled = True
        self.status.setText("Cancelling\u2026")
        QApplication.processEvents()

    # --- API used by run.py ---
    def set_status(self, text):
        self.status.setText(str(text))

    def finish(self, window=None):
        self.close()
