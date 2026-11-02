# 3D prints

Models for a Creality K1 (220 x 220 x 250 mm), sliced in OrcaSlicer.

Each print has its own folder with the STL, the script that generates it, and a render.

| Print | Picture |
| --- | --- |
| [Spiderweb light holder](spiderweb-light-holder/) | ![Render](spiderweb-light-holder/render.png) |

## Rebuilding

```
python3 -m venv ~/.venvs/3d-prints
~/.venvs/3d-prints/bin/pip install -r requirements.txt
cd spiderweb-light-holder
~/.venvs/3d-prints/bin/python model.py
~/.venvs/3d-prints/bin/python ../tools/render.py build/assembled.stl render.png \
  --parts holder-plug-end.stl holder-hook-end.stl \
  --views "Plug block,20,30,75,50,22,75;Hook,30,25,-30,0,26,70;Joint,35,-60,217,0,22,110"
```

`render.py` draws the assembled print, a bed plan for each part and any close-ups given with
`--views` as `title,elevation,azimuth,x,y,z,span` (a negative x counts back from the far end).
