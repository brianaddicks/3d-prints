#!/usr/bin/env python3
"""Spiderweb light holder: a 2 inch wide winder with lips, a hook for the ring and slots for the plug.

The strand winds lengthwise around the two ends, in a channel on each face.
Written to spiderweb-light-holder.stl already turned 45 degrees, because the
winder only reaches its full length across the diagonal of the K1 bed.

Coordinates: x runs from the plug end (0) to the hook end (LENGTH), y across
the winder, z up from the bed.
"""
import math
from pathlib import Path

import manifold3d  # noqa: F401  trimesh's boolean engine
import trimesh
from shapely.geometry import Polygon, box

HERE = Path(__file__).parent

# Printer: Creality K1
BED = 220.0
BED_MARGIN = 4.0  # clear of each bed edge

# Winder
WIDTH = 50.8  # 2 inches
LENGTH = 264.0
CORNER = 8.0  # corners cut at 45 degrees, to fit into the bed corners
SADDLE = 3.0  # ends dip in the middle, so the wraps centre themselves
LIP_WIDTH = 4.0
BACK_DEPTH = 4.0  # channel on the underside
WEB = 4.0
TOP_DEPTH = 5.0  # channel on the top
SOLID_END_PLUG = 45.0  # underside is solid this far in from each end, so the
SOLID_END_HOOK = 50.0  # hook and slots print without supports

# Plug: NEMA 1-15 (US two-blade)
BLADE_SPACING = 12.7  # centre to centre, fixed by the standard
SLOT_WIDTH = 8.5  # both slots clear the 7.9 wide polarized blade, so it fits either way round
SLOT_THICKNESS = 1.9  # blades are about 1.5 thick. Reduce for a tighter grip.
LAND_HEIGHT = 16.0  # raised beside one lip, tall enough to take a whole blade
LAND_WIDTH = 16.0
LAND_START = 16.0
LAND_LENGTH = 24.0

# Hook: a tine inside a window. The ring goes through the window and around the tine,
# which points away from the plug so pulling the strand seats the ring.
WINDOW_FROM_END = 12.0
WINDOW_LENGTH = 30.0
WINDOW_WIDTH = 22.0
TINE_WIDTH = 6.0
TINE_GAP = 8.0  # tine tip to the far edge of the window
BARB = 2.0  # catch on each side of the tine tip

CHAMFER = 0.8
FOOT_CHAMFER = 0.3  # bottom edge, offsets elephant's foot
LAYER = 0.2

FLOOR_TOP = BACK_DEPTH + WEB
HEIGHT = FLOOR_TOP + TOP_DEPTH


def rounded(poly, radius):
    """Round the convex then the concave corners of a polygon."""
    return poly.buffer(-radius).buffer(2 * radius).buffer(-radius)


def outline():
    """2D outline, with cut corners and saddled ends."""
    half, narrow = WIDTH / 2, WIDTH / 2 - CORNER
    return rounded(
        Polygon(
            [
                (SADDLE, 0),
                (0, -narrow),
                (CORNER, -half),
                (LENGTH - CORNER, -half),
                (LENGTH, -narrow),
                (LENGTH - SADDLE, 0),
                (LENGTH, narrow),
                (LENGTH - CORNER, half),
                (CORNER, half),
                (0, narrow),
            ]
        ),
        1.0,
    )


def channel():
    """2D area between the lips, open at both ends. The lips follow the cut corners."""
    half = WIDTH / 2 - LIP_WIDTH
    end = WIDTH / 2 - CORNER - LIP_WIDTH * (math.sqrt(2) - 1)
    inset = half - end
    return Polygon(
        [
            (-1, end - 1),
            (inset, half),
            (LENGTH - inset, half),
            (LENGTH + 1, end - 1),
            (LENGTH + 1, -end + 1),
            (LENGTH - inset, -half),
            (inset, -half),
            (-1, -end + 1),
        ]
    )


def land():
    """Raised block for the plug, against the +y lip."""
    return box(LAND_START, WIDTH / 2 - LAND_WIDTH, LAND_START + LAND_LENGTH, WIDTH / 2).intersection(outline())


def slots():
    """Slot rectangles in the land, long side across the winder."""
    centre_y = WIDTH / 2 - LAND_WIDTH / 2
    first_x = LAND_START + (LAND_LENGTH - BLADE_SPACING) / 2
    return [
        box(x - SLOT_THICKNESS / 2, centre_y - SLOT_WIDTH / 2, x + SLOT_THICKNESS / 2, centre_y + SLOT_WIDTH / 2)
        for x in (first_x, first_x + BLADE_SPACING)
    ]


def window():
    """Hook window with the barbed tine left standing in it."""
    far = LENGTH - WINDOW_FROM_END
    near = far - WINDOW_LENGTH
    half = WINDOW_WIDTH / 2
    tip = far - TINE_GAP
    tine = TINE_WIDTH / 2
    return rounded(
        Polygon(
            [
                (near, -half),
                (far, -half),
                (far, half),
                (near, half),
                (near, tine),
                (tip - 6, tine),
                (tip - 3, tine + BARB),
                (tip, 0),
                (tip - 3, -tine - BARB),
                (tip - 6, -tine),
                (near, -tine),
            ]
        ),
        0.8,
    )


def extrude(poly, z0, z1):
    pieces = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in getattr(poly, "geoms", [poly])]
    mesh = trimesh.util.concatenate(pieces)
    mesh.apply_translation((0, 0, z0))
    return mesh


def prism(poly, height, z0=0.0):
    """Extrude with a stepped top chamfer at layer height, and a foot chamfer on the bed."""
    parts = []
    start = z0
    if z0 == 0:
        parts.append(extrude(poly.buffer(-FOOT_CHAMFER), 0, LAYER))
        start = LAYER
    parts.append(extrude(poly, start, height - CHAMFER))
    for i in range(int(round(CHAMFER / LAYER))):
        z = height - CHAMFER + i * LAYER
        parts.append(extrude(poly.buffer(-(i + 1) * LAYER), z, z + LAYER))
    return trimesh.boolean.union(parts, engine="manifold")


def cutter(poly, top):
    """Through cut with a relief at the bottom, so elephant's foot can't close it."""
    parts = [extrude(poly, -1, top + 1), extrude(poly.buffer(0.4, join_style=2), -1, 0.4)]
    return trimesh.boolean.union(parts, engine="manifold")


def build():
    shape = outline()
    between = channel()
    ends = box(-1, -30, SOLID_END_PLUG, 30).union(box(LENGTH - SOLID_END_HOOK, -30, LENGTH + 1, 30))
    parts = [
        prism(shape.difference(between), HEIGHT),  # lips
        extrude(shape, BACK_DEPTH, FLOOR_TOP),  # web
        prism(shape.intersection(ends), FLOOR_TOP),  # solid ends
        prism(land(), LAND_HEIGHT),
    ]
    part = trimesh.boolean.union(parts, engine="manifold")
    cuts = [cutter(s, LAND_HEIGHT) for s in slots()] + [cutter(window(), HEIGHT)]
    return trimesh.boolean.difference([part] + cuts, engine="manifold")


def place_on_bed(part):
    """Turn the winder onto the diagonal and centre it on the bed."""
    placed = part.copy()
    placed.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 4, (0, 0, 1)))
    lo, hi = placed.bounds
    placed.apply_translation((BED / 2 - (lo[0] + hi[0]) / 2, BED / 2 - (lo[1] + hi[1]) / 2, -lo[2]))
    return placed


def check(part, placed):
    lo, hi = placed.bounds
    size = hi - lo
    print(f"watertight       {placed.is_watertight}")
    print(f"size             {part.extents[0]:.1f} x {part.extents[1]:.1f} mm")
    print(f"footprint on bed {size[0]:.1f} x {size[1]:.1f} mm, height {size[2]:.1f} mm")
    print(f"clear of bed     {min(lo[0], lo[1], BED - hi[0], BED - hi[1]):.1f} mm")
    print(f"volume           {placed.volume / 1000:.1f} cm3 solid")
    assert placed.is_watertight
    assert lo[0] >= BED_MARGIN and lo[1] >= BED_MARGIN
    assert hi[0] <= BED - BED_MARGIN and hi[1] <= BED - BED_MARGIN


def main():
    part = build()
    placed = place_on_bed(part)
    check(part, placed)
    placed.export(HERE / "spiderweb-light-holder.stl")


if __name__ == "__main__":
    main()
