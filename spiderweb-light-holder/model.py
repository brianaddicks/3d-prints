#!/usr/bin/env python3
"""Spiderweb light holder: a two-part winder with deep channels, a hook for the ring and a plug block.

The strand winds lengthwise around the two ends, in a channel on each face. The holder is
two parts, each as long as the K1 bed diagonal allows, that slide together and click.

Writes, beside this file:
  holder-plug-end.stl   the plug end, already turned onto the bed diagonal
  holder-hook-end.stl   the hook end, already turned onto the bed diagonal
  build/assembled.stl   both parts in place, for the render (not for printing)

Coordinates: x runs from the plug end (0) to the hook end, y across the holder, z up from
the bed. The joint is at x = JOINT.

Print with supports on the build plate only: the underside channel's floor spans the
channel 20 mm above the bed.
"""
import math
from pathlib import Path

import manifold3d  # noqa: F401  trimesh's boolean engine
import trimesh
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent

# Printer: Creality K1
BED = 220.0
BED_MARGIN = 7.5  # clear of each bed edge. OrcaSlicer rejects parts much closer once supports are on.

# Cross-section
CHANNEL = 75.8  # between the lips. 3 cm wider than the first holder, for the bulk of the strand.
LIP = 3.5
LIP_HEIGHT = 20.0  # above the web, on each face
WEB = 4.0
WIDTH = CHANNEL + 2 * LIP
FLOOR_BOTTOM = LIP_HEIGHT  # underside of the web
FLOOR_TOP = LIP_HEIGHT + WEB
HEIGHT = FLOOR_TOP + LIP_HEIGHT

# Outer ends
CORNER = 20.0  # corners cut at 45 degrees, to fit into the bed corners
SADDLE = 3.0  # ends dip in the middle, so the wraps centre themselves

# Joint: the hook end drops onto the plug end from above. Dovetails in the web take the
# strand's pull, and the lips overlap in halves, with a bump that clicks into a dimple.
TAIL_LENGTH = 10.0
TAIL_NECK = 10.0
TAIL_HEAD = 16.0
TAIL_Y = (-25.0, 0.0, 25.0)
LAP = 10.0  # length of the overlapping lip halves
CLEARANCE = 0.25
BUMP = 0.5  # how far the click bump stands proud

# Hook: rises from the top channel floor and reaches toward the end. The ring (42-45 mm
# across, 2 mm wire, measured from a photo) lies flat around it with its wire in the crotch,
# so pulling the strand toward the plug seats it. Its underside rises at 45 degrees.
HOOK_FROM_END = 30.0  # outer end to the crotch
HOOK_WIDTH = 12.0
HOOK_THROAT = 5.0
HOOK_BACK = 6.0
HOOK_TOP = FLOOR_TOP + HOOK_THROAT + 3.0

# Plug: an inline adapter with NEMA 1-15 blades, measured from photos. Body about 70 long,
# 30 wide and 28-33 thick, blades about 15 long. Its blades point at the plug end and plug
# into a block on the outside of the +y lip, so the body sits beside the holder.
BLADE_SPACING = 12.7  # centre to centre, fixed by the standard
SLOT_WIDTH = 8.5  # upright. Clears the 7.9 wide polarized blade either way round.
SLOT_THICKNESS = 1.9  # blades are about 1.5 thick. Reduce for a tighter grip.
SLOT_DEPTH = 16.5
SLOT_WALL = 3.0
PLUG_CLEARANCE = 16.5  # lip to the middle of the plug body, half its width plus a little
BLOCK_START = 60.0
BLOCK_LENGTH = 19.0
SLOT_Z = HEIGHT / 2

CHAMFER = 0.8
FOOT_CHAMFER = 0.3  # bottom edge, offsets elephant's foot
LAYER = 0.2

HALF = WIDTH / 2


def rounded(poly, radius):
    """Round the convex then the concave corners of a polygon."""
    return poly.buffer(-radius).buffer(2 * radius).buffer(-radius)


def end_profile(x_end, inward):
    """Points for an outer end with cut corners and a saddle. inward is +1 at x=0, -1 at the far end."""
    narrow = HALF - CORNER
    return [
        (x_end + inward * CORNER, -HALF),
        (x_end, -narrow),
        (x_end + inward * SADDLE, 0),
        (x_end, narrow),
        (x_end + inward * CORNER, HALF),
    ]


def plug_outline(joint):
    """Plug end part, from x=0 to the joint. The joint end stays square."""
    far = [(joint, HALF), (joint, -HALF)]
    pts = end_profile(0, 1)
    poly = Polygon([pts[4], pts[3], pts[2], pts[1], pts[0]] + far[::-1])
    return rounded(poly, 1.0).union(box(joint - 3, -HALF, joint, HALF)).intersection(poly)


def hook_outline(joint, total):
    """Hook end part, from the joint to x=total."""
    pts = end_profile(total, -1)
    poly = Polygon([(joint, -HALF)] + pts + [(joint, HALF)])
    return rounded(poly, 1.0).union(box(joint, -HALF, joint + 3, HALF)).intersection(poly)


def channel(total):
    """2D area between the lips, open at both ends. The lips follow the cut corners."""
    inner = HALF - LIP
    end = HALF - CORNER - LIP * (math.sqrt(2) - 1)
    inset = inner - end
    return Polygon(
        [
            (-1, end - 1),
            (inset, inner),
            (total - inset, inner),
            (total + 1, end - 1),
            (total + 1, -end + 1),
            (total - inset, -inner),
            (inset, -inner),
            (-1, -end + 1),
        ]
    )


def lip_halves(x0, x1, outer, edge=HALF + 1):
    """Strips along both lips for the lap joint: the outer or inner half of each lip."""
    split = HALF - LIP / 2
    if outer:
        spans = [(split + CLEARANCE / 2, edge)]
    else:
        spans = [(HALF - LIP, split - CLEARANCE / 2)]
    strips = []
    for lo, hi in spans:
        strips.append(box(x0, lo, x1, hi))
        strips.append(box(x0, -hi, x1, -lo))
    return unary_union(strips)


def tails(joint, grow=0.0):
    """Dovetails on the hook end part, reaching back over the plug end part."""
    shapes = []
    for y in TAIL_Y:
        neck, head = TAIL_NECK / 2 + grow, TAIL_HEAD / 2 + grow
        shapes.append(
            Polygon(
                [
                    (joint + 1, y - neck),
                    (joint, y - neck),
                    (joint - TAIL_LENGTH - grow, y - head),
                    (joint - TAIL_LENGTH - grow, y + head),
                    (joint, y + neck),
                    (joint + 1, y + neck),
                ]
            )
        )
    return unary_union(shapes)


def block():
    """Plug block on the outside of the +y lip."""
    width = PLUG_CLEARANCE + BLADE_SPACING / 2 + SLOT_THICKNESS / 2 + SLOT_WALL
    return box(BLOCK_START, HALF - 0.5, BLOCK_START + BLOCK_LENGTH, HALF + width)


def slot_cuts():
    """Horizontal blade slots in the block, opening toward the hook end, with a lead-in."""
    centre_y = HALF + PLUG_CLEARANCE
    face = BLOCK_START + BLOCK_LENGTH
    cuts = []
    for y in (centre_y - BLADE_SPACING / 2, centre_y + BLADE_SPACING / 2):
        slot = trimesh.creation.box(extents=(SLOT_DEPTH + 1, SLOT_THICKNESS, SLOT_WIDTH))
        slot.apply_translation((face - SLOT_DEPTH / 2 + 0.5, y, SLOT_Z))
        lead = trimesh.creation.box(extents=(1.2, SLOT_THICKNESS + 1.2, SLOT_WIDTH + 1.2))
        lead.apply_translation((face, y, SLOT_Z))
        cuts += [slot, lead]
    return cuts


def extrude(poly, z0, z1):
    pieces = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in getattr(poly, "geoms", [poly]) if p.area > 0.01]
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


def hook(total):
    """Hook on the top channel floor, from its side profile."""
    crotch = total - HOOK_FROM_END
    profile = Polygon(
        [
            (crotch - HOOK_BACK, FLOOR_TOP - 0.5),
            (crotch, FLOOR_TOP - 0.5),
            (crotch, FLOOR_TOP),
            (crotch + HOOK_THROAT, FLOOR_TOP + HOOK_THROAT),
            (crotch + HOOK_THROAT, HOOK_TOP),
            (crotch - 1, HOOK_TOP),
            (crotch - HOOK_BACK, FLOOR_TOP),
        ]
    )
    mesh = trimesh.creation.extrude_polygon(profile, HOOK_WIDTH)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))
    mesh.apply_translation((0, HOOK_WIDTH / 2, 0))
    return mesh


def click(joint, dimple):
    """Bump on the inner lip half of the hook end part, or the dimple it clicks into."""
    radius = 1.6 if dimple else 1.3
    y_face = HALF - LIP / 2
    spheres = []
    for sign in (1, -1):
        s = trimesh.creation.icosphere(subdivisions=3, radius=radius)
        s.apply_translation((joint - LAP / 2, sign * (y_face + BUMP - radius + (0.2 if dimple else 0)), SLOT_Z))
        spheres.append(s)
    return spheres


def plug_part(joint, total):
    outline = plug_outline(joint)
    lips = outline.difference(channel(total))
    lips = lips.difference(lip_halves(joint - LAP, joint + 1, outer=False))
    lips = lips.union(lip_halves(joint - 0.5, joint + LAP - CLEARANCE, outer=True, edge=HALF))
    web = outline.difference(tails(joint, CLEARANCE))
    web = web.difference(lip_halves(joint - LAP - CLEARANCE, joint + 1, outer=False).buffer(CLEARANCE))
    parts = [
        prism(clean(lips), HEIGHT),
        extrude(clean(web), FLOOR_BOTTOM, FLOOR_TOP),
        prism(block(), HEIGHT),
    ]
    part = trimesh.boolean.union(parts, engine="manifold")
    return trimesh.boolean.difference([part] + slot_cuts() + click(joint, dimple=True), engine="manifold")


def hook_part(joint, total):
    outline = hook_outline(joint, total)
    lips = outline.difference(channel(total))
    lips = lips.difference(lip_halves(joint, joint + LAP, outer=True))
    lips = lips.union(lip_halves(joint - LAP + CLEARANCE, joint + 0.5, outer=False))
    web = outline.union(tails(joint))
    web = web.difference(lip_halves(joint - 1, joint + LAP + CLEARANCE, outer=True).buffer(CLEARANCE))
    parts = [prism(clean(lips), HEIGHT), extrude(clean(web), FLOOR_BOTTOM, FLOOR_TOP), hook(total)]
    parts += click(joint, dimple=False)
    return trimesh.boolean.union(parts, engine="manifold")


def clean(poly):
    """Merge touching pieces and drop slivers, so every extrusion is a closed volume."""
    return poly.buffer(0.02, join_style=2).buffer(-0.04, join_style=2).buffer(0.02, join_style=2)


def turned(poly):
    return affinity.rotate(poly, 45, origin=(0, 0))


def fits(footprint):
    lo_x, lo_y, hi_x, hi_y = turned(footprint).bounds
    return hi_x - lo_x <= BED - 2 * BED_MARGIN and hi_y - lo_y <= BED - 2 * BED_MARGIN


def longest(make):
    """Longest length in 0.5 mm steps whose footprint still fits the bed."""
    length = 150.0
    while fits(make(length + 0.5)):
        length += 0.5
    return length


def plan():
    plug_len = longest(lambda n: plug_outline(n).union(block()).union(box(n, -HALF, n + LAP, HALF)))
    hook_len = longest(lambda n: hook_outline(0, n).union(box(-LAP, -HALF, 0, HALF)))
    return plug_len, plug_len + hook_len


def place_on_bed(part):
    """Turn a part onto the bed diagonal and centre it."""
    placed = part.copy()
    placed.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 4, (0, 0, 1)))
    lo, hi = placed.bounds
    placed.apply_translation((BED / 2 - (lo[0] + hi[0]) / 2, BED / 2 - (lo[1] + hi[1]) / 2, -lo[2]))
    return placed


def check(name, placed):
    lo, hi = placed.bounds
    clear = min(lo[0], lo[1], BED - hi[0], BED - hi[1])
    print(f"{name:10} watertight {placed.is_watertight}, height {hi[2] - lo[2]:.1f} mm, "
          f"{clear:.1f} mm clear of the bed edges, {placed.volume / 1000:.1f} cm3 solid")
    assert placed.is_watertight
    assert clear >= BED_MARGIN - 0.01


def main():
    joint, total = plan()
    plug = plug_part(joint, total)
    hooked = hook_part(joint, total)
    print(f"assembled  {total:.1f} x {WIDTH:.1f} mm, {HEIGHT:.1f} mm thick, joint at {joint:.1f} mm")
    for name, part in (("plug-end", plug), ("hook-end", hooked)):
        placed = place_on_bed(part)
        check(name, placed)
        placed.export(HERE / f"holder-{name}.stl")
    (HERE / "build").mkdir(exist_ok=True)
    trimesh.util.concatenate([plug, hooked]).export(HERE / "build" / "assembled.stl")
    overlap = trimesh.boolean.intersection([plug, hooked], engine="manifold")
    print(f"overlap    {overlap.volume:.1f} mm3 where the parts meet (the click bump only, ideally)")


if __name__ == "__main__":
    main()
