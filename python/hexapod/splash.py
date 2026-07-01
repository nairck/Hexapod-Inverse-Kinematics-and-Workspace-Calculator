"""A lightweight, instant-loading splash screen.

This module deliberately imports ONLY PySide6 (no matplotlib / pyvista / vtk) so
it can be shown immediately on startup - before the heavy modules load - giving
the user feedback that the program is opening.  It shows the logo, a title, a
live status line, and a small "X" button to cancel loading and quit early.
"""
from __future__ import annotations
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QApplication

from . import config

SIZE = 500
LOGO = 380


class SplashScreen(QWidget):
    def __init__(self, icon_path=None):
        super().__init__(None)
        self.cancelled = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setFixedSize(SIZE, SIZE)
        self.setObjectName("splash")
        # a clean card look (frameless, so we draw our own background + border)
        self.setStyleSheet(
            "#splash{background-color:#ffffff; border:1px solid #c8c8c8;}"
            "QLabel{background:transparent;}"
        )
        # icon_path is only used for the taskbar/window icon - NOT the logo image.
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Title (top)
        self.title = QLabel("Hexapod Calculator", self)
        self.title.setGeometry(20, 14, SIZE - 70, 26)
        self.title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        f = self.title.font(); f.setPointSize(12); f.setBold(True); self.title.setFont(f)
        self.title.setStyleSheet("color:#7a1020; background:transparent;")

        self.subtitle = QLabel("Inverse Kinematics & Workspace Solver", self)
        self.subtitle.setGeometry(20, 42, SIZE - 40, 18)
        self.subtitle.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        sf = self.subtitle.font(); sf.setPointSize(9); self.subtitle.setFont(sf)
        self.subtitle.setStyleSheet("color:#555555; background:transparent;")

        # Logo (centre) - ALWAYS the high-resolution splash.png, scaled DOWN with
        # smooth filtering so it stays crisp (never upscaled from the small icon).
        self.logo = QLabel(self)
        self.logo.setGeometry((SIZE - LOGO) // 2, 66, LOGO, LOGO)
        self.logo.setAlignment(Qt.AlignCenter)
        logo_path = config.resource_path("assets", "splash.png")
        if not (logo_path and os.path.exists(logo_path)):
            logo_path = config.resource_path("splash.png")
        pix = QPixmap(logo_path) if logo_path and os.path.exists(logo_path) else QPixmap()
        if not pix.isNull():
            self.logo.setPixmap(pix.scaled(LOGO, LOGO, Qt.KeepAspectRatio,
                                           Qt.SmoothTransformation))

        # Status (bottom)
        self.status = QLabel("Starting up\u2026", self)
        self.status.setGeometry(20, SIZE - 46, SIZE - 40, 22)
        self.status.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        stf = self.status.font(); stf.setPointSize(9); self.status.setFont(stf)
        self.status.setStyleSheet("color:#444444; background:transparent;")

        # "X" cancel button (top-right) - text X with a slightly larger hit box
        self.close_btn = QPushButton("X", self)
        self.close_btn.setGeometry(SIZE - 34, 8, 26, 26)
        bf = self.close_btn.font(); bf.setPointSize(11); bf.setBold(True); self.close_btn.setFont(bf)
        self.close_btn.setStyleSheet(
            "QPushButton{border:none; color:#888888; background:transparent;}"
            "QPushButton:hover{color:#ffffff; background:#c0392b; border-radius:4px;}")
        self.close_btn.setToolTip("Cancel loading and quit")
        self.close_btn.clicked.connect(self._on_cancel)

        self._center_on_screen()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is not None:
            c = screen.availableGeometry().center()
            self.move(c.x() - SIZE // 2, c.y() - SIZE // 2)

    def _on_cancel(self):
        self.cancelled = True
        self.status.setText("Cancelling\u2026")
        QApplication.processEvents()

    # --- API used by run.py ---
    def set_status(self, text):
        self.status.setText(str(text))

    def finish(self, window=None):
        self.close()
