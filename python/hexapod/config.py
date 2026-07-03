"""Constants, defaults, colours and the MATLAB->Qt coordinate helper.

Everything here is a direct transcription of the original MATLAB source
(MAIN_GUI.m and load_data.m) so behaviour and geometry stay faithful.
"""

# ---- Main window size (MATLAB figure was Position [.. .. 720 710]) ----
WIN_W = 720
WIN_H = 710

# ---- Embedded 3D platform axes (MATLAB: axes Position [360 20 350 350]) ----
PLOT_RECT_MATLAB = (360, 20, 350, 350)

# ---- The 71 numeric tags, in the EXACT order used by formdata.txt ----
TAGS = [
    "base1x", "base1y", "base2x", "base2y", "base3x", "base3y", "base4x", "base4y",
    "base5x", "base5y", "base6x", "base6y", "baseZ",
    "plat1x", "plat1y", "plat2x", "plat2y", "plat3x", "plat3y", "plat4x", "plat4y",
    "plat5x", "plat5y", "plat6x", "plat6y", "platZheight",
    "rollmin", "rollmax", "pitchmin", "pitchmax", "yawmin", "yawmax",
    "pxmin", "pxmax", "pymin", "pymax", "pzmin", "pzmax",
    "leg1_old", "leg2_old", "leg3_old", "leg4_old", "leg5_old", "leg6_old",
    "leg1", "leg2", "leg3", "leg4", "leg5", "leg6",
    "roll_old", "pitch_old", "yaw_old", "Pxval_old", "Pyval_old", "Pzval_old",
    "roll", "pitch", "yaw", "Pxval", "Pyval", "Pzval",
    "benchZheight", "jointmin", "jointmax", "benchThickness", "zpdLegLength",
    "platToBenchBottomZ", "actuatorLead",
]

# ---- Default values (verbatim from load_data.m) used only to CREATE a fresh file ----
DEFAULT_VALUES = [
    -1487.250, -108.110, -1487.250, 158.110, -390.100, 533.220,
    -159.550, 400.110, -159.550, -350.110, -390.100, -483.220,
    -375.910,
    -1487.250, -3.100, -1487.250, 53.100, -299.160, 480.720,
    -250.490, 452.620, -250.490, -402.620, -299.160, -430.720,
    -263.444,
    -2.650, 2.650, -1.150, 1.150, -1.500, 1.500,
    -28.000, 28.000, -28.000, 28.000, -20.000, 20.000,
    153.869, 153.869, 153.867, 153.870, 153.870, 153.867,
    153.869, 153.869, 153.867, 153.870, 153.870, 153.867,
    0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
    0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
    -124.000, -18.000, 18.000, 110.000, 153.866, 29.444, 3.000,
]

DEFAULT_NAME = "Hexapod Inverse Kinematics and Workspace Solver"
SETTINGS_FILE = "formdata.txt"

# ---- Colours (the six MATLAB default line colours used for the legs) ----
LEG_COLORS = ["#0072BD", "#D95319", "#EDB120", "#7E2F8E", "#77AC30", "#4DBEEE"]
BASE_COLOR = "#00008b"   # dark blue base triangle (3D plot only)
PLAT_COLOR = "#A2142F"   # dark red platform hexagon (3D plot only)
HEADER_COLOR = "#FF5C5C"  # section headers - bright red, readable on the dark UI
OK_GREEN = "#77AC30"     # in-limit leg value
BAD_RED = "#FF0000"      # out-of-limit leg value

# ---- Workspace resolution scalers ----
# Rendered as a clean STRUCTURED GRID surface (no alpha-shape artifacts at any
# resolution), so even the coarse settings look smooth.  Larger scaler = coarser
# / faster.  Approx boundary-point counts and typical laptop solve times:
#     Low    ~0.16M points  (~2 s)     - quick preview
#     Medium ~1.0M  points  (~10 s)
#     High   ~13M   points  (~2-4 min) - finest
SCALER_HIGH = 0.14
SCALER_MEDIUM = 0.50
SCALER_LOW = 1.2649          # = 0.40 * sqrt(10)  (10x fewer points than 0.40)
SCALER_RECALL = 100.0

# Directions processed per chunk in the vectorised sweep (bounds peak memory
# so even the High setting's millions of points never blow up RAM).
SWEEP_CHUNK = 150_000

# Cap on the number of boundary points fed to the 3D surface builder
# (VTK's Delaunay/alpha-shape).  The full point cloud is used for the reported
# limits; the *rendered* surface is uniformly downsampled to this many points so
# rendering is fast and never freezes.  The configured alpha is auto-scaled to
# the resulting point spacing.
MAX_SURFACE_PTS = 12_000
MAX_SCATTER_PTS = 4_000

# ---- alphaShape radii (verbatim from the draw_* / export_* functions) ----
ALPHA_REACHABLE = 30.0
ALPHA_ORIENTATION = 3.0
ALPHA_REACHABLE_EXPORT = 50.0

# ---- Default 3D workspace view ----
# Clean isometric corner (azimuth CCW from +X in the XY plane) tilted 22.5 deg
# down, rotated 90 deg clockwise about Z from a plain corner (so +Y points to
# where +X was).  Used for the interactive window AND the PNG export, and is the
# view the figure-window "Reset View" (menu + toolbar) returns to.
VIEW_REACHABLE = (45.0, 22.5)
VIEW_ORIENTATION = (45.0, 22.5)


# ---- Shared UI theme state (so secondary windows match the main GUI) ----
# main_window._apply_theme sets this; workspace_view reads it for the 3D plot
# background/foreground colours.  One of: "black", "white", "system".
_THEME = "system"


def set_theme(mode):
    global _THEME
    _THEME = mode if mode in ("black", "white", "system") else "system"


def get_theme():
    return _THEME


def qt_stylesheet(mode=None):
    """A Qt stylesheet that themes a *secondary* window (dialog or the plotter's
    menu/tool-bar chrome) to match the main GUI.  Empty for 'system' (native)."""
    mode = mode or get_theme()
    if mode == "black":
        return (
            "QWidget{background-color:#1e1e1e; color:#f0f0f0;}"
            "QMenuBar,QMenu,QToolBar,QStatusBar{background-color:#2b2b2b; color:#f0f0f0;}"
            "QMenu::item:selected,QMenuBar::item:selected{background-color:#3a6ea5;}"
            "QToolButton{background:transparent; color:#f0f0f0;}"
            "QToolButton:hover{background-color:#3a3a3a;}"
            "QPushButton{background-color:#2b2b2b; color:#f0f0f0; border:1px solid #555;"
            " border-radius:3px; padding:3px 8px;}"
            "QPushButton:hover{background-color:#3a3a3a;}"
            "QPushButton:disabled{color:#777; border-color:#3a3a3a;}"
            "QLineEdit{background-color:#2b2b2b; color:#f0f0f0; border:1px solid #555;}"
            "QTextEdit{background-color:#141414; color:#f0f0f0;}"
            "QRadioButton,QCheckBox,QLabel{background:transparent; color:#f0f0f0;}"
            # Explicit indicators - once a QRadioButton/QCheckBox is styled at all,
            # Qt stops drawing the native tick/dot, so we must draw our own or it
            # vanishes.  Filled = checked, hollow = unchecked; visible on dark bg.
            "QRadioButton::indicator{width:12px; height:12px; border-radius:7px;"
            " border:1px solid #9a9a9a; background:#2b2b2b;}"
            "QRadioButton::indicator:checked{border:1px solid #5b9bd5; background:#4da3ff;}"
            "QCheckBox::indicator{width:12px; height:12px; border:1px solid #9a9a9a;"
            " background:#2b2b2b;}"
            "QCheckBox::indicator:checked{border:1px solid #5b9bd5; background:#4da3ff;}"
        )
    if mode == "white":
        return (
            "QWidget{background-color:#f4f4f4; color:#000000;}"
            "QMenuBar,QMenu,QToolBar,QStatusBar{background-color:#e8e8e8; color:#000000;}"
            "QPushButton{background-color:#ececec; color:#000000; border:1px solid #adadad;"
            " border-radius:3px; padding:3px 8px;}"
            "QPushButton:hover{background-color:#dcdcdc;}"
            "QLineEdit{background-color:#ffffff; color:#000000; border:1px solid #adadad;}"
            "QTextEdit{background-color:#ffffff; color:#000000;}"
            "QRadioButton,QCheckBox,QLabel{background:transparent; color:#000000;}"
            "QRadioButton::indicator{width:12px; height:12px; border-radius:7px;"
            " border:1px solid #888888; background:#ffffff;}"
            "QRadioButton::indicator:checked{border:1px solid #2b6cb0; background:#2b6cb0;}"
            "QCheckBox::indicator{width:12px; height:12px; border:1px solid #888888;"
            " background:#ffffff;}"
            "QCheckBox::indicator:checked{border:1px solid #2b6cb0; background:#2b6cb0;}"
        )
    return ""

# ---- Off-screen export figure size (MATLAB set(fig,'Position',[.. .. 1650 1000])) ----
EXPORT_SIZE = (1650, 1000)


def m2q(left, bottom, w, h, win_h=WIN_H):
    """Convert a MATLAB uicontrol Position [left, bottom, w, h] (origin
    bottom-left) into a Qt (x, y, w, h) geometry tuple (origin top-left)."""
    return int(left), int(win_h - bottom - h), int(w), int(h)


def resource_path(*parts):
    """Locate a bundled resource (e.g. the app icon) whether running from source
    or from a PyInstaller one-file/one-folder build."""
    import os
    import sys
    bases = []
    if hasattr(sys, "_MEIPASS"):              # PyInstaller one-file temp dir
        bases.append(sys._MEIPASS)
    bases.append(os.path.dirname(os.path.abspath(__file__)))       # hexapod/
    bases.append(os.path.dirname(bases[-1]))                       # project root
    bases.append(os.path.dirname(os.path.abspath(sys.argv[0])))    # exe dir
    for b in bases:
        p = os.path.join(b, *parts)
        if os.path.exists(p):
            return p
    return os.path.join(bases[0], *parts)


def icon_path():
    """Return the best available app-icon path (.ico on Windows, else .png)."""
    import os
    import sys
    names = ["icon.ico", "icon.png"] if sys.platform.startswith("win") else ["icon.png", "icon.ico"]
    for name in names:
        for sub in (("assets", name), (name,)):
            p = resource_path(*sub)
            if os.path.exists(p):
                return p
    return None
