#!/usr/bin/env python3
"""
prep_photo.py
-------------
Prepares a portrait photo for ASCII rendering:

  1. Loads the input photo (default: hero.png).
  2. Removes the background with rembg (U2Net).
  3. Applies adaptive contrast enhancement (CLAHE) on the luminance channel.
  4. Centres the subject on a transparent / matte canvas.
  5. Saves the result as `source-prepped.png`.

Dependencies: rembg[cpu], pillow, numpy, opencv-python-headless
(see scripts/requirements.txt).

The script is intentionally defensive: if rembg or cv2 are not installed
it degrades gracefully and still produces a usable `source-prepped.png`.
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a portrait photo for ASCII art.")
    parser.add_argument("input", nargs="?", default="hero.png", help="Input portrait photo (default: hero.png)")
    parser.add_argument("-o", "--output", default="source-prepped.png", help="Output file (default: source-prepped.png)")
    parser.add_argument("--size", type=int, default=640, help="Longest edge of the output in px (default: 640)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[prep] ERROR: input file not found: {args.input}", file=sys.stderr)
        return 1

    from PIL import Image, ImageEnhance, ImageOps

    print(f"[prep] loading {args.input} ...")
    img = Image.open(args.input).convert("RGBA")

    # ------------------------------------------------------------------ #
    # 1. Background removal (rembg / U2Net)                              #
    # ------------------------------------------------------------------ #
    try:
        import numpy as np
        from rembg import remove, new_session

        print("[prep] removing background with rembg (u2net) ...")
        session = new_session("u2net")
        out = remove(img, session=session, force_return_bytes=False)
        if isinstance(out, bytes):
            import io

            out = Image.open(io.BytesIO(out)).convert("RGBA")
        img = out
        bg_removed = True
    except Exception as exc:  # noqa: BLE001 - rembg is heavy; degrade gracefully
        print(f"[prep] WARNING: rembg unavailable or failed ({type(exc).__name__}: {exc})")
        bg_removed = False

    # ------------------------------------------------------------------ #
    # 2. Contrast enhancement (CLAHE on luminance)                       #
    # ------------------------------------------------------------------ #
    try:
        import numpy as np
        import cv2

        arr = np.array(img.convert("RGBA"))
        alpha = arr[..., 3]
        rgb = arr[..., :3]
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l_ch, a_ch, b_ch = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_ch = clahe.apply(l_ch)
        lab = cv2.merge((l_ch, a_ch, b_ch))
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        if bg_removed:
            rgb = np.dstack([rgb, alpha])
        img = Image.fromarray(rgb, "RGBA" if bg_removed else "RGB").convert("RGBA")
        print("[prep] applied CLAHE contrast enhancement.")
    except Exception as exc:  # noqa: BLE001
        print(f"[prep] WARNING: opencv unavailable or failed ({type(exc).__name__}: {exc})")

        # Pillow fallback: gentle contrast + colour boost.
        img = img.convert("RGBA")
        base = img.split()[3]
        img = ImageEnhance.Contrast(img.convert("RGB")).enhance(1.25)
        img = ImageEnhance.Color(img).enhance(1.12)
        img.putalpha(base)

    # ------------------------------------------------------------------ #
    # 3. Crop out transparent margins, then centre on a matte canvas     #
    # ------------------------------------------------------------------ #
    if bg_removed:
        bbox = img.split()[3].getbbox()
        if bbox:
            img = img.crop(bbox)

    # ------------------------------------------------------------------ #
    # 4. Resize to a sane working size                                   #
    # ------------------------------------------------------------------ #
    w, h = img.size
    scale = args.size / max(w, h)
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

    print(f"[prep] writing {args.output} ({img.size[0]}x{img.size[1]}) ...")
    img.save(args.output, "PNG")
    print("[prep] done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())