#!/usr/bin/env python3
"""Slice a tall screenshot into bands and OCR each with RapidOCR."""
import os, sys
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

SRC = "/home/fx/stem/commercial-trend/ji-snapshot-01.jpg"
OUT = "/home/fx/stem/commercial-trend/bands"
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGB")
W, H = im.size
print(f"image {W}x{H}")

BAND = 1500
OVERLAP = 120
engine = RapidOCR()

n = 0
y = 0
while y < H:
    y2 = min(y + BAND, H)
    band = im.crop((0, y, W, y2))
    # upscale narrow bands slightly for better OCR
    if W < 1000:
        scale = 1000 / W
        band = band.resize((1000, int((y2 - y) * scale)), Image.LANCZOS)
    path = os.path.join(OUT, f"band_{n:02d}.png")
    band.save(path)
    result, _ = engine(path)
    print(f"\n===== BAND {n} (y={y}..{y2}) =====")
    if result:
        for box, text, conf in result:
            print(text)
    else:
        print("[no text]")
    n += 1
    y = y2 - OVERLAP
    if y >= H:
        break

print(f"\nDONE: {n} bands")
