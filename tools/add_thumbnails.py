#!/usr/bin/env python3
"""Embed preview thumbnails in a G-code file sliced by OrcaSlicer's command line.

Run headless, OrcaSlicer skips its thumbnails, so Moonraker, Fluidd and the Home Assistant
"Part preview" card have no picture. This renders the STL(s) with render.py's rasterizer and
writes 96x96 and 300x300 PNGs into the G-code the way OrcaSlicer does.

usage: add_thumbnails.py in.gcode out.gcode part.stl [more.stl ...]
"""
import base64
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).parent))
from render import BACKGROUND, rasterize  # noqa: E402

SIZES = (96, 300)
SUPERSAMPLE = 3


def thumbnail(mesh, size):
    big = size * SUPERSAMPLE
    rgb = rasterize(mesh, 30, -60, big, big)
    alpha = (np.abs(rgb - BACKGROUND).sum(axis=2) > 1e-6).astype(float)
    rgba = np.dstack([rgb, alpha]).reshape(size, SUPERSAMPLE, size, SUPERSAMPLE, 4).mean(axis=(1, 3))
    # Undo the background bleed at the edges so the outline doesn't get a pale fringe.
    covered = rgba[..., 3:4] > 0
    rgba[..., :3] = np.where(covered, (rgba[..., :3] - (1 - rgba[..., 3:4]) * BACKGROUND) / np.maximum(rgba[..., 3:4], 1e-6), 0)
    buf = io.BytesIO()
    plt.imsave(buf, np.clip(rgba, 0, 1), format="png")
    return buf.getvalue()


def block(meshes):
    mesh = trimesh.util.concatenate(meshes)
    lines = ["; THUMBNAIL_BLOCK_START\n"]
    for size in SIZES:
        data = base64.b64encode(thumbnail(mesh, size)).decode()
        lines += [";\n", f"; thumbnail begin {size}x{size} {len(data)}\n"]
        lines += [f"; {data[i:i + 78]}\n" for i in range(0, len(data), 78)]
        lines.append("; thumbnail end\n")
    lines.append("; THUMBNAIL_BLOCK_END\n")
    return lines


def main(src, dst, stls):
    text = open(src).readlines()
    if any(line.startswith("; thumbnail begin") for line in text[:2000]):
        sys.exit(f"{src} already has thumbnails")
    meshes = [trimesh.load(s, force="mesh") for s in stls]
    at = next((i + 1 for i, line in enumerate(text[:200]) if line.startswith("; HEADER_BLOCK_END")), 0)
    open(dst, "w").writelines(text[:at] + ["\n"] + block(meshes) + text[at:])
    print(f"{dst}: added {', '.join(f'{s}x{s}' for s in SIZES)} thumbnails")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
