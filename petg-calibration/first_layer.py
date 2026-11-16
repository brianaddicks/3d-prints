#!/usr/bin/env python3
"""First-layer test: one 0.2 mm layer the size of a part, centred on the bed.

Peel it off and look at it against the light. Flat lines fused into a smooth sheet mean the
nozzle height is right there; separate rounded lines with gaps mean it's too high; ridges or
a rough, scraped surface mean it's too low. Note where each happens, since the bed mesh and
the Z offset fix different patterns.

usage: first_layer.py [width depth]   (default 160 x 120, the thermostat plate)
"""
import sys
from pathlib import Path

import trimesh
from shapely.geometry import box

HERE = Path(__file__).parent
LAYER = 0.2
BED = 220.0


def main(w=160.0, d=120.0):
    shape = box(-w / 2 + 4, -d / 2 + 4, w / 2 - 4, d / 2 - 4).buffer(4, resolution=16)
    m = trimesh.creation.extrude_polygon(shape, LAYER)
    m.apply_translation((BED / 2, BED / 2, 0))
    name = f"first-layer-{w:.0f}x{d:.0f}.stl"
    m.export(HERE / name)
    print(name, m.is_watertight)


if __name__ == "__main__":
    main(*map(float, sys.argv[1:3]))
