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
~/.venvs/3d-prints/bin/python spiderweb-light-holder/model.py
~/.venvs/3d-prints/bin/python tools/render.py spiderweb-light-holder/spiderweb-light-holder.stl spiderweb-light-holder/render.png
```
