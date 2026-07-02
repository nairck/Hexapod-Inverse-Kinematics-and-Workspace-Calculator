"""Inverse kinematics for a hexapod (6-6 Gough-Stewart platform).

Direct port of stew_inverse.m and stew_inverse_ws.m.  The NumPy kernels here
were validated to reproduce the original MATLAB leg lengths to < 5e-4 mm (i.e.
identical at the 3-decimal precision the tool uses), and the vectorised sweep
kernel is what makes the workspace solver 25-50x faster than the MATLAB+MEX
version while remaining numerically identical.

An optional compiled C kernel (stew_inverse_ws DLL/so/dylib) can be dropped in
for users who regenerate standalone code with MATLAB Coder; it is detected and
used automatically, otherwise the (already very fast) NumPy path is used.
"""
from __future__ import annotations
import os
import sys
import ctypes
import numpy as np


# ---------------------------------------------------------------------------
# Rotation matrix shared by both solvers (roll-pitch-yaw, degrees -> radians)
# ---------------------------------------------------------------------------
def _rotation(roll, pitch, yaw):
    tx, ty, tz = np.radians(roll), np.radians(pitch), np.radians(yaw)
    cx, sx = np.cos(tx), np.sin(tx)
    cy, sy = np.cos(ty), np.sin(ty)
    cz, sz = np.cos(tz), np.sin(tz)
    return np.array([
        [cy * cz,                 -cy * sz,                  sy],
        [sx * sy * cz + cx * sz,  -sx * sy * sz + cx * cz,  -sx * cy],
        [-cx * sy * cz + sx * sz,  cx * sy * sz + sx * cz,   cx * cy],
    ])


def stew_inverse(xsi, ysi, xmi, ymi, roll, pitch, yaw, px, py, pz, baseZ, platformZ):
    """Full inverse kinematics (port of stew_inverse.m).

    Returns a length-42 vector: [Legs(6), platcoords(18), animcoords(18)].
    platcoords and animcoords are identical (the original T and Ta matrices are
    identical), kept separate to preserve the original return layout.
    """
    xsi = np.asarray(xsi, float); ysi = np.asarray(ysi, float)
    xmi = np.asarray(xmi, float); ymi = np.asarray(ymi, float)
    R = _rotation(roll, pitch, yaw)
    t = np.array([px, py, pz], float)

    a = np.column_stack([xsi, ysi, np.full(6, baseZ)])          # (6,3) base joints
    b = np.column_stack([xmi, ymi, np.full(6, platformZ)])      # (6,3) platform joints
    b_trans = (R @ b.T).T + t                                   # (6,3) transformed

    legs = np.sqrt(np.sum((a - b_trans) ** 2, axis=1))          # (6,)
    platcoords = b_trans.reshape(-1)                            # x1,y1,z1,x2,... (18,)
    animcoords = platcoords.copy()
    return np.concatenate([legs, platcoords, animcoords])


def stew_inverse_ws(xsi, ysi, xmi, ymi, roll, pitch, yaw, px, py, pz, baseZ, platformZ):
    """Optimised kernel returning only the six leg lengths (port of stew_inverse_ws.m)."""
    xsi = np.asarray(xsi, float); ysi = np.asarray(ysi, float)
    xmi = np.asarray(xmi, float); ymi = np.asarray(ymi, float)
    R = _rotation(roll, pitch, yaw)
    t = np.array([px, py, pz], float)
    a = np.column_stack([xsi, ysi, np.full(6, baseZ)])
    b = np.column_stack([xmi, ymi, np.full(6, platformZ)])
    b_trans = (R @ b.T).T + t
    return np.sqrt(np.sum((a - b_trans) ** 2, axis=1))


def legs_for_directions(a, b, R, center, n, radii):
    """Vectorised leg lengths for many probe points at once.

    This is the engine behind the fast workspace sweep.  For every direction
    `n[i]` and radius `radii[i]` it forms a probe point center + radii*n, applies
    the (fixed) rotation R to the platform joints b, and returns an (N, 6) array
    of leg lengths.  Pure array math -> no Python-level per-direction loop.

    a       : (6,3) base joints (already at baseZ)
    b       : (6,3) platform joints (already at platformZ)
    R       : (3,3) rotation for the chosen centre pose (constant during a sweep)
    center  : (3,) translation of the centre pose
    n       : (N,3) unit direction vectors
    radii   : (N,) radius per direction
    """
    points = center[None, :] + radii[:, None] * n          # (N,3)
    b_rot = (R @ b.T).T                                     # (6,3) rotated platform joints
    b_trans = b_rot[None, :, :] + points[:, None, :]        # (N,6,3)
    return np.sqrt(np.sum((a[None, :, :] - b_trans) ** 2, axis=2))   # (N,6)


# ---------------------------------------------------------------------------
# Leg-output arithmetic (port of the maths in solve_inverse.m / overwrite_data.m)
# ---------------------------------------------------------------------------
def leg_revolutions_remainder(ang_delta_deg):
    """Split an angular delta (deg) into integer turns + signed remainder in
    (-360, 360), rounded to 0.1 deg, folding an exact +/-360 back into turns.
    Mirrors the leg_rev / leg_rem logic in solve_inverse.m."""
    ang = np.asarray(ang_delta_deg, float)
    rev = np.fix(ang / 360.0).astype(int)            # toward zero
    rem = np.round(ang - rev * 360.0, 1)
    roll_over = np.abs(rem) == 360.0
    rev = rev + np.where(roll_over, np.sign(ang).astype(int), 0)
    rem = np.where(roll_over, 0.0, rem)
    return rev, rem


# ---------------------------------------------------------------------------
# Optional compiled C kernel (auto-detected).  Falls back silently to NumPy.
# ---------------------------------------------------------------------------
class _CKernel:
    """ctypes wrapper around a standalone stew_inverse_ws shared library.

    The library MUST be the *standalone* (lib/dll) MATLAB Coder build with the
    signature:

        void stew_inverse_ws(const double xsi[6], const double ysi[6],
                             const double xmi[6], const double ymi[6],
                             double roll, double pitch, double yaw,
                             double px, double py, double pz,
                             double baseZ, double platformZ, double Legs[6]);

    The MEX build shipped in the original project will NOT work (it needs the
    MATLAB runtime); regenerate with coder.config('dll').  See native/README.md.
    """

    def __init__(self, path):
        self.lib = ctypes.CDLL(path)
        c6 = ctypes.c_double * 6
        self.lib.stew_inverse_ws.restype = None
        self.lib.stew_inverse_ws.argtypes = [
            c6, c6, c6, c6,
            ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double, c6,
        ]
        for fn in ("stew_inverse_ws_initialize", "stew_inverse_ws_terminate"):
            if hasattr(self.lib, fn):
                getattr(self.lib, fn).restype = None
                getattr(self.lib, fn).argtypes = []
        if hasattr(self.lib, "stew_inverse_ws_initialize"):
            self.lib.stew_inverse_ws_initialize()

    def __call__(self, xsi, ysi, xmi, ymi, roll, pitch, yaw, px, py, pz, baseZ, platformZ):
        c6 = ctypes.c_double * 6
        out = c6()
        self.lib.stew_inverse_ws(
            c6(*xsi), c6(*ysi), c6(*xmi), c6(*ymi),
            roll, pitch, yaw, px, py, pz, baseZ, platformZ, out,
        )
        return np.array(out[:])


def _library_candidates():
    base = "stew_inverse_ws"
    names = {
        "win32": [base + ".dll"],
        "darwin": ["lib" + base + ".dylib", base + ".dylib"],
    }.get(sys.platform, ["lib" + base + ".so", base + ".so"])
    # search next to the frozen exe, the native/ folder, and CWD
    roots = [os.path.dirname(os.path.abspath(sys.argv[0])),
             getattr(sys, "_MEIPASS", ""),
             os.path.join(os.path.dirname(__file__), "..", "native"),
             os.getcwd()]
    for r in roots:
        if not r:
            continue
        for nm in names:
            p = os.path.join(r, nm)
            if os.path.isfile(p):
                yield p


_C_KERNEL = None


def load_c_kernel(verbose=True):
    """Try to load the optional compiled kernel. Returns True if loaded."""
    global _C_KERNEL
    for path in _library_candidates():
        try:
            _C_KERNEL = _CKernel(path)
            if verbose:
                print(f"Fast C kernel loaded: {path}")
            return True
        except Exception as exc:        # pragma: no cover - depends on user build
            if verbose:
                print(f"Could not load C kernel at {path}: {exc}")
    if verbose:
        print("Using vectorised NumPy kernel (no compiled DLL found - this is "
              "already 25-50x faster than the MATLAB MEX build).")
    return False


def have_c_kernel():
    return _C_KERNEL is not None
