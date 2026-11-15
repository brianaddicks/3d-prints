#!/usr/bin/env python3
"""Fit test for the hood pegs, before the 5 hour plate and hood print.

fit-test.stl holds:
  a 5 mm strip of plate, face down like plate.stl, with three peg holes. The notches on its
    back edge count the clearance: 1 notch = 0.05 mm, 2 = 0.10 mm, 3 = 0.15 mm per side.
  three short pieces of hood wall, each with one peg, lying on their outer face like hood.stl.

Push a peg into each hole and set PEG_FIT in model.py to the clearance that holds firmly
but still goes in by hand.
"""
import trimesh
from shapely.geometry import box

import model as m

FITS = (0.05, 0.10, 0.15)
HOLE_X = (10.0, 25.0, 40.0)
STRIP_W, STRIP_H = 50.0, 14.0
TAB_W, TAB_DEPTH = 12.0, 8.0


def strip():
    body = m.extrude(box(0, m.Y1 - STRIP_H, STRIP_W, m.Y1), 0, m.FACE_T)
    cuts = []
    for x, fit in zip(HOLE_X, FITS):
        cuts.append(m.extrude(m.peg_profile(x, m.Y1 - m.PEG_INSET, fit), -1, m.FACE_T + 1))
        count = int(round(fit / 0.05))
        for i in range(count):
            nx = x + (i - (count - 1) / 2) * 2.5
            cuts.append(m.extrude(box(nx - 0.6, m.Y1 - STRIP_H - 1, nx + 0.6, m.Y1 - STRIP_H + 1.5), -1, m.FACE_T + 1))
    return m.lay_plate(m.diff(body, cuts))


def tab():
    wall = m.extrude(box(-TAB_W / 2, m.Y1 - m.HOOD_T, TAB_W / 2, m.Y1), m.FACE_T, m.FACE_T + TAB_DEPTH)
    peg = m.extrude(m.peg_profile(0, m.Y1 - m.PEG_INSET), m.FACE_T - m.PEG_LEN, m.FACE_T + 0.5)
    return m.lay_hood(m.union([wall, peg]))


def tab_peg_up():
    """One tab standing on its free edge with the peg pointing up, so the peg prints as a
    vertical post with no overhang at all. Written to fit-test-peg-up.stl."""
    wall = m.extrude(box(-TAB_W / 2, m.Y1 - m.HOOD_T, TAB_W / 2, m.Y1), m.FACE_T, m.FACE_T + TAB_DEPTH)
    peg = m.extrude(m.peg_profile(0, m.Y1 - m.PEG_INSET), m.FACE_T - m.PEG_LEN, m.FACE_T + 0.5)
    t = m.union([wall, peg])
    t.apply_transform(trimesh.transformations.rotation_matrix(3.14159265, (1, 0, 0)))
    return m.to_bed(t)


def main():
    up = tab_peg_up()
    m.check("peg-up", up)
    up.export(m.HERE / "fit-test-peg-up.stl")
    pieces = [strip()]
    pieces[0].apply_translation((-pieces[0].bounds[0][0] + 0, -pieces[0].bounds[0][1], 0))
    for i in range(3):
        t = tab()
        t.apply_translation((-t.bounds[0][0] + i * (TAB_W + 6), -t.bounds[0][1] + STRIP_H + 8, 0))
        pieces.append(t)
    out = m.to_bed(trimesh.util.concatenate(pieces))
    m.check("fittest", out)
    out.export(m.HERE / "fit-test.stl")


if __name__ == "__main__":
    main()
