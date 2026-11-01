#!/usr/bin/env python3
"""Spiderweb light holder: a flat bar with a hook for the ring and slots for the plug.

Written to spiderweb-light-holder.stl already turned 45 degrees, because the bar
only reaches its full length across the diagonal of the K1 bed.

Bar coordinates: x runs from the plug end (0) to the hook tip (OVERALL_LENGTH),
y across the bar, z up from the bed.
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

# Plug: NEMA 1-15 (US two-blade)
BLADE_SPACING = 12.7  # centre to centre, fixed by the standard
SLOT_WIDTH = 8.5  # both slots clear the 7.9 wide polarized blade, so it fits either way round
SLOT_THICKNESS = 1.9  # blades are about 1.5 thick. Reduce for a tighter grip.
FIRST_SLOT_X = 11.0

# Bar
OVERALL_LENGTH = 298.0
BAR_WIDTH = 16.0
BAR_HEIGHT = 8.0
PAD_WIDTH = 18.0
PAD_HEIGHT = 12.0  # taller at the plug so the blades can't rock
PAD_FLAT_END = 40.0
PAD_RAMP_END = 54.0

# Hook: the ring goes over the tine and its wire seats in the notch.
# The notch opens away from the plug, so pulling the strand tight seats the ring.
TINE_WIDTH = 6.5
TINE_Y = -1.0  # close to the bar axis, where the bed corner leaves the most room
NOTCH_WIDTH = 7.0
NOTCH_DEPTH = 26.0  # tine tip to notch floor
LIP_LENGTH = 9.0  # how far the outer wall stands above the notch floor
LIP_WIDTH = 4.5
BARB = 2.2  # catch on the tine tip, keeps the ring on when the strand goes slack

CHAMFER = 0.8
FOOT_CHAMFER = 0.3  # bottom edge, offsets elephant's foot
LAYER = 0.2


def rounded(poly, radius):
    """Round the convex then the concave corners of a polygon."""
    return poly.buffer(-radius).buffer(2 * radius).buffer(-radius)


def outline():
    """2D outline of the bar, with the slots left out."""
    half_bar, half_pad = BAR_WIDTH / 2, PAD_WIDTH / 2
    tip = OVERALL_LENGTH
    floor_x = tip - NOTCH_DEPTH
    tine_lo, tine_hi = TINE_Y - TINE_WIDTH / 2, TINE_Y + TINE_WIDTH / 2
    notch_hi = tine_hi + NOTCH_WIDTH
    lip_hi = notch_hi + LIP_WIDTH

    body = Polygon(
        [
            # plug end comes to a point, to fit into the bed corner
            (0, 0),
            (half_pad, -half_pad),
            (PAD_FLAT_END, -half_pad),
            (PAD_RAMP_END, -half_bar),
            (floor_x - 16, -half_bar),
            # outer side of the tine
            (floor_x + 4, tine_lo),
            (tip - 4, tine_lo),
            (tip, TINE_Y),
            # barb on the tine tip, its underside faces the notch
            (tip - 3, tine_hi + BARB),
            (tip - 8, tine_hi),
            # notch
            (floor_x, tine_hi),
            (floor_x, notch_hi),
            # lip
            (floor_x + LIP_LENGTH, notch_hi),
            (floor_x + LIP_LENGTH, lip_hi),
            (floor_x - 14, half_bar),
            (PAD_RAMP_END, half_bar),
            (PAD_FLAT_END, half_pad),
            (half_pad, half_pad),
        ]
    )
    return rounded(body, 1.0)


def slots():
    """Slot rectangles, long side across the bar so the blade faces take the strand's pull."""
    return [
        box(x - SLOT_THICKNESS / 2, -SLOT_WIDTH / 2, x + SLOT_THICKNESS / 2, SLOT_WIDTH / 2)
        for x in (FIRST_SLOT_X, FIRST_SLOT_X + BLADE_SPACING)
    ]


def extrude(poly, z0, z1):
    mesh = trimesh.creation.extrude_polygon(poly, z1 - z0)
    mesh.apply_translation((0, 0, z0))
    return mesh


def prism(poly, height):
    """Extrude with a bottom foot chamfer and a stepped top chamfer at layer height."""
    parts = [extrude(poly.buffer(-FOOT_CHAMFER), 0, LAYER)]
    parts.append(extrude(poly, LAYER, height - CHAMFER))
    steps = int(round(CHAMFER / LAYER))
    for i in range(steps):
        z = height - CHAMFER + i * LAYER
        parts.append(extrude(poly.buffer(-(i + 1) * LAYER), z, z + LAYER))
    return trimesh.boolean.union(parts, engine="manifold")


def side_wedge():
    """Side profile of the plug pad: flat, then ramping down to bar height."""
    profile = Polygon(
        [
            (-1, 0),
            (PAD_RAMP_END + 1, 0),
            (PAD_RAMP_END + 1, BAR_HEIGHT - 1),
            (PAD_RAMP_END, BAR_HEIGHT - 1),
            (PAD_FLAT_END, PAD_HEIGHT),
            (-1, PAD_HEIGHT),
        ]
    )
    mesh = trimesh.creation.extrude_polygon(profile, PAD_WIDTH + 4)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))
    mesh.apply_translation((0, PAD_WIDTH / 2 + 2, 0))
    return mesh


def slot_cutter(poly):
    """Through slot with a lead-in at the top and a relief at the bottom."""
    parts = [
        extrude(poly, -1, PAD_HEIGHT + 1),
        extrude(poly.buffer(0.4, join_style=2), -1, 0.4),
        extrude(poly.buffer(0.6, join_style=2), PAD_HEIGHT - 0.6, PAD_HEIGHT + 1),
    ]
    return trimesh.boolean.union(parts, engine="manifold")


def build():
    shape = outline()
    bar = prism(shape, BAR_HEIGHT)
    pad_region = shape.intersection(box(-1, -20, PAD_RAMP_END, 20))
    pad = trimesh.boolean.intersection([prism(pad_region, PAD_HEIGHT), side_wedge()], engine="manifold")
    part = trimesh.boolean.union([bar, pad], engine="manifold")
    return trimesh.boolean.difference([part] + [slot_cutter(s) for s in slots()], engine="manifold")


def place_on_bed(part):
    """Turn the bar onto the diagonal and centre it on the bed."""
    placed = part.copy()
    placed.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 4, (0, 0, 1)))
    lo, hi = placed.bounds
    placed.apply_translation((BED / 2 - (lo[0] + hi[0]) / 2, BED / 2 - (lo[1] + hi[1]) / 2, -lo[2]))
    return placed


def check(part, placed):
    lo, hi = placed.bounds
    size = hi - lo
    print(f"watertight       {placed.is_watertight}")
    print(f"overall length   {part.extents[0]:.1f} mm")
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
