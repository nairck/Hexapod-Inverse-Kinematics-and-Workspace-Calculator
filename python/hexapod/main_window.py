"""The main application window - a faithful port of MAIN_GUI.m.

Every control is placed at the original MATLAB pixel position (converted from
MATLAB's bottom-left origin via config.m2q), so the geometry is pixel-faithful.
Colours/fonts are cleaned up but the layout matches the original 720x710 window.

Added on top of the MATLAB feature set (as requested): a single Console dock
below the GUI that mirrors everything printed to stdout/stderr.  It is anchored
under the fixed panel (it can't grow up into the GUI) but the window's bottom
edge can be dragged down to extend it, with a scrollbar once it fills.
"""
from __future__ import annotations
import os
import sys
import shutil
import traceback
import numpy as np

from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot, QLocale
from PySide6.QtGui import (
    QDoubleValidator, QFont, QTextCursor, QFontMetrics, QIcon,
    QShortcut, QKeySequence,
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLineEdit, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
)

from . import config
from .config import m2q
from . import settings_io
from . import kinematics
from . import workspace as W
from . import workspace_view
from . import dialogs
from .platform_view import PlatformView
from .console_stream import StreamEmitter, install as install_streams

CYAN = "#CCFFFF"      # MATLAB [.8 1 1]
YELLOW = "#FFFFE6"    # MATLAB [1 1 .9]
WHITE = "#FFFFFF"
GREY = "#F0F0F0"
DISABLED_BG = "#F0F0F0"   # MATLAB Enable 'off' greyed background
DISABLED_FG = "#7A7A7A"   # MATLAB Enable 'off' greyed text
MIN_LABEL_H = 18      # min label height so g/p/y descenders are never clipped

POSE_DOFS = ["roll", "pitch", "yaw", "Pxval", "Pyval", "Pzval"]


def data_path(name):
    """Locate a data file next to the executable / script (and CWD fallback)."""
    roots = [os.path.dirname(os.path.abspath(sys.argv[0])), os.getcwd()]
    for r in roots:
        p = os.path.join(r, name)
        if os.path.isfile(p):
            return p
    return os.path.join(roots[0], name)


# ---------------------------------------------------------------------------
# Worker that runs a heavy sweep off the GUI thread
# ---------------------------------------------------------------------------
class SweepWorker(QObject):
    progress = Signal(str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, kind, geom, limits, center, scaler):
        super().__init__()
        self.kind = kind
        self.geom = geom
        self.limits = limits
        self.center = center
        self.scaler = scaler
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            cb = self.progress.emit
            cancelled = lambda: self._cancel
            if self.kind == "reachable":
                data = W.reachable_sweep(self.geom, self.limits, self.center,
                                         self.scaler, progress=cb, cancelled=cancelled)
            else:
                data = W.orientation_sweep(self.geom, self.limits, self.center,
                                           self.scaler, progress=cb, cancelled=cancelled)
            self.done.emit(data)
        except Exception:
            self.failed.emit(traceback.format_exc())


class ExportWorker(QObject):
    """Render the PNG rotation series off the GUI thread (the off-screen VTK
    plotter is created and used entirely on this worker thread)."""
    progress = Signal(str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, data, out_dir, count, kind):
        super().__init__()
        self.data = data
        self.out_dir = out_dir
        self.count = count
        self.kind = kind

    def run(self):
        try:
            paths = workspace_view.export_png_series(
                self.data, self.out_dir, self.count, kind=self.kind,
                progress=self.progress.emit)
            self.done.emit(paths)
        except Exception:
            self.failed.emit(traceback.format_exc())


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class HexapodMainWindow(QMainWindow):
    def __init__(self, status_cb=None):
        super().__init__()
        from . import _startup_log as _slog
        _slog.log("  __init__: begin")
        # Optional splash status callback (native or Qt splash) so slow startup
        # steps - notably first-run creation of formdata.txt - are shown to the
        # user instead of looking like a stall.
        self._status_cb = status_cb if callable(status_cb) else (lambda *_a, **_k: None)
        self.setWindowTitle(config.DEFAULT_NAME)
        ip = config.icon_path()
        if ip:
            self.setWindowIcon(QIcon(ip))

        self.fields = {}           # tag -> QLineEdit
        self.bg = {}               # tag -> active background colour
        self._enable = {}          # tag -> "on" | "inactive" | "off" (MATLAB Enable)
        self._theme_labels = []    # labels whose colour follows the Blk/Wht/Sys theme
        self._theme = "system"
        self.revrem = []           # 6 QLabel turnbuckle readouts
        self.calc_name = config.DEFAULT_NAME
        self._threads = []         # keep worker threads alive
        self._ws_dialogs = {}      # kind -> open progress dialog (one per kind, themed live)
        self._last_reach = None    # last computed reachable dataset (NEW)
        self._last_orient = None   # last computed orientation dataset (NEW)
        self._adjust_totals = {}   # cumulative +/- offset per coordinate column

        # The fixed-size GUI panel that holds every MATLAB-positioned control.
        self.gui_panel = QWidget()
        self.gui_panel.setObjectName("guiPanel")
        self.gui_panel.setFixedSize(config.WIN_W, config.WIN_H)
        self.canvas_parent = self.gui_panel

        self._build_console_and_status()   # creates the single self.console
        self._assemble_layout()            # stacks panel / console as central

        # stream mirror (stdout/stderr -> console + status)
        self.emitter = StreamEmitter()
        self.emitter.text.connect(self._on_stream_text)
        self._restore_streams = install_streams(self.emitter)

        _slog.log("  __init__: building widgets")
        self._build_headers()
        self._build_zero_disp()
        self._build_coordinates()
        self._build_constraints()
        self._build_outputs()
        self._build_inputs()
        self._build_buttons()
        self._build_toggles()
        _slog.log("  __init__: building 3D sketch (matplotlib canvas)")
        self._build_plot()
        # The 3D plot must sit UNDER every surrounding control so buttons/labels
        # are never covered.  (Its background is transparent - see platform_view.)
        self.platform.lower()
        # Match the sketch's origin-arrow colour to the OS theme at startup
        # (white arrows on a dark desktop, black on a light one).
        _slog.log("  __init__: applying initial theme")
        self._apply_theme("system")

        # Pressing Enter/Return anywhere acts like clicking "Solve Inverse Kinematics".
        for _key in (Qt.Key_Return, Qt.Key_Enter):
            _sc = QShortcut(QKeySequence(_key), self)
            _sc.setContext(Qt.WindowShortcut)
            _sc.activated.connect(lambda: self.solve_inverse())

        _slog.log("  __init__: loading settings (formdata.txt)")
        self._load_settings()
        _slog.log("  __init__: settings loaded")
        self._apply_edit_locks(zpd_unlocked=False, constraints_unlocked=False)
        self._recompute_bench_z()
        _slog.log("  __init__: initial solve_inverse")
        self.solve_inverse(animate=False)
        print("Ready. Hexapod calculator started.")
        _slog.log("  __init__: done")

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _label(self, text, mpos, bold=False, size=None, color=None, fit=False,
               align=Qt.AlignLeft):
        x, y, w, h = m2q(*mpos)
        if h < MIN_LABEL_H:           # grow symmetrically about the centre so the
            cy = y + h / 2.0          # baseline stays put but descenders get room
            h = MIN_LABEL_H
            y = int(round(cy - h / 2.0))
        lbl = QLabel(text, self.canvas_parent)
        lbl.setGeometry(x, y, w, h)
        lbl.setAlignment(align | Qt.AlignVCenter)
        f = lbl.font()
        if bold:
            f.setBold(True)
        if size:
            f.setPointSize(size)
        lbl.setFont(f)
        if fit:                        # shrink font if the text is wider than the box
            self._fit_text(lbl, text, w, max_pt=(size or 9))
        if color:
            lbl.setStyleSheet(f"color:{color};")
        else:
            self._theme_labels.append(lbl)   # default colour -> follows theme
        lbl.show()
        return lbl

    @staticmethod
    def _fit_text(widget, text, width, max_pt=9, min_pt=6.0, pad=None):
        """Shrink a widget's font (in half-point steps) until `text` fits `width`.

        QPushButton draws a frame + internal margins (~24 px on Windows) that
        QFontMetrics doesn't include, so buttons get a larger pad than plain
        labels - otherwise the text overflows and clips at both ends.
        """
        if pad is None:
            pad = 24 if isinstance(widget, QPushButton) else 6
        f = widget.font()
        size = float(max_pt)
        f.setPointSizeF(size)
        fm = QFontMetrics(f)
        while size > min_pt and fm.horizontalAdvance(text) > max(width - pad, 1):
            size -= 0.5
            f.setPointSizeF(size)
            fm = QFontMetrics(f)
        widget.setFont(f)
        # Remember the fitted font so it can be re-applied after a theme change:
        # setStyleSheet() re-polishes the widget and otherwise drops setFont(),
        # which would make button text sizes differ between colour themes.
        widget._fit_font = f

    def _edit(self, tag, mpos, bg=WHITE, enable="on", validator=True):
        """Create a value box.  `enable` mirrors MATLAB's Enable property:
        'on' = editable, 'inactive' = shows its colour but not editable,
        'off' = disabled/greyed."""
        e = QLineEdit("0.000", self.canvas_parent)
        e.setGeometry(*m2q(*mpos))
        if validator:
            v = QDoubleValidator(-1e9, 1e9, 3, e)
            v.setLocale(QLocale(QLocale.C))
            v.setNotation(QDoubleValidator.StandardNotation)
            e.setValidator(v)
        e.setReadOnly(enable != "on")
        self.fields[tag] = e
        self.bg[tag] = bg
        self._enable[tag] = enable
        self._style(tag)
        e.show()
        return e

    def _style(self, tag, color="#000000"):
        e = self.fields[tag]
        if self._enable.get(tag, "on") == "off":      # disabled -> greyed out
            bg, fg = DISABLED_BG, DISABLED_FG
        else:                                          # on / inactive -> its colour
            bg, fg = self.bg[tag], color
        e.setStyleSheet(f"QLineEdit{{background:{bg}; color:{fg};}}")

    def _set_field_enable(self, tag, state):
        """Switch a field between 'on' (editable) and 'off' (greyed) and restyle."""
        self._enable[tag] = state
        self.fields[tag].setReadOnly(state != "on")
        self._style(tag)

    # ------------------------------------------------------------------
    def _build_headers(self):
        self._label("Zero-Displacement Configuration  [mm]", (5, 685, 290, 18),
                    bold=True, size=8, color=config.HEADER_COLOR, fit=True)
        self._label("Workspace Search Limits and Constraints", (467, 630, 237, 18),
                    bold=True, size=8, color=config.HEADER_COLOR, fit=True)
        # column headers + adjust buttons
        for s, x in (("xsi", 80), ("ysi", 155), ("xmi", 312), ("ymi", 382)):
            self._label(s, (x, 585, 20, 12))
        for col, x in (("xsi", 102), ("ysi", 177), ("xmi", 334), ("ymi", 404)):
            b = QPushButton("\u00b1", self.canvas_parent)
            b.setGeometry(*m2q(x, 581, 20, 17))
            b.clicked.connect(lambda _=False, c=col: self.open_adjust(c))
            b.show()
            setattr(self, f"adj_{col}", b)

    def _build_zero_disp(self):
        rows = [
            ("Base Z Coordinate:", "baseZ", (28, 661, 100, 13), (128, 657, 70, 20)),
            ("Platform Z Coordinate:", "platZheight", (10, 637, 120, 13), (128, 632, 70, 20)),
            ("ZPD Leg Length:", "zpdLegLength", (24, 612, 120, 13), (128, 607, 70, 20)),
            ("Bench Top Thickness:", "benchThickness", (236, 661, 150, 13), (369, 657, 70, 20)),
            # These two labels are long, so their boxes are narrower and
            # right-justified to the Bench-Top-Thickness box's right edge (439).
            ("Platform Plane to Benchbottom:", "platToBenchBottomZ", (210, 637, 172, 13), (383, 632, 56, 20)),
            ("Calculated Focus to Benchtop Z:", "benchZheight", (207, 612, 175, 13), (383, 607, 56, 20)),
        ]
        for text, tag, lpos, epos in rows:
            self._label(text, lpos)
            self._edit(tag, epos, enable="off")   # locked/greyed until Edit-ZPD is on
        # benchZheight is recomputed when the Edit-ZPD lock is toggled off and on
        # adjust, exactly as in the original (field edits alone do not recompute).

    def _build_coordinates(self):
        for i in range(1, 7):
            yT = 567 - (i - 1) * 25
            yE = yT - 7
            self._label(f"Base {i}:", (5, yT, 50, 12))
            self._edit(f"base{i}x", (55, yE, 70, 20), enable="off")
            self._edit(f"base{i}y", (130, yE, 70, 20), enable="off")
            self._label(f"Platform {i}:", (225, yT, 60, 12))
            self._edit(f"plat{i}x", (285, yE, 70, 20), enable="off")
            self._edit(f"plat{i}y", (359, yE, 70, 20), enable="off")
        # NOTE: editing coordinates does not redraw until "Solve Inverse
        # Kinematics" is pressed, matching the original 'base'/'plat' callbacks.

    def _build_constraints(self):
        # Whole section left-justified to LX (the "Leg Length" left edge); min/max
        # columns at 560 / 634; headers centered over their columns.
        LX = 467
        self._label("Constraints", (LX, 579, 130, 18), bold=True, size=8, color=config.HEADER_COLOR)
        self._label("min", (560, 585, 70, 12), align=Qt.AlignHCenter)
        self._label("max", (634, 585, 70, 12), align=Qt.AlignHCenter)
        C = [("Roll [\u00b0 about x]:", "roll", 563, 560),
             ("Pitch [\u00b0 about y]:", "pitch", 543, 538),
             ("Yaw [\u00b0 about z]:", "yaw", 521, 516)]
        for text, tag, ty, ey in C:
            self._label(text, (LX, ty, 93, 13))
            self._edit(f"{tag}min", (560, ey, 70, 20), enable="off")
            self._edit(f"{tag}max", (634, ey, 70, 20), enable="off")
        D = [("X [mm]:", "px", 499, 494), ("Y [mm]:", "py", 478, 472), ("Z [mm]:", "pz", 455, 450)]
        for text, tag, ty, ey in D:
            self._label(text, (LX, ty, 93, 13))
            self._edit(f"{tag}min", (560, ey, 70, 20), enable="off")
            self._edit(f"{tag}max", (634, ey, 70, 20), enable="off")
        self._label("Leg Length [mm]:", (LX, 433, 100, 13))
        self._edit("jointmin", (560, 428, 70, 20), enable="off")
        self._edit("jointmax", (634, 428, 70, 20), enable="off")
        self._label("Leg Actuator Lead [mm/rev]:", (LX, 412, 165, 13))
        self._edit("actuatorLead", (634, 406, 70, 20), bg=YELLOW, enable="off")

    def _build_outputs(self):
        self._label("OUTPUTS - Leg Lengths [mm] and Angular Adjustment [\u00b0]:",
                    (5, 399, 415, 22), bold=True, size=10, color=config.HEADER_COLOR, fit=True)
        # headers centered over their value-box columns (55/117/179/241/303, w=60).
        # "ang. delta [deg]" gets a wider box (centered on the same column, x=333)
        # so the bracket/degree symbol isn't clipped by the narrow column width.
        for text, x, w in (("abs. old", 55, 60), ("abs. new", 117, 60),
                           ("abs. delta", 179, 60), ("rel. delta", 241, 60),
                           ("ang. delta [\u00b0]", 291, 84)):
            self._label(text, (x, 385, w, 15), align=Qt.AlignHCenter)
        self._label("(turns + rem. ang.)", (366, 385, 116, 15), size=8, align=Qt.AlignHCenter)

        legY = [365, 340, 315, 290, 265, 240]
        for j in range(1, 7):
            y = legY[j - 1]
            self._label(f"Leg {j}:", (5, y + 3, 50, 15), bold=True, size=9,
                        color=config.LEG_COLORS[j - 1])
            self._edit(f"leg{j}_old", (55, y, 60, 20), enable="off")
            self._edit(f"leg{j}", (117, y, 60, 20), bg=CYAN, enable="inactive")
            self._edit(f"leg{j}absdelta", (179, y, 60, 20), bg=CYAN, enable="inactive")
            self._edit(f"leg{j}delta", (241, y, 60, 20), bg=CYAN, enable="inactive")
            self._edit(f"leg{j}angledelta", (303, y, 60, 20), bg=YELLOW, enable="inactive")
            rr = QLabel("(0 rev and 0.0\u00b0)", self.canvas_parent)
            rr.setGeometry(*m2q(366, y - 2, 116, 20))
            rr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)   # centred under the header
            self._theme_labels.append(rr)
            rr.show()
            self.revrem.append(rr)

    def _build_inputs(self):
        self._label("INPUTS - Change to Input Focus Pose:", (5, 206, 270, 20),
                    bold=True, size=10, color=config.HEADER_COLOR, fit=True)
        for text, x in (("abs. old", 55), ("abs. new", 117), ("rel. delta", 179)):
            self._label(text, (x, 190, 60, 15), align=Qt.AlignHCenter)
        P = [("Roll [\u00b0]:", "roll", 175, 170), ("Pitch [\u00b0]:", "pitch", 150, 145),
             ("Yaw [\u00b0]:", "yaw", 125, 120), ("X [mm]:", "Pxval", 100, 95),
             ("Y [mm]:", "Pyval", 75, 70), ("Z [mm]:", "Pzval", 50, 45)]
        for text, tag, ty, ey in P:
            self._label(text, (5, ty, 50, 13))
            self._edit(f"{tag}_old", (55, ey, 60, 20), enable="off")
            self._edit(tag, (117, ey, 60, 20), bg=CYAN, enable="off")
            self._edit(f"{tag}delta", (179, ey, 60, 20), enable="on")

    def _build_buttons(self):
        btns = [
            ("Quit", (618, 10, 90, 25), self.on_quit),
            ("Reset View", (526, 10, 90, 25), lambda: self.platform.reset_view()),
            ("Save Everything", (247, 10, 112, 25), self.save_data),
            ("Update Old Pose", (247, 37, 112, 25), self.overwrite_data),
            ("Zero Input Values", (247, 64, 112, 25), self.zero_data),
            ("Go Home Input Val.", (247, 91, 112, 25), self.home_data),
            ("Solve Inverse Kinematics", (54, 10, 186, 25), lambda: self.solve_inverse()),
            # Right-side block: left edge LX=467, right edge 704 (= max column).
            ("Draw Orientation Workspace", (467, 655, 155, 25), lambda: self.open_workspace("orientation")),
            ("Draw Reachable Workspace", (467, 680, 155, 25), lambda: self.open_workspace("reachable")),
            ("Export to PNG", (626, 655, 78, 25), lambda: self.export_png("orientation")),
            ("Export to PNG", (626, 680, 78, 25), lambda: self.export_png("reachable")),
        ]
        for text, mpos, cb in btns:
            b = QPushButton(text, self.canvas_parent)
            b.setGeometry(*m2q(*mpos))
            self._fit_text(b, text, mpos[2])     # shrink font so text never clips
            b.clicked.connect(cb)
            b.show()

    def _build_toggles(self):
        # "Colour Theme" buttons sit centred between Save Everything (right edge
        # 359) and the Reset View button (left edge 526), with a header above.
        self._label("Colour Theme", (367, 37, 151, 14), bold=True, size=8,
                    color=config.HEADER_COLOR, align=Qt.AlignHCenter)
        for label, mode, x in (("Blk", "black", 370), ("Wht", "white", 419), ("Sys", "system", 468)):
            tb = QPushButton(label, self.canvas_parent)
            tb.setGeometry(*m2q(x, 10, 47, 25))
            f = tb.font(); f.setPointSize(8); tb.setFont(f)   # uniform size (Wht == Blk == Sys)
            tb._fit_font = f                                  # survive theme re-polish
            tb.clicked.connect(lambda _=False, m=mode: self._apply_theme(m))
            tb.show()
            setattr(self, f"theme_{mode}_btn", tb)

        self.editzpd_btn = QPushButton("Edit Zero-Displacement Coordinates", self.canvas_parent)
        self.editzpd_btn.setGeometry(*m2q(240, 682, 200, 25))
        self._fit_text(self.editzpd_btn, "Edit Zero-Displacement Coordinates", 200)
        self.editzpd_btn.setCheckable(True)
        self.editzpd_btn.toggled.connect(self.on_edit_zpd)
        self.editzpd_btn.show()

        # Left-justified to the right-side block (LX=467), full block width.
        self.editcon_btn = QPushButton("Edit Workspace Search Limits and Constraints", self.canvas_parent)
        self.editcon_btn.setGeometry(*m2q(467, 604, 237, 25))
        self._fit_text(self.editcon_btn, "Edit Workspace Search Limits and Constraints", 237)
        self.editcon_btn.setCheckable(True)
        self.editcon_btn.toggled.connect(self.on_edit_constraints)
        self.editcon_btn.show()

    def _build_plot(self):
        self.platform = PlatformView(self.canvas_parent)
        self.platform.setGeometry(*m2q(*config.PLOT_RECT_MATLAB))
        self.platform.show()

    def _build_console_and_status(self):
        # Single, always-on console: anchored directly below the fixed GUI panel.
        # It can't move up into the GUI, but the window's bottom edge can be
        # dragged down to extend it; a scrollbar appears once output fills it.
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(self._mono_font(9))
        # Default the console to exactly 6 visible text lines.  (It still grows
        # when the window's bottom edge is dragged down - see _assemble_layout.)
        fm = QFontMetrics(self._mono_font(9))
        self._console_h = 6 * fm.lineSpacing() + 12     # 6 lines + frame/padding
        self.console.setMinimumHeight(self._console_h)

    @staticmethod
    def _mono_font(pt):
        """A monospace font that resolves on Windows, macOS, and Linux."""
        f = QFont("Consolas", pt)
        f.setStyleHint(QFont.Monospace)
        f.setFamilies(["Consolas", "Menlo", "DejaVu Sans Mono",
                       "Liberation Mono", "Courier New", "monospace"])
        return f

    def _assemble_layout(self):
        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        v.addWidget(self.gui_panel, 0, Qt.AlignLeft | Qt.AlignTop)
        v.addWidget(self.console, 1)          # grows downward when the window is taller
        self.setCentralWidget(container)
        # Lock the width to the (pixel-faithful) panel; allow vertical resize so
        # the console height can be extended by dragging the bottom edge.  The
        # window opens showing the panel + a 6-line console, and won't shrink
        # below that (dragging the bottom edge taller extends the console).
        self.setFixedWidth(config.WIN_W)
        h0 = config.WIN_H + self._console_h + 6
        self.setMinimumHeight(h0)
        self.resize(config.WIN_W, h0)

    def _apply_theme(self, mode):
        """Change the window theme (Black / White / System).

        Black -> themed-label text white; White -> black; System -> OS defaults.
        Native buttons read well on Black/System, but wash out on a White panel,
        so in White mode every button gets an explicit light style + black font.
        The 3D sketch's origin arrows/labels turn white on a dark background."""
        from PySide6.QtGui import QPalette, QColor
        from PySide6.QtWidgets import QApplication, QPushButton
        if mode == "black":
            panel, text, con = QColor("#000000"), "#FFFFFF", ("#101010", "#F0F0F0")
        elif mode == "white":
            panel, text, con = QColor("#FFFFFF"), "#000000", ("#FFFFFF", "#000000")
        else:                                   # system defaults
            panel, text, con = None, None, None

        # Panel background via palette (so native buttons/boxes stay native-looking).
        if panel is not None:
            pal = self.gui_panel.palette()
            pal.setColor(QPalette.Window, panel)
            self.gui_panel.setPalette(pal)
            self.gui_panel.setAutoFillBackground(True)
        else:
            self.gui_panel.setAutoFillBackground(False)
            self.gui_panel.setPalette(QPalette())

        # Default-coloured labels follow the theme (red headers / coloured leg
        # labels keep their own colour and are untouched).
        for lbl in self._theme_labels:
            lbl.setStyleSheet(f"color:{text};" if text else "")

        # Buttons have fixed geometry (setGeometry), so they never move or resize
        # between themes.  The only problem is visibility: native buttons wash out
        # on a White panel, so in White mode they get an explicit light fill +
        # border + black text.  Black / System keep native buttons (which read
        # fine on their panels).  The fitted fonts are re-applied below so the
        # text size is identical in every theme too.
        if mode == "white":
            bcss = ("QPushButton{background-color:#e6e6e6; color:#000000;"
                    " border:1px solid #9a9a9a;}"
                    "QPushButton:hover{background-color:#d6d6d6;}"
                    "QPushButton:pressed{background-color:#c8c8c8;}"
                    "QPushButton:checked{background-color:#cfe3ff; border:1px solid #5b9bd5;}")
        else:
            bcss = ""
        for b in self.gui_panel.findChildren(QPushButton):
            b.setStyleSheet(bcss)

        # Console matches the window background.
        self.console.setStyleSheet(
            f"QTextEdit{{background-color:{con[0]}; color:{con[1]};}}" if con else "")

        # 3D sketch origin arrows + XYZ labels: white on a dark background.
        if hasattr(self, "platform"):
            if mode == "black":
                arrow = "white"
            elif mode == "white":
                arrow = "black"
            else:                               # system: detect from OS palette luminance
                wc = QApplication.palette().color(QPalette.Window)
                lum = 0.299 * wc.red() + 0.587 * wc.green() + 0.114 * wc.blue()
                arrow = "white" if lum < 128 else "black"
            self.platform.set_theme_color(arrow)

        self._theme = mode
        config.set_theme(mode)          # shared state read by the 3D workspace windows

        # Re-apply every button's fitted font: setStyleSheet() above re-polishes
        # the widgets and drops setFont(), which otherwise makes button text sizes
        # differ between colour themes.  This keeps all buttons identical in size.
        for b in self.gui_panel.findChildren(QPushButton):
            f = getattr(b, "_fit_font", None)
            if f is not None:
                b.setFont(f)

        # Reflect the theme in any open secondary windows so the colours match
        # everywhere: the workspace progress dialog(s), and the 3D workspace
        # windows (their Qt chrome + the VTK scene background/foreground).
        css = config.qt_stylesheet(mode)
        for d in list(self._ws_dialogs.values()):
            if d is not None:
                try:
                    d.setStyleSheet(css)
                except Exception:
                    pass
        try:
            workspace_view.apply_theme_to_open()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stream / console handling
    # ------------------------------------------------------------------
    def _on_stream_text(self, text):
        self.console.moveCursor(QTextCursor.End)
        self.console.insertPlainText(text)
        self.console.moveCursor(QTextCursor.End)

    # ------------------------------------------------------------------
    # Settings load/save
    # ------------------------------------------------------------------
    def _load_settings(self):
        # 1) A formdata.txt sitting next to the exe (or in the working dir) is the
        #    user's own editable copy - prefer it.
        path = data_path(config.SETTINGS_FILE)
        status = settings_io.read_settings(path)

        # 2) If there isn't one (the usual case for a freshly-built exe, where the
        #    file is bundled INSIDE the exe rather than next to it), fall back to
        #    the bundled copy and write it out next to the exe so it's editable and
        #    so "Save Everything" has a place to save.  This is what prevents the
        #    old hidden "Settings file" dialog from blocking startup.
        if status[0] == "missing":
            bundled = config.resource_path(config.SETTINGS_FILE)
            try:
                same = os.path.abspath(bundled) == os.path.abspath(path)
            except Exception:
                same = False
            if os.path.isfile(bundled) and not same:
                b_status = settings_io.read_settings(bundled)
                if b_status[0] == "ok":
                    status = b_status
                    try:
                        shutil.copyfile(bundled, path)
                    except Exception:
                        pass                    # not fatal - we still have the values

        if status[0] == "ok":
            values, name = status[1], status[2]
            self._apply_values(values)
            self.calc_name = name
            self.setWindowTitle(name)
            print(f"Loaded configuration from {os.path.basename(path)}.")
            return

        # 3) Genuinely nothing usable to load.  IMPORTANT: do NOT pop a modal
        #    dialog here.  During startup the splash screen is always-on-top, so a
        #    QMessageBox opens *behind* it - invisible - and the app looks frozen
        #    forever at "Building interface" while it waits for a click.  Instead
        #    fall back to defaults silently and report it in the console.
        self._apply_values(settings_io.default_values_dict())
        if status[0] == "missing":
            self._status_cb("Creating formdata.txt with default values\u2026")
            try:
                settings_io.write_defaults(path)
                print(f"'{config.SETTINGS_FILE}' not found - created it next to the "
                      f"program with default values.")
            except Exception as exc:
                print(f"'{config.SETTINGS_FILE}' not found - using built-in defaults "
                      f"(couldn't write a copy: {exc}).")
        else:                                   # present but invalid/corrupt
            self._status_cb("Settings file unreadable - using defaults\u2026")
            print(f"'{config.SETTINGS_FILE}' could not be read ({status[2]}). "
                  f"Using built-in defaults; the existing file was left untouched.")

    def _apply_values(self, values):
        for tag in config.TAGS:
            if tag in self.fields and tag in values:
                self.fields[tag].setText(settings_io.fmt(values[tag]))

    def _collect_values(self):
        out = {}
        for tag in config.TAGS:
            out[tag] = self.get(tag)
        return out

    def save_data(self):
        path = data_path(config.SETTINGS_FILE)
        settings_io.write_settings(path, self._collect_values(), self.calc_name)
        print("configuration saved...")

    # ------------------------------------------------------------------
    # Field accessors
    # ------------------------------------------------------------------
    def get(self, tag):
        try:
            return float(self.fields[tag].text())
        except (ValueError, KeyError):
            return 0.0

    def set(self, tag, value, color="#000000", prec=3):
        if tag in self.fields:
            self.fields[tag].setText(f"{float(value):.{prec}f}")
            self._style(tag, color)

    # ------------------------------------------------------------------
    # Core: solve inverse kinematics + leg outputs + redraw
    # ------------------------------------------------------------------
    def _geom(self):
        return dict(
            xsi=[self.get(f"base{i}x") for i in range(1, 7)],
            ysi=[self.get(f"base{i}y") for i in range(1, 7)],
            xmi=[self.get(f"plat{i}x") for i in range(1, 7)],
            ymi=[self.get(f"plat{i}y") for i in range(1, 7)],
            baseZ=self.get("baseZ"), platformZ=self.get("platZheight"),
            zpd=self.get("zpdLegLength"),
            leg_lo=self.get("jointmin"), leg_hi=self.get("jointmax"),
        )

    def solve_inverse(self, animate=None):
        # new = old + delta   (port of solve_inverse.m)
        for tag in POSE_DOFS:
            self.set(tag, self.get(f"{tag}_old") + self.get(f"{tag}delta"))
        g = self._geom()
        roll, pitch, yaw = self.get("roll"), self.get("pitch"), self.get("yaw")
        px, py, pz = self.get("Pxval"), self.get("Pyval"), self.get("Pzval")
        lead = self.get("actuatorLead")

        sol = kinematics.stew_inverse(g["xsi"], g["ysi"], g["xmi"], g["ymi"],
                                      roll, pitch, yaw, px, py, pz,
                                      g["baseZ"], g["platformZ"])
        legs = sol[:6]
        plat = sol[24:42].reshape(6, 3)             # animcoords (== platcoords; T == Ta)

        # Display new leg lengths, then compute deltas from the 3-decimal values
        # exactly as the MATLAB does (it reads the rounded strings back).
        legs_disp = np.round(legs, 3)
        legs_old = np.array([round(self.get(f"leg{j+1}_old"), 3) for j in range(6)])
        legs_delta = np.round(legs_disp - legs_old, 3)
        legs_absdelta = np.round(legs_disp - g["zpd"], 3)
        with np.errstate(divide="ignore", invalid="ignore"):
            legs_ang = np.round((legs_disp - legs_old) * 360.0 / lead, 1) if lead else np.zeros(6)
        rev, rem = kinematics.leg_revolutions_remainder(legs_ang)

        for j in range(6):
            self.set(f"leg{j+1}", legs_disp[j])
            self.set(f"leg{j+1}absdelta", legs_absdelta[j])
            self.set(f"leg{j+1}delta", legs_delta[j])
            self.set(f"leg{j+1}angledelta", legs_ang[j], prec=1)
            self.revrem[j].setText(f"({int(rev[j])} rev and {float(rem[j]):.1f}\u00b0)")

        self._recolor_legs()

        base_pts = np.column_stack([g["xsi"], g["ysi"], np.full(6, g["baseZ"])])
        do_anim = True if animate is None else animate
        self.platform.update_pose(base_pts, plat, animate=do_anim)

    def _recolor_legs(self):
        """Port of color_input_box.m: colour each leg's *absdelta* field red when
        its stroke leaves [jointmin, jointmax], green otherwise."""
        jmin, jmax = self.get("jointmin"), self.get("jointmax")
        for j in range(6):
            tag = f"leg{j+1}absdelta"
            v = self.get(tag)
            col = config.BAD_RED if (v < jmin or v > jmax) else config.OK_GREEN
            self._style(tag, col)

    # ------------------------------------------------------------------
    # Pose buttons
    # ------------------------------------------------------------------
    def overwrite_data(self):
        """Update Old Pose (port of overwrite_data.m): copy new -> old (legs and
        posture), recompute deltas (now zero), then re-solve and recolour."""
        for k in range(6):
            self.set(f"leg{k+1}_old", self.get(f"leg{k+1}"))
        for tag in POSE_DOFS:
            self.set(f"{tag}_old", self.get(tag))
        # zero the input deltas, then re-solve (new == old now)
        for tag in POSE_DOFS:
            self.set(f"{tag}delta", 0.0)
        self.solve_inverse(animate=False)
        self._recolor_legs()
        print("current pose overwritten... SAVE if you want to keep this pose...")

    def zero_data(self):
        """Zero Input Values (port of zero_data.m): set the six input deltas to
        zero and recolour. Does NOT re-solve (matches the original)."""
        for tag in POSE_DOFS:
            self.set(f"{tag}delta", 0.0)
        self._recolor_legs()
        print("new input data zeroed...")

    def home_data(self):
        """Go Home (port of home_data.m): set each delta to the negative of the
        current *new* pose value and recolour. Does NOT re-solve (matches the
        original)."""
        for tag in POSE_DOFS:
            self.set(f"{tag}delta", -self.get(tag))
        self._recolor_legs()
        print("new input data given home values...")

    # ------------------------------------------------------------------
    # Column adjust (+/-)
    # ------------------------------------------------------------------
    def open_adjust(self, column):
        """Port of openAdjustDlg.m / applyAdjust.m. Adds one entered value to all
        six joints of a column, keeps a cumulative running total per column,
        recomputes benchZheight, and re-solves."""
        prev = self._adjust_totals.get(column, 0.0)
        dlg = dialogs.AdjustDialog(column, prev, self)
        if not dlg.exec():
            return
        v = dlg.value
        self._adjust_totals[column] = prev + v
        which = "base" if column in ("xsi", "ysi") else "plat"
        axis = "x" if column in ("xsi", "xmi") else "y"
        for i in range(1, 7):
            t = f"{which}{i}{axis}"
            self.set(t, self.get(t) + v)
        self._recompute_bench_z()
        self.solve_inverse()

    # ------------------------------------------------------------------
    # Edit-lock toggles
    # ------------------------------------------------------------------
    def _geom_tags(self):
        # benchZheight is a computed field and stays read-only at all times,
        # so it is intentionally excluded from the editable set.
        tags = ["baseZ", "platZheight", "zpdLegLength", "benchThickness",
                "platToBenchBottomZ"]
        for i in range(1, 7):
            tags += [f"base{i}x", f"base{i}y", f"plat{i}x", f"plat{i}y"]
        return tags

    def _constraint_tags(self):
        t = []
        for k in ("roll", "pitch", "yaw", "px", "py", "pz"):
            t += [f"{k}min", f"{k}max"]
        t += ["jointmin", "jointmax", "actuatorLead"]
        return t

    def _apply_edit_locks(self, zpd_unlocked, constraints_unlocked):
        for tag in self._geom_tags():
            self._set_field_enable(tag, "on" if zpd_unlocked else "off")
        # benchZheight is always disabled/greyed (computed field).
        self._set_field_enable("benchZheight", "off")
        # The +/- column adjusters work even while coordinates are locked
        # (exactly as in the MATLAB tool), so they are always enabled.
        for tag in self._constraint_tags():
            self._set_field_enable(tag, "on" if constraints_unlocked else "off")

    def on_edit_zpd(self, checked):
        # checked == True -> unlock for editing; False -> lock (and recompute
        # benchZheight), matching edit_zpd.m. No re-solve here.
        self._apply_edit_locks(checked, self.editcon_btn.isChecked())
        if not checked:
            self._recompute_bench_z()

    def on_edit_constraints(self, checked):
        # Enable/disable the constraint fields, matching edit_Constraints.m.
        self._apply_edit_locks(self.editzpd_btn.isChecked(), checked)

    def _recompute_bench_z(self):
        bz = self.get("platZheight") + self.get("benchThickness") + self.get("platToBenchBottomZ")
        self.set("benchZheight", bz)

    # ------------------------------------------------------------------
    # Workspace (reachable / orientation)
    # ------------------------------------------------------------------
    def _center_pose(self, pose_key):
        if pose_key == "new":
            return (self.get("roll"), self.get("pitch"), self.get("yaw"),
                    self.get("Pxval"), self.get("Pyval"), self.get("Pzval"))
        if pose_key == "old":
            return (self.get("roll_old"), self.get("pitch_old"), self.get("yaw_old"),
                    self.get("Pxval_old"), self.get("Pyval_old"), self.get("Pzval_old"))
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)   # home

    def _limits(self, kind):
        if kind == "reachable":
            return dict(pxmin=self.get("pxmin"), pxmax=self.get("pxmax"),
                        pymin=self.get("pymin"), pymax=self.get("pymax"),
                        pzmin=self.get("pzmin"), pzmax=self.get("pzmax"))
        return dict(rollmin=self.get("rollmin"), rollmax=self.get("rollmax"),
                    pitchmin=self.get("pitchmin"), pitchmax=self.get("pitchmax"),
                    yawmin=self.get("yawmin"), yawmax=self.get("yawmax"))

    def _standalone_window(self, dlg):
        """Make a dialog a top-level window with its own taskbar button + preview
        and the app icon (like the main window and the 3D figure windows).  A
        parented QDialog is an owned tool-window on Windows and gets no taskbar
        entry, so it is created parentless and given the plain Window type."""
        from PySide6.QtCore import Qt as _Qt
        dlg.setWindowFlags(_Qt.Window)
        ip = config.icon_path()
        if ip:
            dlg.setWindowIcon(QIcon(ip))
        return dlg

    def open_workspace(self, kind):
        # Only one progress window per kind at a time.  If one is already open,
        # bring it to the front instead of opening a second.  (Multiple finished
        # 3D figure windows may still stack up - those are not limited.)
        existing = self._ws_dialogs.get(kind)
        if existing is not None:
            try:
                existing.showNormal()
                existing.raise_()
                existing.activateWindow()
                return
            except Exception:
                self._ws_dialogs.pop(kind, None)

        title = "Draw Reachable Workspace Progress" if kind == "reachable" \
            else "Draw Orientation Workspace Progress"
        dlg = dialogs.WorkspaceProgressDialog(title, None)   # parentless -> own taskbar window
        self._standalone_window(dlg)
        dlg.setStyleSheet(config.qt_stylesheet())        # match current theme
        self._ws_dialogs[kind] = dlg
        dlg.finished.connect(lambda *_, k=kind: self._ws_dialogs.pop(k, None))

        def run(scaler, pose_key, is_recall):
            res_label = self._res_label(scaler, is_recall)
            if is_recall:
                self._recall_workspace(kind, dlg, res_label)
                dlg.finished_run()
                return
            self._start_sweep(kind, scaler, pose_key, dlg, res_label)

        dlg.run_requested.connect(run)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    @staticmethod
    def _res_label(scaler, is_recall):
        if is_recall:
            return "Recalled"
        for name, val in (("High", config.SCALER_HIGH),
                          ("Medium", config.SCALER_MEDIUM),
                          ("Low", config.SCALER_LOW)):
            if abs(scaler - val) < 1e-9:
                return name
        return "Custom"

    def _start_sweep(self, kind, scaler, pose_key, dlg, res_label=None):
        geom = self._geom()
        limits = self._limits(kind)
        center = self._center_pose(pose_key)
        thread = QThread()
        worker = SweepWorker(kind, geom, limits, center, scaler)
        worker.moveToThread(thread)
        # stash context so the GUI-thread slots can recover it via sender()
        worker._kind = kind
        worker._dlg = dlg
        worker._thread = thread
        worker._res_label = res_label

        thread.started.connect(worker.run)
        # progress/done/failed are emitted from the worker thread; connecting them
        # to bound methods of GUI-thread QObjects gives queued (thread-safe) calls.
        worker.progress.connect(dlg.append_status)
        worker.progress.connect(self._echo)
        worker.done.connect(self._on_sweep_done)
        worker.failed.connect(self._on_sweep_failed)
        # DirectConnection: cancel() must run in the GUI thread and set the flag
        # right away.  A queued connection would wait for the worker thread's event
        # loop, which is busy inside run(), so Abort would never take effect.
        dlg.cancel_requested.connect(worker.cancel, Qt.DirectConnection)

        self._threads.append((thread, worker))
        thread.start()

    @Slot(str)
    def _echo(self, text):
        print(text)

    @Slot(object)
    def _on_sweep_done(self, data):
        worker = self.sender()
        kind, dlg, thread = worker._kind, worker._dlg, worker._thread
        res_label = getattr(worker, "_res_label", None)
        dlg.finished_run()
        if data is None:
            print("...workspace search aborted (no window opened).")
            dlg.append_status("aborted - no window opened.")
        else:
            if kind == "reachable":
                self._last_reach = data
                W.save_dataset(data_path("reachable_workspace_data_NEW.mat"), data)
            else:
                self._last_orient = data
                W.save_dataset(data_path("orientation_workspace_data_NEW.mat"), data)
            print("workspace data saved (..._NEW.mat). Opening 3D view...")
            dlg.append_status("done - opening 3D view.")
            try:
                workspace_view.show_interactive(data, kind, res_label=res_label)
            except Exception:
                print(traceback.format_exc())
        thread.quit()
        thread.wait()
        self._threads = [(t, w) for (t, w) in self._threads if t is not thread]

    @Slot(str)
    def _on_sweep_failed(self, tb):
        worker = self.sender()
        dlg, thread = worker._dlg, worker._thread
        print(tb)
        dlg.append_status("ERROR - see console.")
        dlg.finished_run()
        thread.quit()
        thread.wait()
        self._threads = [(t, w) for (t, w) in self._threads if t is not thread]

    def _recall_workspace(self, kind, dlg, res_label="Recalled"):
        """Recall (port of the scaler==100 path): re-render the most recent NEW
        dataset, from memory or the ..._NEW.mat file on disk. No file picker."""
        cached = self._last_reach if kind == "reachable" else self._last_orient
        if cached is None:
            fname = data_path(f"{kind}_workspace_data_NEW.mat")
            if os.path.isfile(fname):
                try:
                    cached = W.load_dataset(fname)
                except Exception:
                    print(traceback.format_exc())
                    cached = None
        if cached is None:
            msg = f'"{kind}_workspace_data_NEW.mat" not found'
            print(msg)
            print("Computation cancelled by program - run NEW workspace first or include file.")
            dlg.append_status("...... run NEW workspace first or include file ......")
            dlg.append_status(msg)
            return
        dlg.append_status("recalling last computed dataset...")
        workspace_view.show_interactive(cached, kind, res_label=res_label)

    # ------------------------------------------------------------------
    # PNG export
    # ------------------------------------------------------------------
    def export_png(self, kind):
        cached = self._last_reach if kind == "reachable" else self._last_orient
        # Loop so that a missing/invalid RECALL file returns to the export window
        # rather than aborting the whole action.
        while True:
            dlg = dialogs.PngExportDialog(None, has_new=cached is not None)   # own taskbar window
            self._standalone_window(dlg)
            dlg.setStyleSheet(config.qt_stylesheet())        # match current theme
            if not dlg.exec():
                return
            if dlg.use_recall:
                recall = data_path(f"{kind}_workspace_data_RECALL.mat")
                if not os.path.isfile(recall):
                    QMessageBox.warning(
                        self, "Recall file not found",
                        f'"{kind}_workspace_data_RECALL.mat" was not found in the '
                        f'program folder.\n\nSave a workspace first, or place that '
                        f'file next to the program, then try again.')
                    continue                                 # back to the export window
                try:
                    data = W.load_dataset(recall)
                except Exception:
                    print(traceback.format_exc())
                    QMessageBox.warning(
                        self, "Could not read recall file",
                        f'"{kind}_workspace_data_RECALL.mat" could not be read '
                        f'(see the console for details).')
                    continue                                 # back to the export window
            else:
                data = cached
            break

        out_dir = QFileDialog.getExistingDirectory(self, "Choose output folder", data_path(""))
        if not out_dir:
            return
        print(f"exporting {dlg.count} PNG image(s) for {kind} workspace...")
        print("(rendering in the background - the window stays responsive)")
        self._start_export(data, out_dir, dlg.count, kind)

    def _start_export(self, data, out_dir, count, kind):
        thread = QThread()
        worker = ExportWorker(data, out_dir, count, kind)
        worker.moveToThread(thread)
        worker._thread = thread
        thread.started.connect(worker.run)
        worker.progress.connect(self._echo)
        worker.done.connect(self._on_export_done)
        worker.failed.connect(self._on_export_failed)
        self._threads.append((thread, worker))
        thread.start()

    @Slot(object)
    def _on_export_done(self, paths):
        worker = self.sender()
        thread = worker._thread
        n = len(paths) if paths else 0
        print(f"PNG export finished - {n} image(s) written.")
        thread.quit()
        thread.wait()
        self._threads = [(t, w) for (t, w) in self._threads if t is not thread]

    @Slot(str)
    def _on_export_failed(self, tb):
        worker = self.sender()
        thread = worker._thread
        print(tb)
        thread.quit()
        thread.wait()
        self._threads = [(t, w) for (t, w) in self._threads if t is not thread]

    # ------------------------------------------------------------------
    # Quit
    # ------------------------------------------------------------------
    def on_quit(self):
        choice = dialogs.quit_dialog(self)
        if choice == "cancel":
            return
        if choice == "save":
            self.save_data()                 # prints "configuration saved..."
            print("quitting...")
        else:
            print("quitting without saving...")
        self.close()

    def closeEvent(self, event):
        try:
            self._restore_streams()
        except Exception:
            pass
        super().closeEvent(event)
