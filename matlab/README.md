# MATLAB version

The original MATLAB implementation of the Hexapod IK & Workspace Calculator. This is
the reference version; the [Python port](../python/) and the Windows executable reproduce its math,
file formats, and workflow.

For the full description of what the tool does (geometry, IK, workspace analysis, screenshots), see
the [main README](../README.md).

## Requirements

- MATLAB **R2020b or later**, with GUI support
- 64-bit Windows (tested on Windows 11)
- The precompiled 64-bit MEX file `stew_inverse_ws_mex.mexw64` is included for fast workspace
  sweeps. (If MATLAB can't load it on your setup, regenerate it from `stew_inverse_ws.m` with
  MATLAB Coder, or the code falls back to the plain `.m` solver.)

## Run

1. Open MATLAB.
2. Set the working directory to this `matlab/` folder and add it (and subfolders) to the path.
3. Run:

   ```matlab
   >> RUN_HEXAPOD_CALCULATOR
   ```

## File overview

- `RUN_HEXAPOD_CALCULATOR.m` — main entry point
- `MAIN_GUI.m` — GUI layout and logic
- `solve_inverse.m`, `stew_inverse.m`, `stew_inverse_ws.m` — IK and workspace solvers
- `draw_*.m`, `export_*.m`, `anim_plat.m` — visualization and export
- `edit_*.m`, `handle_*.m`, `*_data.m`, `*_callback.m` — dialogs, save/load, and button handlers
- `formdata.txt` — platform/system configuration save file (auto-loaded on start)
- `*.mat` — example generated workspace data (reachable / orientation, NEW / RECALL)
- `stew_inverse_ws_mex.mexw64`, `codegen/` — compiled fast kernel and its generated sources
