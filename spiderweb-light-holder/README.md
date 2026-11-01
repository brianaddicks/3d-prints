# Spiderweb light holder

Holds a large spiderweb light gathered into a single strand. The ring goes on the
hook and the plug's blades go in the slots, with the strand running along the bar.

![Render](render.png)

- About 297 mm long, the most the K1 bed allows, so the STL is already turned onto the bed diagonal.
- The hook opens away from the plug, so tension in the strand seats the ring.
- The slots suit a US two-blade plug, with room for the wider polarized blade either way round.
  The plug's pull goes against the blade faces, so it won't pull the blades out of the slots.

## Printing

Import the STL into OrcaSlicer and leave it where it lands, without rotating or auto-arranging it.

| Setting | Value |
| --- | --- |
| Printer | Creality K1 (0.4 nozzle) |
| Process | 0.20mm Standard |
| Filament | PLA, about 20 g |
| Supports | None |
| Time | About 31 minutes |

Change the dimensions at the top of `model.py`, then rerun it. `SLOT_THICKNESS` sets the plug's grip.
