"""Secondary dialogs.

- AdjustDialog          : the "+/-" column offset tool (openAdjustDlg.m / applyAdjust.m)
- WorkspaceProgressDialog: resolution + pose picker with a scrolling status log
- PngExportDialog       : NEW/RECALL source + number-of-images (yes_callback.m)
- quit_dialog()         : Quit with / without saving / Cancel
"""
from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QTextEdit, QMessageBox, QWidget,
)

from . import config


# ---------------------------------------------------------------------------
# Column adjust ("+/-") dialog
# ---------------------------------------------------------------------------
class AdjustDialog(QDialog):
    """Add or subtract one value from all six joints of a coordinate column.

    Faithful port of openAdjustDlg.m / applyAdjust.m: a single numeric entry plus
    an "Update ZPD" button. The running total (cumulative across openings) is kept
    by the caller and shown here. The entered value is read from `.value` after
    the dialog is accepted; the caller applies it to the six fields, recomputes
    benchZheight, and re-solves."""

    def __init__(self, field, prev_total=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust ZPD")
        self._value = 0.0

        axis_char = field[0].upper()                       # 'X' or 'Y'
        prefix = "platform" if field.endswith("mi") else "base"

        lay = QVBoxLayout(self)
        msg = QLabel(f"Add or subtract {axis_char} value from all "
                     f"{prefix} ({field}) joints:")
        msg.setAlignment(Qt.AlignHCenter)
        lay.addWidget(msg)

        total = QLabel(f"Total offset so far: {prev_total:.3f} mm")
        total.setAlignment(Qt.AlignHCenter)
        f = total.font(); f.setItalic(True); total.setFont(f)
        lay.addWidget(total)

        row = QHBoxLayout()
        row.addStretch(1)
        self.entry = QLineEdit("0.000")
        v = QDoubleValidator(-1e9, 1e9, 3, self)
        self.entry.setValidator(v)
        self.entry.setFixedWidth(150)
        self.entry.setAlignment(Qt.AlignHCenter)
        row.addWidget(self.entry)
        row.addStretch(1)
        lay.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.update_btn = QPushButton("Update ZPD")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(self.update_btn)
        btn_row.addWidget(self.cancel_btn)
        lay.addLayout(btn_row)

        self.update_btn.clicked.connect(self._on_update)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_update(self):
        try:
            self._value = float(self.entry.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a numeric value.")
            return
        self.accept()

    @property
    def value(self):
        return self._value


# ---------------------------------------------------------------------------
# Workspace progress dialog (resolution + pose + scrolling status)
# ---------------------------------------------------------------------------
class WorkspaceProgressDialog(QDialog):
    """Pick resolution + starting pose and watch progress.

    Emits run_requested(scaler, pose_key, is_recall).  pose_key in
    {"home","new","old"}.  The owner runs the solver in a worker thread and feeds
    text back via append_status()."""
    run_requested = Signal(float, str, bool)
    cancel_requested = Signal()

    HIGH = config.SCALER_HIGH
    MEDIUM = config.SCALER_MEDIUM
    LOW = config.SCALER_LOW
    RECALL = config.SCALER_RECALL

    def __init__(self, title="Workspace", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(460, 380)
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Select pose to start analysis at:"))
        pose_row = QHBoxLayout()
        self.pose_group = QButtonGroup(self)
        self.rb_home = QRadioButton("Home")
        self.rb_new = QRadioButton("New pose")
        self.rb_old = QRadioButton("Old pose")
        self.rb_home.setChecked(True)
        for rb in (self.rb_home, self.rb_new, self.rb_old):
            self.pose_group.addButton(rb)
            pose_row.addWidget(rb)
        lay.addLayout(pose_row)

        lay.addWidget(QLabel("Resolution:   (Low = quick preview \u2192 High = finest)"))
        res_row = QGridLayout()
        self.btn_high = QPushButton("High \u2014 finest")
        self.btn_med = QPushButton("Medium")
        self.btn_low = QPushButton("Low \u2014 fastest")
        self.btn_recall = QPushButton("Recall saved data")
        res_row.addWidget(self.btn_high, 0, 0)
        res_row.addWidget(self.btn_med, 0, 1)
        res_row.addWidget(self.btn_low, 1, 0)
        res_row.addWidget(self.btn_recall, 1, 1)
        res_row.setColumnStretch(0, 1)          # equal-width columns
        res_row.setColumnStretch(1, 1)
        lay.addLayout(res_row)

        lay.addWidget(QLabel("Status:"))
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        lay.addWidget(self.status, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setEnabled(False)            # only active while a run is live
        self.abort_btn.setToolTip("Stop the current workspace analysis")
        self.cancel_btn = QPushButton("Close")
        bottom.addWidget(self.abort_btn)
        bottom.addWidget(self.cancel_btn)
        lay.addLayout(bottom)

        # Fixed button heights so the layout is identical in every colour theme
        # (a themed stylesheet changes button padding; a native button doesn't -
        # pinning the height keeps everything in the same place across themes).
        for b in (self.btn_high, self.btn_med, self.btn_low, self.btn_recall):
            b.setFixedHeight(32)
        for b in (self.abort_btn, self.cancel_btn):
            b.setFixedHeight(28)

        self.btn_high.clicked.connect(lambda: self._go(self.HIGH, False))
        self.btn_med.clicked.connect(lambda: self._go(self.MEDIUM, False))
        self.btn_low.clicked.connect(lambda: self._go(self.LOW, False))
        self.btn_recall.clicked.connect(lambda: self._go(self.RECALL, True))
        self.abort_btn.clicked.connect(self._on_abort)
        self.cancel_btn.clicked.connect(self._on_cancel)

    def _pose_key(self):
        if self.rb_new.isChecked():
            return "new"
        if self.rb_old.isChecked():
            return "old"
        return "home"

    def _go(self, scaler, is_recall):
        self._set_buttons(False)
        self.abort_btn.setEnabled(not is_recall)    # recall is instant; nothing to abort
        self.run_requested.emit(scaler, self._pose_key(), is_recall)

    def _on_abort(self):
        """Halt the running sweep but keep the dialog open so it can be re-run."""
        self.append_status("aborting current analysis...")
        self.abort_btn.setEnabled(False)
        self.cancel_requested.emit()

    def _on_cancel(self):
        self.cancel_requested.emit()
        self.reject()

    def _set_buttons(self, enabled):
        for b in (self.btn_high, self.btn_med, self.btn_low, self.btn_recall):
            b.setEnabled(enabled)

    def append_status(self, text):
        """Prepend newest-first, like the MATLAB status box."""
        for line in str(text).splitlines():
            if line.strip():
                self.status.insertPlainText("")
                cursor_text = line + "\n" + self.status.toPlainText()
                self.status.setPlainText(cursor_text)

    def finished_run(self):
        self._set_buttons(True)
        self.abort_btn.setEnabled(False)


# ---------------------------------------------------------------------------
# PNG export dialog
# ---------------------------------------------------------------------------
class PngExportDialog(QDialog):
    """Choose NEW vs RECALL source and number of images (1-360)."""

    def __init__(self, parent=None, has_new=True):
        super().__init__(parent)
        self.setWindowTitle("Export Workspace to PNG")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Data source:"))
        src_row = QHBoxLayout()
        self.group = QButtonGroup(self)
        self.rb_new = QRadioButton("NEW (most recent)")
        self.rb_recall = QRadioButton("RECALL (load file)")
        self.group.addButton(self.rb_new)
        self.group.addButton(self.rb_recall)
        if has_new:
            self.rb_new.setChecked(True)
        else:
            self.rb_recall.setChecked(True)
            self.rb_new.setEnabled(False)
        src_row.addWidget(self.rb_new)
        src_row.addWidget(self.rb_recall)
        lay.addLayout(src_row)

        n_row = QHBoxLayout()
        n_row.addWidget(QLabel("Number of images (1-360):"))
        self.n_images = QLineEdit("1")
        self.n_images.setValidator(QIntValidator(1, 360, self))
        n_row.addWidget(self.n_images)
        lay.addLayout(n_row)

        note = QLabel("1 = a single still image of the current view. "
                      "N = N images taken at evenly spaced angles around a full "
                      "360\u00b0 turn (for assembling a rotation/turntable animation).")
        note.setWordWrap(True)
        nf = note.font(); nf.setPointSize(8); nf.setItalic(True); note.setFont(nf)
        note.setStyleSheet("color:#888888;")
        lay.addWidget(note)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.ok = QPushButton("Export")
        self.cancel = QPushButton("Cancel")
        for b in (self.ok, self.cancel):
            b.setFixedHeight(28)            # theme-independent height
        btn_row.addWidget(self.ok)
        btn_row.addWidget(self.cancel)
        lay.addLayout(btn_row)

        self.ok.clicked.connect(self._validate_accept)
        self.cancel.clicked.connect(self.reject)

    def _validate_accept(self):
        try:
            n = int(self.n_images.text())
        except ValueError:
            n = 0
        if not (1 <= n <= 360):
            QMessageBox.warning(self, "Invalid number",
                                "Please enter a whole number of images between 1 and 360.")
            return
        self.accept()

    @property
    def use_recall(self):
        return self.rb_recall.isChecked()

    @property
    def count(self):
        return int(self.n_images.text())


# ---------------------------------------------------------------------------
# Quit dialog
# ---------------------------------------------------------------------------
def quit_dialog(parent=None):
    """Return 'save', 'nosave', or 'cancel'."""
    box = QMessageBox(parent)
    box.setWindowTitle("Quit")
    box.setText("Do you want to save your configuration before quitting?")
    save_btn = box.addButton("Quit with saving", QMessageBox.AcceptRole)
    nosave_btn = box.addButton("Quit without saving", QMessageBox.DestructiveRole)
    cancel_btn = box.addButton("Cancel", QMessageBox.RejectRole)
    box.setDefaultButton(save_btn)
    box.exec()
    clicked = box.clickedButton()
    if clicked is save_btn:
        return "save"
    if clicked is nosave_btn:
        return "nosave"
    return "cancel"
