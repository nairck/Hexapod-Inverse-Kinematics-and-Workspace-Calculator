"""Render the workspace alpha-shape surface and export PNG rotation series.

Port of the rendering half of draw_reachable_workspace_spherical.m /
draw_orientation_workspace_spherical.m and of export_reachable_workspace.m /
export_orientation_workspace.m.

MATLAB opened these as their own figure windows (figure 500/600), so this port
opens a separate, non-blocking pyvistaqt window for the interactive surface, and
renders the PNG series off-screen at the original 1650x1000 size.

MATLAB alphaShape + boundaryFacets maps onto PyVista's
delaunay_3d(alpha=...).extract_surface(); shading interp / phong / turbo /
FaceAlpha 0.6 / camlight headlight all have direct PyVista equivalents.
"""
from __future__ import annotations
import os
import numpy as np

from . import config
from . import workspace as W

_OPEN_WINDOWS = []        # keep references so interactive windows aren't GC'd


def _downsample_for_surface(pts, alpha):
    """Uniformly subsample a large boundary cloud down to config.MAX_SURFACE_PTS
    so VTK's Delaunay/alpha-shape stays fast (the full cloud is still used for
    the reported limits).  The alpha-ball radius is scaled up by the cube root of
    the density reduction so the surface still closes over the sparser points."""
    pts = np.asarray(pts, float)
    n = len(pts)
    cap = config.MAX_SURFACE_PTS
    if n <= cap:
        return pts, alpha
    idx = np.random.default_rng(0).choice(n, size=cap, replace=False)
    sub = pts[idx]
    factor = (n / len(sub)) ** (1.0 / 3.0)
    return sub, alpha * factor


def _build_surface(data, alpha):
    """Build the workspace surface.

    Preferred: a clean structured grid mesh straight from the spherical search
    grid (artifact-free at any resolution).  Fallback (e.g. for externally
    produced .mat data that isn't a recognised grid): the alpha-shape on a
    downsampled cloud, as before.
    """
    import pyvista as pv
    mesh = W.structured_mesh(data)
    if mesh is not None:
        verts, faces = mesh
        f = np.empty((len(faces), 4), np.int64)
        f[:, 0] = 3
        f[:, 1:] = faces
        return pv.PolyData(verts, f.ravel())

    pts, _ = W.dataset_points(data)
    sub, eff = _downsample_for_surface(pts, alpha)
    cloud = pv.PolyData(np.asarray(sub, float))
    try:
        surf = cloud.delaunay_3d(alpha=float(eff)).extract_surface()
        if surf.n_points == 0:
            raise ValueError("empty alpha surface")
        return surf
    except Exception:
        verts, faces = W.alpha_surface(sub, eff)
        if len(faces) == 0:
            return pv.PolyData(np.asarray(sub, float))
        f = np.hstack([np.full((len(faces), 1), 3), faces]).astype(np.int64).ravel()
        return pv.PolyData(verts, f)


def _set_view(plotter, azimuth_deg, elevation_deg):
    """Point the camera at the data centre from a clean (azimuth, elevation).

    azimuth is measured CCW from +X in the XY plane and elevation above the XY
    plane (so e.g. (-45, 22.5) is an isometric corner tilted 22.5 deg down), with
    +Z up.  Setting the camera position directly (then reset_camera to frame the
    data) is far more predictable than chaining azimuth/elevation increments.
    """
    import numpy as np
    try:
        b = plotter.bounds
        cx, cy, cz = 0.5 * (b[0] + b[1]), 0.5 * (b[2] + b[3]), 0.5 * (b[4] + b[5])
        span = max(b[1] - b[0], b[3] - b[2], b[5] - b[4]) or 1.0
    except Exception:
        cx = cy = cz = 0.0
        span = 1.0
    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    pos = np.array([cx, cy, cz]) + d * span * 2.5
    try:
        plotter.camera_position = [tuple(pos), (cx, cy, cz), (0.0, 0.0, 1.0)]
        plotter.reset_camera()
    except Exception:
        pass


def _theme_colors():
    """Background / foreground colours for the 3D view, following the app theme.

    Only the *black* theme darkens the figure (black background, white text, axis
    lines and bounding-box labels).  White and System both keep the original
    white background with black text / grey grid.
    """
    mode = config.get_theme()
    if mode == "black":
        return dict(bg="black", fg="white", fg_rgb=(1.0, 1.0, 1.0),
                    grid="white", scatter=(0.75, 0.75, 0.75))
    return dict(bg="white", fg="black", fg_rgb=(0.0, 0.0, 0.0),
                grid="gray", scatter=(0.55, 0.55, 0.55))


def _show_grid(plotter, labels, color):
    lx, ly, lz = labels
    try:
        plotter.remove_bounds_axes()      # avoid stacking a 2nd grid on re-theme
    except Exception:
        pass
    try:
        plotter.show_grid(color=color, xtitle=lx, ytitle=ly, ztitle=lz)
    except TypeError:
        plotter.show_grid(color=color)


def _populate(plotter, data, kind, alpha, labels):
    import pyvista as pv
    pts, (xl, yl, zl) = W.dataset_points(data)        # full cloud -> reported limits
    surf = _build_surface(data, alpha)                # clean structured surface
    col = _theme_colors()

    # lit, turbo-coloured, semi-transparent surface (== MATLAB patch + shading interp)
    if surf.n_points:
        surf["height"] = surf.points[:, 2]
    plotter.add_mesh(surf, scalars="height" if surf.n_points else None,
                     cmap="turbo", opacity=0.6, smooth_shading=True,
                     show_scalar_bar=False, lighting=True, specular=0.4,
                     specular_power=15)

    # faint boundary-point scatter, capped (== MATLAB scatter3 downsample)
    total = len(pts)
    cap = config.MAX_SCATTER_PTS
    step = 1 if total <= cap else int(np.ceil(total / cap))
    scat = plotter.add_points(pts[::step], color=col["scatter"], opacity=0.25,
                              point_size=3, render_points_as_spheres=True)

    # coordinate axis lines (== MATLAB plot3 axes to half the limit)
    axis_actors = [
        plotter.add_mesh(pv.Line((0, 0, 0), (0.5 * max(xl[1], 1e-6), 0, 0)), color=col["fg"], line_width=5),
        plotter.add_mesh(pv.Line((0, 0, 0), (0, 0.5 * max(yl[1], 1e-6), 0)), color=col["fg"], line_width=5),
        plotter.add_mesh(pv.Line((0, 0, 0), (0, 0, 0.5 * max(zl[1], 1e-6))), color=col["fg"], line_width=5),
    ]

    # limits annotation box (upper-right) + orientation widget (lower-left)
    lx, ly, lz = labels
    txt = (f"{lx} = [{xl[0]:.3f}, {xl[1]:.3f}]\n"
           f"{ly} = [{yl[0]:.3f}, {yl[1]:.3f}]\n"
           f"{lz} = [{zl[0]:.3f}, {zl[1]:.3f}]")
    txt_actor = plotter.add_text(txt, position="upper_right", font_size=11, color=col["fg"])
    plotter.add_axes(xlabel=lx, ylabel=ly, zlabel=lz)

    plotter.set_background(col["bg"])
    try:
        plotter.remove_all_lights()
        plotter.add_light(pv.Light(light_type="headlight"))
    except Exception:
        pass
    # Parallel (orthographic) projection by default, and label the bounding-box
    # axes with the workspace's own quantities (Roll/Pitch/Yaw, not X/Y/Z).
    try:
        plotter.enable_parallel_projection()
    except Exception:
        pass
    _show_grid(plotter, labels, col["grid"])

    # stash themeable handles so the window can be re-themed live
    plotter._wsv_theme = dict(axis=axis_actors, scatter=scat, text=txt_actor, labels=labels)
    return pts


def apply_theme_to_open():
    """Re-theme every open interactive workspace window to the current app theme."""
    col = _theme_colors()
    css = config.qt_stylesheet()
    for plotter in list(_OPEN_WINDOWS):
        try:
            try:
                plotter.app_window.setStyleSheet(css)      # menu / tool-bar chrome
            except Exception:
                pass
            plotter.set_background(col["bg"])
            th = getattr(plotter, "_wsv_theme", None)
            if th:
                for a in th["axis"]:
                    try:
                        a.prop.color = col["fg_rgb"]
                    except Exception:
                        pass
                try:
                    th["scatter"].prop.color = col["scatter"]
                except Exception:
                    pass
                try:
                    th["text"].GetTextProperty().SetColor(*col["fg_rgb"])
                except Exception:
                    pass
                _show_grid(plotter, th["labels"], col["grid"])
            plotter.render()
        except Exception:
            pass


def _labels_for(kind):
    if kind == "reachable":
        return ("X [mm]", "Y [mm]", "Z [mm]")
    return ("Roll [deg]", "Pitch [deg]", "Yaw [deg]")


def _install_menu(plotter, reset_view, default_parallel=True):
    """Replace the default menu with a clean File/View menu.

    Removes the confusing 'Export to VTKjs/HTML' items and offers a simple
    PNG/JPEG screenshot, a real 'Reset View', and a parallel-projection toggle.
    The interactive toolbar (camera tools) is kept.
    """
    try:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QFileDialog
        win = plotter.app_window
        mb = win.menuBar()
        mb.clear()

        filem = mb.addMenu("File")
        act_shot = QAction("Save Screenshot (PNG / JPG)\u2026", win)

        def save_shot():
            fn, _ = QFileDialog.getSaveFileName(
                win, "Save screenshot", "workspace.png",
                "PNG image (*.png);;JPEG image (*.jpg *.jpeg)")
            if fn:
                try:
                    plotter.screenshot(fn)
                    print(f"screenshot saved: {fn}")
                except Exception as exc:
                    print(f"screenshot failed: {exc}")

        act_shot.triggered.connect(save_shot)
        filem.addAction(act_shot)
        filem.addSeparator()
        act_close = QAction("Close", win)
        act_close.triggered.connect(win.close)
        filem.addAction(act_close)

        viewm = mb.addMenu("View")
        act_reset = QAction("Reset View", win)
        act_reset.triggered.connect(reset_view)
        viewm.addAction(act_reset)
        act_par = QAction("Parallel Projection", win)
        act_par.setCheckable(True)
        act_par.setChecked(default_parallel)

        def toggle_par(on):
            try:
                plotter.enable_parallel_projection() if on else plotter.disable_parallel_projection()
                plotter.render()
            except Exception:
                pass

        act_par.toggled.connect(toggle_par)
        viewm.addAction(act_par)
    except Exception:
        pass


def show_interactive(data, kind=None, alpha=None, res_label=None):
    """Open a separate, non-blocking interactive surface window.

    res_label (e.g. "Low"/"Medium"/"High"/"Recalled") is shown in the window
    title bar, e.g. "Orientation Workspace - LOW Resolution".
    """
    from pyvistaqt import BackgroundPlotter
    kind = kind or data.get("kind", "reachable")
    if alpha is None:
        alpha = config.ALPHA_REACHABLE if kind == "reachable" else config.ALPHA_ORIENTATION
    view = config.VIEW_REACHABLE if kind == "reachable" else config.VIEW_ORIENTATION
    base = "Reachable Workspace" if kind == "reachable" else "Orientation Workspace"
    if res_label and res_label.lower() == "recalled":
        title = f"{base} - Recalled Data"
    elif res_label:
        title = f"{base} - {res_label.upper()} Resolution"
    else:
        title = base

    # Build our own menu (menu_bar=False) so the default 'Export to VTKjs' is
    # gone; keep the toolbar (camera tools); drop the scene-tree editor panel.
    try:
        plotter = BackgroundPlotter(title=title, window_size=(1100, 750),
                                    menu_bar=False, editor=False)
    except TypeError:
        plotter = BackgroundPlotter(title=title, window_size=(1100, 750))

    _populate(plotter, data, kind, alpha, _labels_for(kind))
    _set_view(plotter, *view)
    try:
        plotter.enable_parallel_projection()
    except Exception:
        pass

    # Remove the "Save Camera Position" / "Clear Cameras" toolbar (keep the
    # standard camera-view buttons).
    try:
        bar = getattr(plotter, "saved_cameras_tool_bar", None)
        if bar is not None:
            plotter.app_window.removeToolBar(bar)
            bar.setVisible(False)
    except Exception:
        pass

    def reset_view():
        # Go back to the exact default isometric view the window started at.
        _set_view(plotter, *view)
        try:
            plotter.enable_parallel_projection()
            plotter.render()
        except Exception:
            pass

    # Re-point the toolbar "Reset" camera button (next to Isometric) at our
    # default-view reset, so it matches the View > Reset View menu item.
    try:
        tb = getattr(plotter, "default_camera_tool_bar", None)
        if tb is not None:
            for act in tb.actions():
                label = (act.text() or "") + " " + (act.toolTip() or "")
                if "reset" in label.strip().lower():
                    try:
                        act.triggered.disconnect()
                    except Exception:
                        pass
                    act.triggered.connect(lambda *_: reset_view())
    except Exception:
        pass

    _install_menu(plotter, reset_view, default_parallel=True)

    # Window / taskbar icon (same as the main app icon).
    try:
        from PySide6.QtGui import QIcon
        ipath = config.icon_path()
        if ipath:
            plotter.app_window.setWindowIcon(QIcon(ipath))
    except Exception:
        pass
    # Match the current colour theme (menu / tool-bar chrome).
    try:
        plotter.app_window.setStyleSheet(config.qt_stylesheet())
    except Exception:
        pass
    plotter.app_window.show()
    _OPEN_WINDOWS.append(plotter)
    return plotter


def export_png_series(data, out_dir, n_images, kind=None, alpha=None, progress=None):
    """Render N PNGs at evenly spaced view angles (== the MATLAB PNG exporter).

    N=90 -> 90 images at 4 deg increments, N=1 -> single standard view, etc.
    """
    import pyvista as pv
    kind = kind or data.get("kind", "reachable")
    if alpha is None:
        alpha = config.ALPHA_REACHABLE_EXPORT if kind == "reachable" else config.ALPHA_ORIENTATION
    base_view = config.VIEW_REACHABLE if kind == "reachable" else config.VIEW_ORIENTATION
    os.makedirs(out_dir, exist_ok=True)

    plotter = pv.Plotter(off_screen=True, window_size=list(config.EXPORT_SIZE))
    _populate(plotter, data, kind, alpha, _labels_for(kind))

    n_images = int(n_images)
    step = 360.0 / n_images
    paths = []
    for i in range(n_images):
        # MATLAB: for i = 1:360/N:360, view(base_az + i, el) -> N views over a full turn
        az = base_view[0] + i * step
        _set_view(plotter, az, base_view[1])
        fname = os.path.join(out_dir, f"{kind}_workspace_{i + 1:03d}.png")
        plotter.screenshot(fname)
        paths.append(fname)
        if progress:
            progress(f"... exported image {i + 1}/{n_images}: {os.path.basename(fname)}")
    plotter.close()
    if progress:
        progress(f"...PNG export complete: {n_images} image(s) in {out_dir}")
    return paths
