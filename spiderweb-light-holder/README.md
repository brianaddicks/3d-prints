# Spiderweb light holder

A winder for a large spiderweb light gathered into a single strand. The strand wraps
lengthwise around the ends, and lips on both faces keep it from sliding off the sides.

![Render](render.png)

- 264 x 50.8 mm (2 inches wide), the longest that width fits on the K1 bed diagonal.
  The STL is already turned onto the diagonal.
- To start, tuck the ring's wire under the hook on the channel floor and lay the ring flat. The
  hook reaches toward the end, so pulling the strand toward the plug seats the ring. It's sized
  for a ring of about 42-45 mm in 2 mm wire, measured from a photo of the first print.
- Lips run the full length of both edges, on both faces.
- To finish, push the plug's blades into the block beside the lip. The slots suit a US two-blade plug,
  with room for the wider polarized blade either way round, and the block takes the full blade.

## Printing

Import the STL into OrcaSlicer and leave it where it lands, without rotating or auto-arranging it.

| Setting | Value |
| --- | --- |
| Printer | Creality K1 (0.4 nozzle) |
| Process | 0.20mm Standard |
| Filament | PLA, about 50 g |
| Time | About 1 hour 20 minutes |
| Brim | **None.** Auto brim runs right up to the bed edge. |
| Supports | None. The underside channel bridges 43 mm between the lips. |

Change the dimensions at the top of `model.py`, then rerun it. `SLOT_THICKNESS` sets the plug's grip.
