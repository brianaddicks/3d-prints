#!/usr/bin/env python3
"""Render an STL laid out on the bed diagonal to a PNG: 3D views and a bed plan.

Uses a small software z-buffer, so it needs no GPU or display.

usage: render.py part.stl out.png [--bed 220]
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

BASE = np.array([0.95, 0.50, 0.10])
BACKGROUND = np.array([0.97, 0.97, 0.97])
EDGE = 0.45  # brightness kept along creases and outlines


def camera(elev, azim):
    """Rows are the view's right, up and towards-the-viewer axes."""
    e, a = np.radians(elev), np.radians(azim)
    toward = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    world_up = np.array([0.0, 0.0, 1.0]) if abs(toward[2]) < 0.99 else np.array([0.0, 1.0, 0.0])
    right = np.cross(world_up, toward)
    right /= np.linalg.norm(right)
    return np.array([right, np.cross(toward, right), toward])


def rasterize(mesh, elev, azim, width, height, centre=None, span=None):
    """Orthographic z-buffer render. centre and span zoom in, span is mm across the image."""
    view = camera(elev, azim)
    verts = mesh.vertices @ view.T
    if centre is None:
        origin = (verts.min(axis=0) + verts.max(axis=0)) / 2
    else:
        origin = np.asarray(centre) @ view.T
    if span is None:
        extent = verts.max(axis=0) - verts.min(axis=0)
        span = max(extent[0], extent[1] * width / height) * 1.06
    scale = width / span
    px = (verts[:, 0] - origin[0]) * scale + width / 2
    py = height / 2 - (verts[:, 1] - origin[1]) * scale
    pz = verts[:, 2]

    normals = mesh.face_normals @ view.T
    # Key light from the upper left, plus a soft fill so nothing goes black.
    key = np.array([-0.45, 0.55, 0.70])
    key /= np.linalg.norm(key)
    light = 0.38 + 0.62 * np.clip(normals @ key, 0, 1)

    depth = np.full((height, width), -np.inf)
    shade = np.zeros((height, width))
    ids = np.full((height, width), -1, dtype=int)
    for index, face in enumerate(mesh.faces):
        if normals[index, 2] <= 0:
            continue
        x0, x1, x2 = px[face]
        y0, y1, y2 = py[face]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        left, right = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 2, width)
        top, bottom = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 2, height)
        if left >= right or top >= bottom:
            continue
        xs, ys = np.meshgrid(np.arange(left, right) + 0.5, np.arange(top, bottom) + 0.5)
        w0 = ((x1 - xs) * (y2 - ys) - (x2 - xs) * (y1 - ys)) / area
        w1 = ((x2 - xs) * (y0 - ys) - (x0 - xs) * (y2 - ys)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        z = w0 * pz[face[0]] + w1 * pz[face[1]] + w2 * pz[face[2]]
        window = (slice(top, bottom), slice(left, right))
        nearer = inside & (z > depth[window])
        depth[window][nearer] = z[nearer]
        shade[window][nearer] = light[index]
        ids[window][nearer] = index

    # Darken outlines and creases, found where the surface normal jumps between pixels.
    hit = ids >= 0
    pixel_normals = np.zeros((height, width, 3))
    pixel_normals[hit] = normals[ids[hit]]
    edges = np.zeros((height, width), dtype=bool)
    for axis in (0, 1):
        jump = np.linalg.norm(np.diff(pixel_normals, axis=axis), axis=2) > 0.25
        outline = np.diff(hit.astype(int), axis=axis) != 0
        mark = jump | outline
        if axis == 0:
            edges[:-1, :] |= mark
        else:
            edges[:, :-1] |= mark

    image = np.tile(BACKGROUND, (height, width, 1))
    image[hit] = shade[hit, None] * BASE
    image[edges & hit] *= EDGE
    return image


def panel(fig, slot, mesh, elev, azim, title, centre=None, span=None, supersample=2):
    ax = fig.add_subplot(slot)
    bbox = ax.get_position()
    w_in, h_in = fig.get_size_inches() * (bbox.width, bbox.height)
    width = int(w_in * fig.dpi * supersample)
    height = int(h_in * fig.dpi * supersample)
    image = rasterize(mesh, elev, azim, width, height, centre, span)
    ax.imshow(image, interpolation="antialiased")
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)


def bed_plan(ax, mesh, bed):
    ax.add_patch(plt.Rectangle((0, 0), bed, bed, fc="#eeeeee", ec="#555555", lw=1.2, zorder=1))
    for v in range(20, int(bed), 20):
        ax.plot([v, v], [0, bed], color="#d8d8d8", lw=0.6, zorder=2)
        ax.plot([0, bed], [v, v], color="#d8d8d8", lw=0.6, zorder=2)
    up = mesh.face_normals[:, 2] > 0.5
    ax.tripcolor(
        mesh.vertices[:, 0],
        mesh.vertices[:, 1],
        mesh.faces[up],
        facecolors=np.ones(up.sum()),
        cmap=matplotlib.colors.ListedColormap([BASE]),
        shading="flat",
        zorder=3,
    )
    lo, hi = mesh.bounds
    clear = min(lo[0], lo[1], bed - hi[0], bed - hi[1])
    ax.set_title(f"On the {bed:.0f} x {bed:.0f} mm K1 bed, {clear:.1f} mm clear of the edges", fontsize=11)
    ax.set_xlim(-5, bed + 5)
    ax.set_ylim(-5, bed + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("mm")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stl")
    parser.add_argument("png")
    parser.add_argument("--bed", type=float, default=220.0)
    args = parser.parse_args()

    mesh = trimesh.load(args.stl, force="mesh")
    # Turn back off the bed diagonal for the 3D views, so the long axis runs along x.
    flat = mesh.copy()
    flat.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 4, (0, 0, 1)))
    flat.apply_translation((-flat.bounds[0][0], -flat.bounds.mean(axis=0)[1], -flat.bounds[0][2]))
    length = flat.extents[0]

    fig = plt.figure(figsize=(15, 10), dpi=130)
    grid = fig.add_gridspec(2, 3, left=0.02, right=0.98, top=0.95, bottom=0.03, wspace=0.05, hspace=0.2)
    width = flat.extents[1]
    panel(fig, grid[0, :2], flat, 35, -80, f"Overall, {length:.0f} x {width:.0f} mm")
    bed_plan(fig.add_subplot(grid[0, 2]), mesh, args.bed)
    panel(fig, grid[1, 0], flat, 20, 30, "Plug block, looking toward the plug end", (28, 8, 20), 70)
    panel(fig, grid[1, 1], flat, 28, 25, "Hook end, looking in from the end", (length - 24, 0, 10), 60)
    panel(fig, grid[1, 2], flat, -35, -80, "Underside", None, None)
    fig.savefig(args.png)


if __name__ == "__main__":
    main()
