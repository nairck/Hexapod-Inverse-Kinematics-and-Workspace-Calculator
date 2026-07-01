# Hexapod Inverse Kinematics & Workspace Calculator

Compute and visualize the **inverse kinematics (IK)** and **workspace** of a **6-6 Gough-Stewart
platform** (a *hexapod*). Given a commanded pose, it solves the six actuator (leg) lengths needed
to reach it, draws the mechanism, and maps its **reachable** (translational) and **orientation**
(rotational) workspaces. The "6-6" denotes six independent base joints and six independent platform
joints: the solver assumes a **fully general geometry with no symmetry requirement**, so any valid
joint layout is supported.

Originally a MATLAB tool by **Joe Brown** (CSU Sacramento, 2006); adapted and extended by
**Adam B. Johnson** (University of Victoria, 2022–2025) to align the SPIDERS instrument on the
Subaru Telescope. The figures below are from the associated dissertation (see [References](#references)).

## Versions

All three implementations share the same math and the same file formats (`formdata.txt` settings and
`.mat`/`.npz` workspace data), so results and saved files are interchangeable.

| Version | Best for | Location |
|---|---|---|
| **Windows executable** | Running on Windows with no install — no MATLAB or Python | [Releases](../../releases) → `HexapodCalculator.exe` |
| **MATLAB** | MATLAB users; the original reference implementation | [`matlab/`](matlab/) |
| **Python** | macOS/Linux, building your own binary, or modifying the source | [`python/`](python/) |

The Windows executable is built from the Python version, which additionally provides a docked output
console, light/dark/system themes, a startup splash, per-window icons, and non-blocking
workspace/PNG rendering. Prebuilt macOS/Linux binaries are not provided — the Python version can
build them, but those builds are currently untested.

## Getting started

**Windows 10/11:** 
- Download `HexapodCalculator.exe` from [Releases](../../releases) and run it. SmartScreen
may warn about an unrecognized app (the executable is unsigned); choose *More info → Run anyway*. A
default `formdata.txt` is created next to the executable on first launch.

**MATLAB:** 
- Open MATLAB (R2020b or later), `cd` into [`matlab/`](matlab/), add the folder to the
path, and run:

```matlab
RUN_HEXAPOD_CALCULATOR
```

**Python** (3.11 or 3.12):

```bash
cd python
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

To build a standalone binary, run `build_windows.bat`, `./build_macos.sh`, or `./build_linux.sh`.
See [`python/README.md`](python/README.md) for build options and details.

## How it works

### Geometry and inverse kinematics

![Hexapod geometry](docs/figures/figure-2-14-platform-geometry.png)

The mechanism is defined by six base joints **aᵢ** and six platform joints **bᵢ**, each with a planar
(X, Y) position and a plane height. A commanded pose is a translation **p** plus a ZYX Euler rotation
(yaw, pitch, roll). Each platform joint is mapped into the global frame by the homogeneous transform
**T** = (**R**, **p**), and each leg length is its distance to the corresponding base joint:

```
Lᵢ = ‖aᵢ − T·bᵢ‖        (i = 1 … 6)
```

The solution {L₁ … L₆} defines the pose. Saved leg lengths then serve as the reference for the
**relative** adjustment needed to reach any new pose.

### Interface

![Calculator interface](docs/figures/figure-2-16-calculator-interface.png)

*The calculator at the home configuration.* **Inputs** are the zero-displacement (home) joint
coordinates and plane heights, the workspace search limits and pose/leg-length constraints, and the
commanded offset in X, Y, Z, roll, pitch, and yaw. **Outputs** are the absolute and relative
leg-length changes with their equivalent turnbuckle revolutions and residual angle, a live 3D drawing
of the hexapod, and controls to save the configuration and to draw or export the workspaces.

![IK output](docs/figures/figure-2-17-ik-output.png)

*IK output.* Each leg's change is colour-coded against the configured limits (green = valid,
red = out of range) and converted into actuator revolutions and a residual angle, giving the
turnbuckle adjustment for manual alignment.

### Workspace analysis

Two complementary workspaces are mapped from the same IK. Each boundary is found by a radial-bisection
search over a spherical grid, refined out to the actuator stroke limits. The search can start from the
home, new, or old pose, at a selectable resolution that trades speed against fidelity.

![Workspace resolution and pose selection](docs/figures/figure-2-18-workspace-resolution.png)

![Reachable workspace](docs/figures/figure-2-19-reachable-workspace.png)

*Reachable workspace* — the attainable X, Y, Z translations at fixed orientation. For a symmetric
hexapod at the home pose it forms a hexagonal bipyramid.

![Orientation workspace](docs/figures/figure-2-20-orientation-workspace.png)

*Orientation workspace* — the attainable roll, pitch, and yaw at fixed position: a dome-like volume
shaped by the actuator limits.

![Adjusted workspaces](docs/figures/figure-2-21-adjusted-workspaces.png)

Both workspaces can be re-evaluated after a pose change to assess its effect on reachability.

![PNG export](docs/figures/figure-2-22-png-export.png)

*Export.* Workspaces are saved as data files and can be exported as PNG images — optionally as a
series of evenly spaced viewing angles for assembling rotation videos.

## Repository layout

```
matlab/         Original MATLAB program (RUN_HEXAPOD_CALCULATOR.m + solvers, GUI, MEX)
python/         Cross-platform Python/Qt port (source, build scripts, PyInstaller spec)
docs/figures/   Figures used in this README
```

The Windows executable is distributed via Releases rather than committed to the repository;
`.gitignore` excludes build artifacts (`build/`, `dist/`, `.venv/`).

## References

1. J. Brown, *Stewart Platform Forward Kinematics Solver*, CSU Sacramento, 2006.
   <https://github.com/jotux/Steward-Platform-Forward-Kinematics-Solver>
2. A. B. Johnson, *Beyond the speckles: New horizons in high-contrast imaging for exoplanet science*,
   Ph.D. dissertation, University of Victoria, 2025. <https://hdl.handle.net/1828/22655>
