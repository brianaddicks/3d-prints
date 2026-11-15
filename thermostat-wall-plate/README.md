# Thermostat wall plate with sun hood

A plate for the downstairs ecobee Smart Thermostat Premium. A hollow plug fills the notch
the previous owners cut in the paneling (121 x 80 mm, 18 mm deep). A 160 x 120 mm face laps onto the paneling and frames the 104 mm ecobee. An
L-shaped hood along the top and left edges keeps direct sun off the thermostat. It sticks
out 45 mm at the top, about 19 mm past the front of the ecobee, and the left side tapers
to 22 mm at the bottom.

![Render](render.png)

## Parts

- `plate.stl` prints face down on the bed. It has the plug, four countersunk wall-screw holes
  hidden under the ecobee, a 36 x 20 mm wire slot, and five through-holes for the hood's
  pegs. There's no recess for the hood: one at the edge would float over the bed when the
  face prints down.
- `hood.stl` prints lying on the outside of its top wing, with the left wing standing up.
  Five 2.6 mm pegs stick out of the edge that meets the plate. They're teardrop-shaped so
  they print sideways without supports, and they stop 0.5 mm short of the back of the plate.

## Install

1. Attach the hood first. Line its pegs up with the holes along the plate's top and left
   edges and press it down until it sits flat. If it's too tight, tap it home with a
   mallet or sand the pegs lightly; if it's loose, add a drop of CA glue in each hole.
2. Feed the cable through the plug and the wire slot. Plug the hole in the wall around the
   cable with putty or foam so draughts from the wall cavity don't reach the sensor.
3. Press the plug into the notch and screw the plate to the notch floor with four #6 or #8
   flat-head wood screws, about 1-1/4" long.
4. Hold the ecobee back plate over the wire slot and mark its holes. Drill 2.5 mm pilots
   (the face is 5 mm thick) and screw it on with the ecobee's screws. If one of its holes
   lands on a wall screw, turn the back plate slightly.

## Printing

| Setting | Value |
| --- | --- |
| Printer | Creality K1 (0.4 nozzle) |
| Process | 0.20mm Standard, 4 walls, 15% infill |
| Plate | About 80 g of PETG and 2.5 hours, 250 °C nozzle and 70 °C bed |
| Hood | About 39 g of PETG and 2.6 hours |
| Filament | **PETG or ASA, not PLA.** The plate sits in direct sun on a black wall, and PLA softens at about 55 °C. |
| Supports | None |
| Brim | None |

The sizes are at the top of `model.py`. Change them and rerun it. `NOTCH_W`, `NOTCH_H` and
`FIT` set how the plug fits the notch, and `HOOD_TOP_DEPTH` sets how far the hood sticks out.
`PEG_FIT` is the clearance on each side of each peg (0.1 mm). Lower it for a tighter press fit
and raise it if the pegs won't go in.
