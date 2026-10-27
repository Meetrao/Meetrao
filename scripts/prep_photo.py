#!/usr/bin/env python3
"""
Prepare the photo for clean ASCII conversion:
  1. remove the background (using fast u2netp model) so the subject is isolated
  2. bilateral-smooth away texture while keeping lines sharp
  3. stretch tones so highlights land near white and dark lines stay dark
  4. darken line work (difference-of-gaussians ridges)
  5. composite onto white and crop square around the subject

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = 0.6     # how hard drawn lines are pushed toward black


def prep_image(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {input_path}...")
    img = Image.open(input_path)
    
    alpha = None
    if img.mode == "RGBA":
        alpha = np.array(img.split()[-1])
        if np.all(alpha == 255):
            alpha = None

    if alpha is None:
        try:
            print("Removing background with rembg (u2netp)...")
            from rembg import new_session, remove
            session = new_session("u2netp")
            cut = remove(img.convert("RGBA"), session=session)
            rgb = np.array(cut.convert("RGB"))
            alpha = np.array(cut.split()[-1])
        except Exception as e:
            print(f"Notice: Background removal fallback ({e}). Proceeding without rembg.")
            img_rgba = img.convert("RGBA")
            rgb = np.array(img_rgba.convert("RGB"))
            alpha = np.full((rgb.shape[0], rgb.shape[1]), 255, dtype=np.uint8)
    else:
        rgb = np.array(img.convert("RGB"))

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # 2. smooth texture, keep edges
    print("Smoothing textures while preserving edges...")
    smooth = gray
    for _ in range(3):
        smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

    # 3. tone stretch over the subject only
    if np.any(alpha > 128):
        lo, hi = np.percentile(smooth[alpha > 128], [2, 92])
        if hi <= lo:
            hi = lo + 1.0
        tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0, 1)
    else:
        tone = smooth.astype(np.float32) / 255.0

    # 4. dark-on-light ridges -> darken
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
    lines = np.clip((coarse - fine) / 40.0, 0, 1)
    out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

    # 5. paste onto white (feathered a hair to avoid a halo), square crop
    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
    out = out * mask + 255.0 * (1.0 - mask)

    ys, xs = np.where(alpha > 20)
    if len(xs) > 0 and len(ys) > 0:
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
        cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        canvas = np.full((side, side), 255, np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        dx0, dy0 = max(0, -x0), max(0, -y0)
        dx1, dy1 = dx0 + (sx1 - sx0), dy0 + (sy1 - sy0)
        canvas[dy0:dy1, dx0:dx1] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
    else:
        canvas = out.astype(np.uint8)

    Image.fromarray(canvas, mode="L").save(output_path)
    print("Wrote prepped image to", output_path, canvas.shape)


if __name__ == "__main__":
    prep_image(INP, OUT)
