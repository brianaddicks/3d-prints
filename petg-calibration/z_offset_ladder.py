#!/usr/bin/env python3
"""Z-offset ladder: five single-layer 30 mm squares, each printed with the nozzle lower.

Each square is its own STL so OrcaSlicer labels it as a separate object; set_z_offsets.py
then puts a SET_GCODE_OFFSET before each one. Square n has n notches on its front edge.

    square   notches   Z offset
    1        1          0.00
    2        2         -0.03
    3        3         -0.06
    4        4         -0.09
    5        5         -0.12

Pick the square whose lines are pressed flat and fused, without ridges or a scraped look.
"""
from pathlib import Path

import trimesh
from shapely.geometry import box

HERE = Path(__file__).parent
OFFSETS = (0.0, -0.03, -0.06, -0.09, -0.12)
SIZE = 30.0
GAP = 10.0
LAYER = 0.2
BED = 220.0


def square(n, x0, y0):
    shape = box(x0, y0, x0 + SIZE, y0 + SIZE)
    for i in range(n):
        nx = x0 + SIZE / 2 + (i - (n - 1) / 2) * 4.0
        shape = shape.difference(box(nx - 0.8, y0 - 1, nx + 0.8, y0 + 3))
    m = trimesh.creation.extrude_polygon(shape, LAYER)
    return m


def main():
    total = len(OFFSETS) * SIZE + (len(OFFSETS) - 1) * GAP
    x = (BED - total) / 2
    y = (BED - SIZE) / 2
    for n in range(1, len(OFFSETS) + 1):
        m = square(n, x, y)
        name = f"z-ladder-{n}.stl"
        m.export(HERE / "build" / name)
        print(name, m.is_watertight, f"x {x:.0f}-{x + SIZE:.0f}", f"offset {OFFSETS[n - 1]:+.2f}")
        x += SIZE + GAP


if __name__ == "__main__":
    (HERE / "build").mkdir(exist_ok=True)
    main()
