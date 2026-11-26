#!/usr/bin/env python3
"""
Prepare a portrait photo for clean, light-on-dark ASCII conversion.

Output is a grayscale "lit" image meant to be printed in light ink on a dark
terminal card: background is pure black (-> blank), bright areas (skin, white
shirt, highlights) are bright (-> dense glyphs), and dark areas (hair, suit)
sit on a small floor so the silhouette still shows as faint dots.

Steps:
  1. find the subject mask
       - PNG alpha channel if present
       - else a plain light background flood-filled in from the top/sides
       - else rembg person segmentation (pip install "rembg[cpu]")
  2. bilateral-smooth skin texture while keeping edges (glasses, beard, hair)
  3. CLAHE local contrast + tone stretch over the subject only
  4. lift the darkest subject tones to a floor so dark clothes don't vanish
  5. composite onto black and crop a head-and-shoulders square

    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

SUBJECT_FLOOR = 0.12   # min brightness inside the subject (dark suit -> faint dots)
EDGE_BOOST = 0.25      # brightens bright-side edges so features pop
TONE_GAMMA = 1.1       # >1 keeps hair/suit dark so the face and shirt stand out
HEAD_MARGIN = 0.05     # space above the hair, as a fraction of crop size
MAX_SIDE = 1400        # downscale big camera files first (filters are tuned for this)
REMBG_MODEL = os.environ.get("REMBG_MODEL", "u2net_human_seg")


def plain_background_mask(rgb):
    """Subject mask for a photo shot on a plain light background.

    Near-white, low-saturation pixels connected to the top or side borders are
    background. The bottom border is excluded as a seed because a white shirt
    usually touches it.
    """
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    light = (hsv[..., 2] > 215) & (hsv[..., 1] < 40)
    light = cv2.morphologyEx(light.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels = cv2.connectedComponents(light, connectivity=4)
    h, w = light.shape
    seeds = set(labels[0, :]) | set(labels[: h * 2 // 3, 0]) | set(labels[: h * 2 // 3, w - 1])
    seeds.discard(0)
    bg = np.isin(labels, list(seeds))

    fg = (~bg).astype(np.uint8)
    # keep only the biggest blob (the person), fill pinholes
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = (labels == biggest).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return fg * 255


def border_is_plain(rgb):
    top = rgb[: max(4, rgb.shape[0] // 50)]
    sides = np.concatenate([rgb[:, :4], rgb[:, -4:]], axis=1)[: rgb.shape[0] // 2]
    border = np.concatenate([top.reshape(-1, 3), sides.reshape(-1, 3)])
    return border.mean() > 200 and border.std() < 30


def subject_mask(img):
    if img.mode in ("RGBA", "LA"):
        alpha = np.array(img.getchannel("A"))
        if not np.all(alpha == 255):
            return np.array(img.convert("RGB")), alpha

    rgb = np.array(img.convert("RGB"))
    if border_is_plain(rgb):
        print("Plain light background detected -> flood-fill mask")
        return rgb, plain_background_mask(rgb)

    try:
        from rembg import new_session, remove
        print(f"Removing background with rembg ({REMBG_MODEL})...")
        cut = remove(img.convert("RGBA"), session=new_session(REMBG_MODEL))
        return np.array(cut.convert("RGB")), np.array(cut.getchannel("A"))
    except Exception as e:  # rembg missing or failed
        print(f"Notice: no background removal ({e}); using the full frame.")
        return rgb, np.full(rgb.shape[:2], 255, np.uint8)


def crop_head_and_shoulders(img, alpha):
    ys, xs = np.where(alpha > 128)
    if len(xs) == 0:
        return img
    h, w = img.shape[:2]
    side = min(w, h, int((xs.max() - xs.min()) * 1.02))
    cx = (xs.min() + xs.max()) // 2
    top = max(0, ys.min() - int(side * HEAD_MARGIN))
    x0 = int(np.clip(cx - side // 2, 0, w - side))
    y0 = int(np.clip(top, 0, h - side))
    return img[y0:y0 + side, x0:x0 + side]


def prep_image(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {input_path}...")
    img = ImageOps.exif_transpose(Image.open(input_path))
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    rgb, alpha = subject_mask(img)
    # pull the edge in a few px so light background fringe doesn't leave a halo
    alpha = cv2.erode(alpha, np.ones((5, 5), np.uint8), iterations=1)
    inside = alpha > 128

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    smooth = gray
    for _ in range(2):
        smooth = cv2.bilateralFilter(smooth, 9, 30, 7)

    clahe = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8, 8))
    local = clahe.apply(smooth)

    lo, hi = np.percentile(local[inside], [4, 99]) if inside.any() else (0, 255)
    tone = np.clip((local.astype(np.float32) - lo) / max(hi - lo, 1.0), 0, 1)

    # bright-side edges (difference of gaussians) -> rim light on features
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.2).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 5).astype(np.float32)
    edges = np.clip((fine - coarse) / 30.0, 0, 1)
    tone = np.clip(tone + EDGE_BOOST * edges, 0, 1) ** TONE_GAMMA

    tone = SUBJECT_FLOOR + (1 - SUBJECT_FLOOR) * tone

    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.2)
    out = (tone * mask * 255).astype(np.uint8)   # background -> black

    out = crop_head_and_shoulders(out, alpha)
    Image.fromarray(out, mode="L").save(output_path)
    print("Wrote prepped image to", output_path, out.shape)


if __name__ == "__main__":
    prep_image(INP, OUT)
