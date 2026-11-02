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
TOP_LIP = 2.5  # narrow, so the 42-45 mm ring lies flat between the lips
BACK_LIP = 4.0  # wider, as these are what sit on the bed
BACK_DEPTH = 4.0  # channel on the underside
WEB = 4.0
TOP_DEPTH = 8.0  # channel on the top
END_RIB = 5.0  # underside rib across each end, measured in from the saddle

# Plug: an inline adapter with NEMA 1-15 blades, measured from photos. Body about 70 long,
# 30 wide and 28-33 thick, blades about 15 long. It lies lengthwise with its blades pointing
# at the plug end, plugged into a block. The body sits above the lips, so the lips stay
# whole and the cable can still run under it.
BLADE_SPACING = 12.7  # centre to centre, fixed by the standard
SLOT_WIDTH = 8.5  # upright in the block. Clears the 7.9 wide polarized blade either way round.
SLOT_THICKNESS = 1.9  # blades are about 1.5 thick. Reduce for a tighter grip.
SLOT_DEPTH = 16.5
SLOT_Z = 33.0  # blade centre height. Half the 33 thick flange clears the 16 high lips.
SLOT_WALL = 3.0
BLOCK_START = 7.0
BLOCK_LENGTH = 19.0
BLOCK_HEIGHT = SLOT_Z + SLOT_WIDTH / 2 + SLOT_WALL

# Hook: rises from the channel floor and reaches toward the end. The ring (42-45 mm
# across, 2 mm wire, measured from a photo) lies flat around it, with its wire in the
# crotch under the hook, so pulling the strand toward the plug seats it. The underside
# rises at 45 degrees, so it prints without supports.
HOOK_FROM_END = 24.0  # end to the crotch
HOOK_WIDTH = 12.0
HOOK_THROAT = 5.0  # height and reach of the opening under the hook
HOOK_BACK = 6.0  # how far the base spreads toward the plug

CHAMFER = 0.8
FOOT_CHAMFER = 0.3  # bottom edge, offsets elephant's foot
LAYER = 0.2

FLOOR_TOP = BACK_DEPTH + WEB
HEIGHT = FLOOR_TOP + TOP_DEPTH
LIP_ALLOWANCE = 2.5  # extra block width outside the outer slot, over the lip


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


def channel(lip):
    """2D area between lips of this width, open at both ends. The lips follow the cut corners."""
    half = WIDTH / 2 - lip
    end = WIDTH / 2 - CORNER - lip * (math.sqrt(2) - 1)
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


def block_width():
    return BLADE_SPACING + SLOT_THICKNESS + 2 * SLOT_WALL + LIP_ALLOWANCE


def block():
    """Plug block at the plug end, against the +y edge."""
    return box(BLOCK_START, WIDTH / 2 - block_width(), BLOCK_START + BLOCK_LENGTH, WIDTH / 2)


def slot_cuts():
    """Horizontal blade slots, opening toward the middle of the winder, with a lead-in."""
    centre_y = WIDTH / 2 - block_width() + SLOT_WALL + SLOT_THICKNESS / 2 + BLADE_SPACING / 2
    face = BLOCK_START + BLOCK_LENGTH
    cuts = []
    for y in (centre_y - BLADE_SPACING / 2, centre_y + BLADE_SPACING / 2):
        slot = trimesh.creation.box(extents=(SLOT_DEPTH + 1, SLOT_THICKNESS, SLOT_WIDTH))
        slot.apply_translation((face - SLOT_DEPTH / 2 + 0.5, y, SLOT_Z))
        lead = trimesh.creation.box(extents=(1.2, SLOT_THICKNESS + 1.2, SLOT_WIDTH + 1.2))
        lead.apply_translation((face, y, SLOT_Z))
        cuts += [slot, lead]
    return cuts


def hook():
    """Hook on the channel floor, from its side profile. Its top is level with the lips."""
    crotch = LENGTH - HOOK_FROM_END
    profile = Polygon(
        [
            (crotch - HOOK_BACK, FLOOR_TOP - 0.5),
            (crotch, FLOOR_TOP - 0.5),
            (crotch, FLOOR_TOP),
            (crotch + HOOK_THROAT, FLOOR_TOP + HOOK_THROAT),
            (crotch + HOOK_THROAT, HEIGHT),
            (crotch - 1, HEIGHT),
            (crotch - HOOK_BACK, FLOOR_TOP),
        ]
    )
    mesh = trimesh.creation.extrude_polygon(profile, HOOK_WIDTH)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))
    mesh.apply_translation((0, HOOK_WIDTH / 2, 0))
    return mesh


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


def build():
    shape = outline()
    # Lips, plus a rib across each end that anchors the bridged floor on all four sides.
    ends = box(-1, -30, SADDLE + END_RIB, 30).union(box(LENGTH - SADDLE - END_RIB, -30, LENGTH + 1, 30))
    footing = shape.difference(channel(BACK_LIP).difference(ends)).buffer(-0.05).buffer(0.05)
    parts = [
        extrude(footing.buffer(-FOOT_CHAMFER), 0, LAYER),
        extrude(footing, LAYER, BACK_DEPTH + 0.5),
        extrude(shape, BACK_DEPTH, FLOOR_TOP),  # web
        prism(shape.difference(channel(TOP_LIP)), HEIGHT, FLOOR_TOP - 0.5),  # top lips
        prism(block().intersection(shape), BLOCK_HEIGHT, FLOOR_TOP - 0.5),
        hook(),
    ]
    part = trimesh.boolean.union(parts, engine="manifold")
    return trimesh.boolean.difference([part] + slot_cuts(), engine="manifold")


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
