"""Build Spoolman label designs for a Brother PT-P710BT and render previews.

Geometry is laid out in printer dots (180 dpi) and converted to mm so the QR
modules land on whole dots: 24 mm tape prints 128 dots, 12 mm tape 76 dots.

Usage: python labels.py [outdir]  -> designs.json, preview-24mm.png, preview-12mm.png
"""
import json
import sys

import segno
from PIL import Image, ImageDraw, ImageFont

DPI = 180
MM = 25.4 / DPI  # mm per dot
# HA tag URL: the iPhone camera hands it to the HA app, which fires tag_scanned
# and the k1_set_active_spool automation makes the spool active.
TAG_URL = "https://www.home-assistant.io/tag/spool{id}"
FONT = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"


def d(dots):
    return round(dots * MM, 4)


def layout():
    return {
        "mode": "image", "exportFormat": "png", "dpi": DPI, "paper": "A4",
        "custom": {"w": 50, "h": 25}, "landscape": False,
        "margin": {"t": 10, "b": 10, "l": 10, "r": 10},
        "safe": {"t": 0, "b": 0, "l": 0, "r": 0},
        "columns": 3, "spacing": {"h": 2, "v": 2}, "skip": 0, "copies": 1,
        "border": "none",
    }


def text(id_, x, y, w, fs, bold, wrap, template):
    return {"id": id_, "type": "text", "x": x, "y": y, "w": w, "fontSize": fs,
            "bold": bold, "align": "left", "color": "#000000", "wrap": wrap,
            "template": template}


# 24 mm tape: 128 x 360 dots (18.06 x 50.8 mm). QR v4-Q = 33 modules x 3 dots.
P = "7d0c3f52-24aa-4c1e-9b1a-2f8e6a1c0024"
spool24 = {
    "id": P, "name": "P-touch 24mm spool", "kind": "spool",
    "label": {"w": d(360), "h": d(128)},
    "layout": layout(),
    "elements": [
        {"id": f"{P}-qr", "type": "qr", "x": d(14), "y": d(14), "size": d(99),
         "ec": "Q", "encoding": "custom", "urlTemplate": TAG_URL, "logo": True},
        text(f"{P}-vendor", d(124), 1.5, round(d(360) - d(124) - 1.0, 4), 2.5, False, False,
             "{{vendor.name}}"),
        text(f"{P}-name", d(124), 4.4, round(d(360) - d(124) - 1.0, 4), 3.4, True, True,
             "{filament.name}"),
        text(f"{P}-meta", d(124), 13.3, round(d(360) - d(124) - 1.0, 4), 2.6, False, False,
             "{{filament.material} · }{{filament.nozzleTemp}°C · }#{spool.id}"),
    ],
}

# 12 mm tape: 76 x 288 dots (10.72 x 40.64 mm). QR v3-M = 29 modules x 2 dots.
S = "7d0c3f52-24aa-4c1e-9b1a-2f8e6a1c0012"
spool12 = {
    "id": S, "name": "P-touch 12mm spool", "kind": "spool",
    "label": {"w": d(288), "h": d(76)},
    "layout": layout(),
    "elements": [
        {"id": f"{S}-qr", "type": "qr", "x": d(9), "y": d(9), "size": d(58),
         "ec": "M", "encoding": "custom", "urlTemplate": TAG_URL, "logo": False},
        text(f"{S}-name", d(72), 0.5, round(d(288) - d(72) - 0.8, 4), 2.9, True, True,
             "{filament.name}"),
        text(f"{S}-meta", d(72), 7.6, round(d(288) - d(72) - 0.8, 4), 2.4, False, False,
             "{{filament.material} · }#{spool.id}"),
    ],
}

DESIGNS = [spool24, spool12]

SAMPLE = {
    "vendor.name": "Creality", "filament.name": "Hyper PLA Matte Charcoal Black",
    "filament.material": "PLA", "filament.nozzleTemp": "220", "spool.id": "12",
}


def resolve(t):
    import re
    t = re.sub(r"\{([^{}]*)\{([\w.]+)\}([^{}]*)\}",
               lambda m: m[1] + SAMPLE[m[2]] + m[3] if m[2] in SAMPLE else "", t)
    return re.sub(r"\{([\w.]+)\}", lambda m: SAMPLE.get(m[1], "?"), t)


def wrap_lines(draw, s, font, width):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def render(design, path):
    px = 1 / MM
    W, H = round(design["label"]["w"] * px), round(design["label"]["h"] * px)
    img = Image.new("L", (W, H), 255)
    dr = ImageDraw.Draw(img)
    for el in design["elements"]:
        if el["type"] == "qr":
            url = el["urlTemplate"].replace("{id}", SAMPLE["spool.id"])
            q = segno.make_qr(url, error=el["ec"].lower(), boost_error=False)
            mod = round(el["size"] * px) // q.symbol_size(border=0)[0]
            x0, y0 = round(el["x"] * px), round(el["y"] * px)
            for r, row in enumerate(q.matrix):
                for c, v in enumerate(row):
                    if v:
                        dr.rectangle([x0 + c * mod, y0 + r * mod,
                                      x0 + (c + 1) * mod - 1, y0 + (r + 1) * mod - 1], fill=0)
            if el["logo"]:
                size = el["size"] * px
                pad = size * 0.285
                o = (size - pad) / 2
                dr.rectangle([x0 + o, y0 + o, x0 + o + pad, y0 + o + pad], fill=255)
                lg = size * 0.25
                o = (size - lg) / 2
                dr.ellipse([x0 + o, y0 + o, x0 + o + lg, y0 + o + lg], fill=0)
        else:
            font = ImageFont.truetype(FONT_BOLD if el["bold"] else FONT,
                                      round(el["fontSize"] * px))
            s = resolve(el["template"])
            width = el["w"] * px
            lines = wrap_lines(dr, s, font, width) if el["wrap"] else [s]
            y = el["y"] * px
            for line in lines:
                dr.text((el["x"] * px, y), line, font=font, fill=0)
                y += el["fontSize"] * 1.15 * px
            if not el["wrap"]:
                # Clip horizontal overflow like Spoolman's no-wrap mode.
                x1 = round((el["x"] + el["w"]) * px)
                dr.rectangle([x1, round(el["y"] * px), W, round(y)], fill=255)
    # Threshold like the thermal head, then show on the tape with its margins.
    img = img.point(lambda v: 0 if v < 128 else 255)
    margin = {128: 3.0, 76: 2.0}[H] / MM
    tape = Image.new("L", (W + 40, round(H + 2 * margin)), 235)
    tape.paste(img, (20, round(margin)))
    tape = tape.resize((tape.width * 4, tape.height * 4), Image.NEAREST)
    tape.save(path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for dsg in DESIGNS:
        mm = dsg["name"].split()[1]
        render(dsg, f"{out}/preview-{mm}.png")
    with open(f"{out}/designs.json", "w") as f:
        json.dump(DESIGNS, f, ensure_ascii=False, indent=1)
