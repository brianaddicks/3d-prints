#!/usr/bin/env python3
"""Downstairs thermostat wall plate for an ecobee Smart Thermostat Premium, with a sun hood.

The old owners cut a notch in the wall paneling, 121 wide, 80 tall and 18 deep. The plate fills the notch with a hollow plug and laps onto the
paneling with a flange big enough to frame the ecobee (104 mm square). The sun comes
from the top and left, so an L-shaped hood stands off the top and left edges.

Two parts, both printed without supports:
  plate.stl   face down on the bed, plug pointing up
  hood.stl    standing on the edge that meets the plate
  build/assembled.stl   both in place, for the render (not for printing)

Coordinates (assembled): x right, y up, z out of the wall. The paneling face is z = 0.
The notch centre is x = y = 0.

Mounting: four countersunk screws through the face into the notch floor, hidden under
the ecobee. The ecobee's own back plate screws straight into the 5 mm face: mark its
holes, drill 2.5 mm pilots. The hood sits flat on the face along the top and left edges
and is located and held with #4 x 1/2" flat-head screws driven from the back before the plate goes on
the wall.
"""
from pathlib import Path

import manifold3d  # noqa: F401  trimesh's boolean engine
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent

# Notch, from the photos
NOTCH_W, NOTCH_H, NOTCH_D = 121.0, 80.0, 18.0  # remeasured 2026-11-14
FIT = 0.5  # clearance on each side of the plug
PLUG_W, PLUG_H = NOTCH_W - 2 * FIT, NOTCH_H - 2 * FIT
PLUG_DEPTH = NOTCH_D - 1.0  # stops short of the floor so the face always seats on the paneling
PLUG_WALL = 3.0

# Face plate: frames the 104 mm ecobee
FACE_W, FACE_H, FACE_T = 160.0, 120.0, 5.0
FACE_RADIUS = 4.0
FRONT_CHAMFER = 1.0
WIRE_SLOT = (36.0, 20.0)

# Wall screws: #6 or #8 flat head, under the ecobee
WALL_SCREWS = [(sx * 45.0, sy * 24.0) for sx in (-1, 1) for sy in (-1, 1)]
WALL_HOLE, WALL_HEAD, BOSS = 4.6, 9.0, 10.0

# Hood: top and left, deeper at the top-left corner where the sun comes from
HOOD_T = 5.0
HOOD_TOP_DEPTH = 45.0  # out from the face; the ecobee stands about 26 mm proud
HOOD_LEFT_BOTTOM_DEPTH = 22.0  # the left side tapers down to this at the bottom
RABBET = 0.0  # no recess: the plate prints face down, and a rabbet at the edge would float over the bed
HOOD_FIT = 0.2
HOOD_SCREW_PILOT, HOOD_SCREW_HOLE, HOOD_SCREW_HEAD = 2.0, 3.2, 6.5
HOOD_SCREWS_TOP = (-55.0, 0.0, 55.0)
HOOD_SCREWS_LEFT = (-30.0, 25.0)

LAYER = 0.2
X0, X1, Y0, Y1 = -FACE_W / 2, FACE_W / 2, -FACE_H / 2, FACE_H / 2


def rounded_box(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, resolution=16)


def extrude(poly, z0, z1):
    pieces = [trimesh.creation.extrude_polygon(p, z1 - z0) for p in getattr(poly, "geoms", [poly]) if p.area > 0.01]
    mesh = trimesh.util.concatenate(pieces)
    mesh.apply_translation((0, 0, z0))
    return mesh


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def diff(base, cuts):
    return trimesh.boolean.difference([base] + cuts, engine="manifold")


def countersink(x, y, hole, head, z_head, toward):
    """A clearance hole through everything plus a 90 degree cone, its wide end at z_head.

    toward is +1 when the head faces +z (front), -1 when it faces -z (back)."""
    shaft = trimesh.creation.cylinder(radius=hole / 2, height=200, sections=32)
    shaft.apply_translation((x, y, 0))
    depth = (head - hole) / 2
    cone = trimesh.creation.cone(radius=head / 2 + 0.01, height=head / 2 + 0.01, sections=32)
    if toward > 0:
        cone.apply_transform(trimesh.transformations.rotation_matrix(3.14159265, (1, 0, 0)))
        cone.apply_translation((x, y, z_head + 0.01))
    else:
        cone.apply_translation((x, y, z_head - 0.01))
    del depth
    return [shaft, cone]


def hood_footprint(grow=0.0):
    """The L the hood stands on, flush with the plate's top and left edges."""
    top = box(X0, Y1 - HOOD_T - grow, X1, Y1 + 1)
    left = box(X0 - 1, Y0, X0 + HOOD_T + grow, Y1 + 1)
    return unary_union([top, left]).intersection(rounded_box(FACE_W, FACE_H, FACE_RADIUS).buffer(grow))


def hood_screw_points():
    pts = [(x, Y1 - HOOD_T / 2) for x in HOOD_SCREWS_TOP]
    pts += [(X0 + HOOD_T / 2, y) for y in HOOD_SCREWS_LEFT]
    return pts


def plate():
    outline = rounded_box(FACE_W, FACE_H, FACE_RADIUS)
    # Face, with a chamfer on the front edge stepped at layer height (it prints on the bed).
    parts = []
    steps = int(round(FRONT_CHAMFER / LAYER))
    for i in range(steps):
        z = FACE_T - (i + 1) * LAYER
        parts.append(extrude(outline.buffer(-(steps - i) * LAYER), z, z + LAYER))
    parts.append(extrude(outline, 0, FACE_T - FRONT_CHAMFER))

    # Hollow plug, open at the back.
    plug = rounded_box(PLUG_W, PLUG_H, 1.5)
    ring = plug.difference(rounded_box(PLUG_W - 2 * PLUG_WALL, PLUG_H - 2 * PLUG_WALL, 0.5))
    parts.append(extrude(ring, -PLUG_DEPTH, 0.01))
    for x, y in WALL_SCREWS:
        parts.append(extrude(Point(x, y).buffer(BOSS / 2, resolution=16), -PLUG_DEPTH, 0.01))
    body = union(parts)

    cuts = [extrude(box(-WIRE_SLOT[0] / 2, -WIRE_SLOT[1] / 2, WIRE_SLOT[0] / 2, WIRE_SLOT[1] / 2).buffer(3), -50, 50)]
    for x, y in WALL_SCREWS:
        cuts += countersink(x, y, WALL_HOLE, WALL_HEAD, FACE_T, +1)
    # Rabbet for the hood along the top and left edges.
    cuts.append(extrude(hood_footprint(HOOD_FIT), FACE_T - RABBET, FACE_T + 10))
    # Hood screws come in from the back of the flange; their heads sit flush against the paneling.
    for x, y in hood_screw_points():
        cuts += countersink(x, y, HOOD_SCREW_HOLE, HOOD_SCREW_HEAD, 0.0, -1)
    return diff(body, cuts)


def hood():
    """L-shaped hood. Its profile is drawn in the wall frame, then lifted out of the face."""
    base_z = FACE_T - RABBET
    # Top wing: full depth across the top.
    top = box(X0, Y1 - HOOD_T, X1, Y1)
    top_mesh = extrude(top, base_z, base_z + HOOD_TOP_DEPTH)
    # Left wing: tapers from full depth at the top to HOOD_LEFT_BOTTOM_DEPTH at the bottom.
    side = Polygon([
        (Y0, 0), (Y1, 0), (Y1, HOOD_TOP_DEPTH), (Y0, HOOD_LEFT_BOTTOM_DEPTH),
    ])  # (y, depth)
    left = trimesh.creation.extrude_polygon(side, HOOD_T)
    # extrude_polygon builds in (x=y_wall, y=depth, z=thickness); map to (x=X0+t, y, z=base+depth)
    left.apply_transform([
        [0, 0, 1, X0],
        [1, 0, 0, 0],
        [0, 1, 0, base_z],
        [0, 0, 0, 1],
    ])
    if left.volume < 0:
        left.invert()
    body = union([top_mesh, left])
    # Round the outer corner to match the plate, and the free edges lightly.
    keep = extrude(rounded_box(FACE_W, FACE_H, FACE_RADIUS), base_z - 1, base_z + HOOD_TOP_DEPTH + 1)
    body = trimesh.boolean.intersection([body, keep], engine="manifold")
    cuts = []
    for x, y in hood_screw_points():
        pilot = trimesh.creation.cylinder(radius=HOOD_SCREW_PILOT / 2, height=2 * 12.0, sections=24)
        pilot.apply_translation((x, y, base_z))
        cuts.append(pilot)
    return diff(body, cuts)


def lay_plate(mesh):
    """Face down on the bed: flip z, centre on the bed."""
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(3.14159265, (0, 1, 0)))
    return to_bed(m)


def lay_hood(mesh):
    """Stand the hood on the edge that meets the plate (it already points +z)."""
    return to_bed(mesh.copy())


def to_bed(m, bed=220.0):
    lo, hi = m.bounds
    m.apply_translation((bed / 2 - (lo[0] + hi[0]) / 2, bed / 2 - (lo[1] + hi[1]) / 2, -lo[2]))
    return m


def check(name, m, bed=220.0):
    lo, hi = m.bounds
    clear = min(lo[0], lo[1], bed - hi[0], bed - hi[1])
    print(f"{name:6} watertight {m.is_watertight}, {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} x {hi[2]-lo[2]:.1f} mm, "
          f"{clear:.1f} mm clear of the bed edges, {m.volume / 1000:.1f} cm3")
    assert m.is_watertight
    assert clear >= 14.0


def main():
    p, h = plate(), hood()
    overlap = trimesh.boolean.intersection([p, h], engine="manifold").volume
    print(f"overlap between plate and hood: {overlap:.2f} mm3 (should be 0)")
    for name, mesh, lay in (("plate", p, lay_plate), ("hood", h, lay_hood)):
        placed = lay(mesh)
        check(name, placed)
        placed.export(HERE / f"{name}.stl")
    (HERE / "build").mkdir(exist_ok=True)
    assembled = trimesh.util.concatenate([p, h])
    # Stand it up as on the wall (z up, the room toward -y) so the render shows it from the room.
    assembled.apply_transform(trimesh.transformations.rotation_matrix(3.14159265 / 2, (1, 0, 0)))
    assembled.export(HERE / "build" / "assembled.stl")


if __name__ == "__main__":
    main()
