"""Embedded interactive 3D view of the hexapod (base, platform, legs, axes).

Port of draw_plat.m (static draw) and anim_plat.m (40-step animation).  Rendered
with matplotlib inside Qt so the mouse rotates it just like the MATLAB axes, and
so dashed legs / circular joint markers / axis-arrow labels match the original.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
# Make sure matplotlib's Qt backend binds to PySide6 (what we ship), not some
# other Qt binding that might also be present in the user's environment.
os.environ.setdefault("QT_API", "pyside6")
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from . import config

ARROW_LEN = 150.0
LINE_W = 2.0
N_STEPS = 40                       # animation frames (matches anim_plat.m)
SKETCH_ZOOM = 1.5                  # default magnification of the embedded sketch
DEFAULT_AZIM = -120.0              # MATLAB view([-30,20]) -> matplotlib azim = az-90
DEFAULT_ELEV = 20.0
BASE_EDGES = [(1, 2), (3, 4), (5, 0)]                       # 0-indexed (MATLAB 2-3,4-5,6-1)
PLAT_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]


class PlatformView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fig = Figure(figsize=(3.5, 3.5))
        self.canvas = FigureCanvas(self.fig)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)

        # Transparent background so the plot blends into the window instead of
        # sitting in an opaque white box that covers the controls behind it.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.canvas.setAttribute(Qt.WA_TranslucentBackground, True)
        self.canvas.setAutoFillBackground(False)
        self.canvas.setStyleSheet("background: transparent;")

        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_axis_off()
        # MATLAB view([-30,20]) -> matplotlib azim = az-90 = -120, elev = 20.
        self.ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
        self._fg = "black"          # axis-arrow / label colour (white in dark themes)
        self._apply_transparency()

        self._base = np.zeros((6, 3))
        self._plat = np.zeros((6, 3))
        self._leg_lines = []
        self._plat_lines = []
        self._base_lines = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._anim_tick)
        self._anim_start = None
        self._anim_end = None
        self._anim_i = 0
        self._first = True

    # ------------------------------------------------------------------
    def _apply_transparency(self):
        """Keep the figure/axes backgrounds fully transparent (must be re-applied
        after every ax.cla(), which resets the axes facecolor to white)."""
        self.fig.patch.set_facecolor("none")
        self.fig.patch.set_alpha(0.0)
        self.ax.patch.set_facecolor("none")
        self.ax.patch.set_alpha(0.0)
        try:
            for axis in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                axis.pane.set_alpha(0.0)
                axis.pane.fill = False
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _set_equal_aspect(self, pts):
        lo = pts.min(axis=0)
        hi = pts.max(axis=0)
        ctr = 0.5 * (lo + hi)
        rng = float(np.max(hi - lo)) * 0.5 + 1e-6
        self.ax.set_xlim(ctr[0] - rng, ctr[0] + rng)
        self.ax.set_ylim(ctr[1] - rng, ctr[1] + rng)
        self.ax.set_zlim(ctr[2] - rng, ctr[2] + rng)
        # zoom>1 enlarges the drawn content without changing the data limits (so
        # nothing is clipped).  Re-applied on every draw_static, so it survives
        # theme-change redraws.
        try:
            self.ax.set_box_aspect((1, 1, 1), zoom=SKETCH_ZOOM)
        except TypeError:                 # older matplotlib without the zoom kwarg
            try:
                self.ax.set_box_aspect((1, 1, 1))
            except Exception:
                pass
        except Exception:
            pass

    def _draw_axes_arrows(self):
        a = ARROW_LEN
        c = self._fg
        self.ax.plot([0, 0], [0, 0], [0, a], "-", color=c, lw=1)
        self.ax.plot([0, 0], [0, a], [0, 0], "-", color=c, lw=1)
        self.ax.plot([0, a], [0, 0], [0, 0], "-", color=c, lw=1)
        self.ax.scatter([0, 0, a], [0, a, 0], [a, 0, 0], c=c, marker="^", s=12)
        self.ax.text(0, 0, a, "Z", fontsize=8, ha="center", va="bottom", color=c)
        self.ax.text(0, a, 0, "Y", fontsize=8, ha="center", va="bottom", color=c)
        self.ax.text(a, 0, 0, "X", fontsize=8, ha="center", va="bottom", color=c)

    def set_theme_color(self, color):
        """Set the origin-arrow / XYZ-label colour (e.g. white on a dark theme)
        and redraw so the axes are always readable against the background."""
        color = "white" if str(color).lower() in ("white", "#ffffff", "#fff") else (
                "black" if str(color).lower() in ("black", "#000000", "#000") else color)
        if color == self._fg:
            return
        self._fg = color
        if not self._first:
            self.draw_static(self._base, self._plat)

    def reset_view(self):
        """Reset the embedded sketch to its default view angle + magnification."""
        self._timer.stop()
        self.ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
        if not self._first:
            self.draw_static(self._base, self._plat)   # re-applies default zoom too
        else:
            self.canvas.draw_idle()

    # ------------------------------------------------------------------
    def draw_static(self, base_pts, plat_pts):
        """Full redraw (equivalent to draw_plat.m)."""
        self._timer.stop()
        # Remember the current view angle so a redraw (pose change / theme change)
        # keeps the user's mouse rotation instead of snapping back to default.
        try:
            cur_elev, cur_azim = float(self.ax.elev), float(self.ax.azim)
        except Exception:
            cur_elev, cur_azim = DEFAULT_ELEV, DEFAULT_AZIM
        self._base = np.asarray(base_pts, float)
        self._plat = np.asarray(plat_pts, float)
        self.ax.cla()
        self.ax.set_axis_off()
        self.ax.view_init(elev=cur_elev, azim=cur_azim)
        self._apply_transparency()
        self._draw_axes_arrows()

        # base triangle edges (dark blue)
        self._base_lines = []
        for i1, i2 in BASE_EDGES:
            ln, = self.ax.plot(self._base[[i1, i2], 0], self._base[[i1, i2], 1],
                               self._base[[i1, i2], 2], "-", lw=LINE_W, color=config.BASE_COLOR)
            self._base_lines.append(ln)

        # legs base->platform (first dash-dot, rest solid), coloured
        self._leg_lines = []
        for i in range(6):
            style = "-." if i == 0 else "-"
            ln, = self.ax.plot([self._base[i, 0], self._plat[i, 0]],
                               [self._base[i, 1], self._plat[i, 1]],
                               [self._base[i, 2], self._plat[i, 2]],
                               style, marker="o", ms=3, lw=LINE_W, color=config.LEG_COLORS[i])
            self._leg_lines.append(ln)

        # platform hexagon edges (dark red)
        self._plat_lines = []
        for i1, i2 in PLAT_EDGES:
            ln, = self.ax.plot(self._plat[[i1, i2], 0], self._plat[[i1, i2], 1],
                               self._plat[[i1, i2], 2], "-", lw=LINE_W, color=config.PLAT_COLOR)
            self._plat_lines.append(ln)

        allpts = np.vstack([self._base, self._plat, [[0, 0, 0], [ARROW_LEN, 0, 0],
                            [0, ARROW_LEN, 0], [0, 0, ARROW_LEN]]])
        self._set_equal_aspect(allpts)
        if self._first:
            self._first = False
        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    def update_pose(self, base_pts, plat_pts, animate=True):
        """Move to a new platform pose, animating over N_STEPS frames if asked."""
        base_pts = np.asarray(base_pts, float)
        plat_pts = np.asarray(plat_pts, float)
        if self._first or not self._leg_lines or not animate:
            self.draw_static(base_pts, plat_pts)
            return
        self._base = base_pts
        self._anim_start = self._plat.copy()
        self._anim_end = plat_pts.copy()
        self._anim_i = 0
        self._timer.start(16)        # ~60 fps

    def _anim_tick(self):
        self._anim_i += 1
        t = self._anim_i / N_STEPS
        cur = self._anim_start + (self._anim_end - self._anim_start) * t
        # update legs
        for i, ln in enumerate(self._leg_lines):
            ln.set_data_3d([self._base[i, 0], cur[i, 0]],
                           [self._base[i, 1], cur[i, 1]],
                           [self._base[i, 2], cur[i, 2]])
        # update base edges (base may have moved)
        for (i1, i2), ln in zip(BASE_EDGES, self._base_lines):
            ln.set_data_3d(self._base[[i1, i2], 0], self._base[[i1, i2], 1], self._base[[i1, i2], 2])
        # update platform edges
        for (i1, i2), ln in zip(PLAT_EDGES, self._plat_lines):
            ln.set_data_3d(cur[[i1, i2], 0], cur[[i1, i2], 1], cur[[i1, i2], 2])
        self.canvas.draw_idle()
        if self._anim_i >= N_STEPS:
            self._timer.stop()
            self._plat = self._anim_end.copy()
