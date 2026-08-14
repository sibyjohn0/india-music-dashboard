#!/usr/bin/env python3
"""
Turn a folder of 1080x1920 slide_*.png frames into a motion Reel (.mp4).

Motion = a gentle Ken Burns push on every slide (holds attention / watch-time)
plus a quick cross-dissolve between slides. First slide gets a short punch-in so
the opening second moves, which is what keeps a Reel being served.

Usage: python3 scripts/render_reel.py <frames_dir> [out.mp4]
Local only. No audio (add trending audio in the IG app when posting).
"""
import sys, glob, os
import numpy as np
from PIL import Image
import imageio.v2 as imageio

FPS = 24
HOLD = 1.9          # seconds each slide is on screen
XFADE = 0.35        # cross-dissolve duration
ZOOM = 0.035        # Ken Burns zoom amount over a hold
W, H = 1080, 1920

def kb_frame(img, t):
    """Ken Burns: scale from 1.0 to 1+ZOOM across t=0..1, centre-cropped to WxH."""
    s = 1.0 + ZOOM * t
    nw, nh = int(W * s), int(H * s)
    big = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - W) // 2, (nh - H) // 2
    return np.asarray(big.crop((x, y, x + W, y + H)))

def main():
    d = sys.argv[1]
    # Single-image mode: arg1 is a .png -> short ~4.5s Ken Burns reel from one tile.
    if os.path.isfile(d) and d.lower().endswith(".png"):
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(d)[0] + "_reel.mp4"
        img = Image.open(d).convert("RGB").resize((W, H))
        n = int(4.5 * FPS)
        writer = imageio.get_writer(out, fps=FPS, codec="libx264", quality=8,
                                    macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
        for k in range(n):
            writer.append_data(kb_frame(img, k / max(n - 1, 1)))
        writer.close()
        print(f"wrote {out}  (1 tile, ~4.5s)")
        return
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, "reel.mp4")
    files = sorted(glob.glob(os.path.join(d, "slide_*.png")))
    if not files:
        print("no slides in", d); return
    imgs = [Image.open(f).convert("RGB").resize((W, H)) for f in files]

    hold_n = int(HOLD * FPS)
    xfade_n = int(XFADE * FPS)
    writer = imageio.get_writer(out, fps=FPS, codec="libx264",
                                quality=8, macro_block_size=8,
                                ffmpeg_params=["-pix_fmt", "yuv420p"])

    prev_tail = None  # last frame of previous slide's hold (for crossfade)
    for idx, img in enumerate(imgs):
        # pre-render this slide's Ken Burns hold
        hold = [kb_frame(img, k / max(hold_n - 1, 1)) for k in range(hold_n)]
        # crossfade from previous slide's tail into this slide's head
        if prev_tail is not None:
            head = hold[0]
            for k in range(xfade_n):
                a = (k + 1) / xfade_n
                writer.append_data((prev_tail * (1 - a) + head * a).astype("uint8"))
        for fr in hold:
            writer.append_data(fr)
        prev_tail = hold[-1].astype("float64")
    writer.close()
    dur = (len(imgs) * hold_n + (len(imgs) - 1) * xfade_n) / FPS
    print(f"wrote {out}  ({len(imgs)} slides, ~{dur:.1f}s, {FPS}fps)")

if __name__ == "__main__":
    main()
