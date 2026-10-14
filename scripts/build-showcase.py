#!/usr/bin/env python3
"""Build web-optimized showcase images for README / marketplace rendering.

Outputs into <repo>/showcase/:
  01..04-*.jpg      gallery images (width 720, JPEG q82)
  hero.jpg          4 tiles in a row
  social-preview.jpg  3 tiles in a row, 1280x640 (for GitHub social preview upload)
"""
import os
from PIL import Image

REPO = "/Users/yw/ai/poet/muse-illustration"
SRC = os.path.join(REPO, "skills/muse-illustration/assets/cases/images")
OUT = os.path.join(REPO, "showcase")
os.makedirs(OUT, exist_ok=True)

PAPER = (250, 247, 240)

CASES = [
    ("01-jiangnanchun-muke.jpg", "2026-10-14-jiangnanchun.png"),
    ("02-yijiangnan-muke.jpg", "2026-10-14-yijiangnan.png"),
    ("03-jiangnanchun-riso.jpg", "2026-10-14-jiangnanchun-riso.png"),
    ("04-jiangnanchun-chunkcolor.jpg", "2026-10-14-jiangnanchun-chunkcolor.png"),
]

def save_jpg(im, path, quality=82):
    im.convert("RGB").save(path, "JPEG", quality=quality,
                           optimize=True, progressive=True)

# 1) gallery copies at width 720
gallery = []
for outname, srcname in CASES:
    im = Image.open(os.path.join(SRC, srcname)).convert("RGB")
    w, h = im.size
    tw = 720
    im2 = im.resize((tw, round(h * tw / w)), Image.LANCZOS)
    p = os.path.join(OUT, outname)
    save_jpg(im2, p)
    gallery.append(im2)
    print(f"{outname:38s} {im2.size}  {os.path.getsize(p)/1024:.0f} KB")

def compose(images, tile_w, tile_h, gap, pad, canvas_w, canvas_h, outpath):
    canvas = Image.new("RGB", (canvas_w, canvas_h), PAPER)
    row_w = len(images) * tile_w + (len(images) - 1) * gap
    x = (canvas_w - row_w) // 2
    y = (canvas_h - tile_h) // 2
    for im in images:
        t = im.resize((tile_w, tile_h), Image.LANCZOS)
        canvas.paste(t, (x, y))
        x += tile_w + gap
    save_jpg(canvas, outpath, quality=88)
    print(f"{os.path.basename(outpath):38s} {canvas.size}  {os.path.getsize(outpath)/1024:.0f} KB")

# 2) hero: all four in a row
compose(gallery, 400, 600, 20, 20, 1720, 640, os.path.join(OUT, "hero.jpg"))

# 3) social preview: first three in a row, exactly 1280x640
compose(gallery[:3], 400, 600, 16, 20, 1280, 640,
        os.path.join(OUT, "social-preview.jpg"))

print("\ntotal:", sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) // 1024, "KB")
