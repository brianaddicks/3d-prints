#!/usr/bin/env python3
"""Put a SET_GCODE_OFFSET before each Z-ladder square in a sliced G-code file.

OrcaSlicer labels each square with EXCLUDE_OBJECT_START NAME=z-ladder-<n>...; this adds the
offset for square n just before it, and resets the offset to 0 at the end of the print.

usage: set_z_offsets.py in.gcode out.gcode
"""
import re
import sys

from z_offset_ladder import OFFSETS


def main(src, dst):
    out, seen = [], set()
    for line in open(src):
        m = re.match(r"EXCLUDE_OBJECT_START NAME=z-ladder-(\d+)", line)
        if m:
            n = int(m.group(1))
            out.append(f"SET_GCODE_OFFSET Z={OFFSETS[n - 1]:.3f} MOVE=1 ; z ladder square {n}\n")
            seen.add(n)
        if line.startswith("; EXECUTABLE_BLOCK_END"):
            out.append("SET_GCODE_OFFSET Z=0 ; z ladder done\n")
        out.append(line)
    assert seen == set(range(1, len(OFFSETS) + 1)), f"found squares {sorted(seen)}"
    open(dst, "w").writelines(out)
    print(f"offsets placed for squares {sorted(seen)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
