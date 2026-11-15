#!/usr/bin/env python3
"""Add the per-block nozzle temperature changes to a sliced temp-tower G-code.

usage: set_temps.py in.gcode out.gcode
"""
import sys

from model import BLOCK_H, TEMPS, block_start


def main(src, dst):
    starts = [(block_start(i), t) for i, t in enumerate(TEMPS)][1:]
    out, done = [], 0
    for line in open(src):
        out.append(line)
        if line.startswith(";Z:") and done < len(starts):
            z = float(line[3:])
            if z > starts[done][0] + 1e-3:
                t = starts[done][1]
                out.append(f"M104 S{t} ; temp tower: block {done + 2}, {t} C\n")
                print(f"z {z:.2f}: M104 S{t}")
                done += 1
    assert done == len(starts), f"only {done} of {len(starts)} changes placed"
    open(dst, "w").writelines(out)


if __name__ == "__main__":
    del BLOCK_H
    main(sys.argv[1], sys.argv[2])
