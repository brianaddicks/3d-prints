"""Press-fit pegs and matching holes, tested on the K1 in PETG.

A peg is a 2.6 mm teardrop post; its hole is the same shape grown by a clearance on every
side. The teardrop lets a peg print lying sideways without supports: point the tip at the
bed. A peg printed standing up doesn't need the tip (pass point=None), but the teardrop
version fits the same holes either way.

Tested 2026-11-15 (thermostat-wall-plate/fit_test.py, Inland black PETG at 240 C,
0.20 mm layers, 4 walls):

    clearance per side   result
    0.05 mm              not one of the holes that fit
    0.10 mm              fits well (the default)
    0.15 mm              fits well

The pegs in that test printed rough, so smooth pegs may feel a little looser.

Printing tips, learned the hard way:
  - Standing up is the cleanest peg. Sideways ones come out rougher even as teardrops.
  - A lone peg prints lumpy: each layer takes under a second, so the plastic never sets.
    Print several parts at once, or use the side fan (40%) and a 10 mm/s minimum speed.
  - Keep the peg 0.5 mm shorter than the hole is deep so it can't bottom out.

Everything is drawn with the peg's axis along z. Rotate the mesh into place afterwards.

    import sys; sys.path.insert(0, "../lib")
    import pegs
    body = union([body, pegs.peg(x, y, z0=-4.5, z1=0.5)])
    plate = difference([plate, pegs.hole(x, y, z0=-1, z1=6)])
"""
import math

import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

DIAMETER = 2.6
FIT = 0.10  # clearance per side; see the table above
TIP = 1.2  # the teardrop's tip is cut off this many radii from the centre


def profile(x, y, d=DIAMETER, grow=0.0, point=(0.0, 1.0), tip=TIP):
    """The peg's cross-section around (x, y).

    point is the direction the teardrop's tip faces, which should be down when the peg
    prints lying sideways, or None for a plain circle. grow adds clearance on every side.
    """
    r = d / 2
    shape = Point(x, y).buffer(r, resolution=24)
    if point is not None:
        k = r / 2 ** 0.5
        drop = Polygon([(x - k, y + k), (x + k, y + k), (x, y + r * 2 ** 0.5)])
        shape = unary_union([shape, drop]).intersection(box(x - r, y - r, x + r, y + tip * r))
        angle = math.degrees(math.atan2(point[1], point[0])) - 90.0
        if abs(angle) > 1e-9:
            shape = affinity.rotate(shape, angle, origin=(x, y))
    if grow:
        shape = shape.buffer(grow, resolution=24)
    return shape.simplify(0.005)  # drops near-duplicate vertices that break the extrusion


def _extrude(shape, z0, z1):
    mesh = trimesh.creation.extrude_polygon(shape, z1 - z0)
    mesh.apply_translation((0, 0, z0))
    return mesh


def peg(x, y, z0, z1, **kw):
    """A peg from z0 to z1. Overlap the part it grows from by about 0.5 mm."""
    return _extrude(profile(x, y, **kw), z0, z1)


def hole(x, y, z0, z1, fit=FIT, **kw):
    """The cutter for a peg's hole, from z0 to z1. Run it past the surfaces it opens."""
    return _extrude(profile(x, y, grow=fit, **kw), z0, z1)
