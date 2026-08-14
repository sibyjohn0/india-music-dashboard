#!/usr/bin/env python3
"""Batch-convert every carousel folder and every single tile into a motion Reel.
Carousels -> <folder>/reel.mp4 (multi-slide, cross-dissolve).
Single tiles -> social/reels_from_tiles/<name>_reel.mp4 (~4.5s Ken Burns).
Run from the repo root. Local only."""
import glob, os
import render_reel as RR
from PIL import Image

def render_folder(d, out):
    files = sorted(glob.glob(os.path.join(d, "slide_*.png")))
    if not files: return False
    imgs = [Image.open(f).convert("RGB").resize((RR.W, RR.H)) for f in files]
    hold_n = int(RR.HOLD * RR.FPS); xf = int(RR.XFADE * RR.FPS)
    w = RR.imageio.get_writer(out, fps=RR.FPS, codec="libx264", quality=8,
                              macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
    prev = None
    for img in imgs:
        hold = [RR.kb_frame(img, k / max(hold_n - 1, 1)) for k in range(hold_n)]
        if prev is not None:
            head = hold[0]
            for k in range(xf):
                a = (k + 1) / xf
                w.append_data((prev * (1 - a) + head * a).astype("uint8"))
        for fr in hold: w.append_data(fr)
        prev = hold[-1].astype("float64")
    w.close(); return True

def render_image(f, out):
    img = Image.open(f).convert("RGB").resize((RR.W, RR.H))
    n = int(4.5 * RR.FPS)
    w = RR.imageio.get_writer(out, fps=RR.FPS, codec="libx264", quality=8,
                              macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p"])
    for k in range(n): w.append_data(RR.kb_frame(img, k / max(n - 1, 1)))
    w.close()

def main():
    car = 0; tile = 0
    dirs = [d for d in glob.glob("social/carousels/*") if os.path.isdir(d)]
    dirs += [d for d in glob.glob("social/carousels/batch2/*") if os.path.isdir(d)]
    for d in dirs:
        if render_folder(d, os.path.join(d, "reel.mp4")):
            car += 1; print("carousel:", d)
    outdir = "social/reels_from_tiles"; os.makedirs(outdir, exist_ok=True)
    for f in sorted(glob.glob("social/posts/*/*.png")):
        if "caption" in os.path.basename(f).lower(): continue
        base = os.path.relpath(f, "social/posts").replace("/", "__")[:-4]
        render_image(f, os.path.join(outdir, base + "_reel.mp4")); tile += 1
    print(f"DONE: {car} carousel reels + {tile} tile reels = {car+tile}")

if __name__ == "__main__":
    main()
