#!/usr/bin/env python3
"""social_reel.py — 9:16 poppy reel frames + a silent-mp4 assembler.

Same brand as social_brand.py (cream, ink, candy accents, Bricolage/Space Mono),
sized 1080x1920 with the safe zone the /brand/ page specifies (top ~14% and bottom
~20% are covered by the IG UI). render_mp4() sequences frames with holds and quick
cross-fades. Reels export SILENT, add trending audio inside Instagram.
"""
from pathlib import Path
import numpy as np, imageio.v2 as imageio
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from social_brand import (F, wrap, logo_mark, CREAM, INK, PINK, DARK, MUT,
                          YELLOW, VIOLET, MINT, PAPER, HEAD, BODY, MONO)

W9, H9 = 1080, 1920
MX = 96                 # side margin
SAFE_TOP, SAFE_BOT = 300, 1560   # keep text between these

def base9(bar=PINK):
    im = Image.new("RGB", (W9, H9), CREAM); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W9, 16], fill=bar)
    return im, d

def footer9(d):
    y = 1600
    logo_mark(d, MX+14, y+15, 14, INK)
    d.text((MX+44, y), "@indiemusicindia.co", font=F(MONO, 30), fill=INK)

def chip9(d, x, y, text, fill=YELLOW, fg=INK):
    f = F(MONO, 30); tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x+tw+52, y+62], radius=999, fill=fill, outline=INK, width=4)
    d.text((x+26, y+14), text, font=f, fill=fg)
    return y+62

def block_height(d, parts):
    """Measure a stack of (kind, text, size) parts for vertical centering."""
    h = 0
    for kind, text, size in parts:
        if kind == "chip": h += 62 + 30
        elif kind == "gap": h += size
        else:
            f = F(HEAD if kind == "head" else BODY, size)
            lines = wrap(d, text, f, W9-2*MX)
            h += len(lines) * int(size*1.14)
    return h

def render_mp4(frames, path, fps=30, hold=2.6, fade=0.35, holds=None):
    """frames: list of PIL images. Sequences each for `hold`s with `fade`s crossfades."""
    arrs = [np.asarray(f.convert("RGB")) for f in frames]
    hd = holds or [hold]*len(arrs)
    seq = []
    for i, a in enumerate(arrs):
        seq += [a] * int(hd[i]*fps)
        if i < len(arrs)-1:
            nf = int(fade*fps)
            for k in range(1, nf+1):
                t = k/(nf+1)
                seq.append((a*(1-t) + arrs[i+1]*t).astype(np.uint8))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    w = imageio.get_writer(path, fps=fps, codec="libx264", quality=8,
                           pixelformat="yuv420p", macro_block_size=None)
    for fr in seq: w.append_data(fr)
    w.close()
    return path
