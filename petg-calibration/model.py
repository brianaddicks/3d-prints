#!/usr/bin/env python3
"""Temperature tower for tuning a PETG spool on the K1.

Six 10 mm blocks, hottest at the bottom. Each block has its temperature engraved on the
front, a 45 degree overhang on the left, and a 4 mm post 8 mm to the right joined by a
bridge at the top of the block. Strings across the gap, a droopy overhang or a saggy
bridge show which temperature is too hot; weak layers or a rough surface show too cold.

The slicer prints everything at TEMPS[0]; set_temps.py adds the M104 changes per block.

  temp-tower.stl   the tower, standing as printed
"""
from pathlib import Path

import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent

TEMPS = (250, 245, 240, 235, 230, 225)  # bottom to top
BASE_T = 1.0
BLOCK_H = 10.0
CORE_W, CORE_D = 20.0, 10.0
OVERHANG = 6.0  # out and up, so 45 degrees
GAP = 8.0  # bridge span and stringing gap
POST = 4.0
BRIDGE_T = 1.0
ENGRAVE = 0.6
TEXT_H = 5.0


def block_start(i):
    return BASE_T + i * BLOCK_H


def extrude(poly, z0, z1):
    pieces = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in getattr(poly, "geoms", [poly]) if p.area > 0.01]
    mesh = trimesh.util.concatenate(pieces)
    mesh.apply_translation((0, 0, z0))
    return mesh


def side_prism(poly_xz, y0, y1):
    """Extrude a polygon drawn in (x, z) along y from y0 to y1."""
    m = extrude(poly_xz, 0, y1 - y0)  # built in (x, y=z_wall, z=y_wall)
    m.apply_transform([[1, 0, 0, 0], [0, 0, 1, y0], [0, 1, 0, 0], [0, 0, 0, 1]])
    if m.volume < 0:
        m.invert()
    return m


def text_outline(s, x0, z0, height):
    path = TextPath((0, 0), s, size=height * 1.4, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    shape = Polygon()
    for ring in path.to_polygons():
        if len(ring) >= 3:
            shape = shape.symmetric_difference(Polygon(ring).buffer(0))
    minx, minz, maxx, maxz = shape.bounds
    k = height / (maxz - minz)
    from shapely import affinity
    shape = affinity.scale(shape, k, k, origin=(minx, minz))
    return affinity.translate(shape, x0 - minx, z0 - minz).simplify(0.01)


def tower():
    top = block_start(len(TEMPS))
    post_x = CORE_W + GAP
    parts = [extrude(box(0, -2, post_x + POST, CORE_D + 2), 0, BASE_T),
             extrude(box(0, 0, CORE_W, CORE_D), BASE_T, top),
             extrude(box(post_x, (CORE_D - POST) / 2, post_x + POST, (CORE_D + POST) / 2), BASE_T, top)]
    cuts = []
    for i, t in enumerate(TEMPS):
        z0, z1 = block_start(i), block_start(i) + BLOCK_H
        wing = Polygon([(0, z0), (-OVERHANG, z0 + OVERHANG), (-OVERHANG, z1), (0, z1)])
        parts.append(side_prism(wing, 0, CORE_D))
        parts.append(extrude(box(CORE_W - 0.5, (CORE_D - POST) / 2, post_x + 0.5, (CORE_D + POST) / 2), z1 - BRIDGE_T, z1))
        label = text_outline(str(t), 3.0, z0 + (BLOCK_H - TEXT_H) / 2, TEXT_H)
        cuts.append(side_prism(label, -1.0, ENGRAVE))
    body = trimesh.boolean.union(parts, engine="manifold")
    return trimesh.boolean.difference([body] + cuts, engine="manifold")


def main():
    m = tower()
    lo, hi = m.bounds
    m.apply_translation((110 - (lo[0] + hi[0]) / 2, 110 - (lo[1] + hi[1]) / 2, -lo[2]))
    lo, hi = m.bounds
    print(f"tower watertight {m.is_watertight}, {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm")
    assert m.is_watertight
    m.export(HERE / "temp-tower.stl")
    (HERE / "build").mkdir(exist_ok=True)
    m.export(HERE / "build" / "assembled.stl")


if __name__ == "__main__":
    main()
