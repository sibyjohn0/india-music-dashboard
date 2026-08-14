#!/usr/bin/env python3
"""Print-craft treatment engine for IMI hero art.
Turns a flat digital image into something that feels physically MADE:
halftone dot-screen, duotone, grain, paper, poster type (incl. Indian scripts).
Reusable module — imported by the compose scripts."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

SYS = "/System/Library/Fonts/Supplemental/"
REPO_FONTS = os.path.expanduser("~/music-india-dashboard/assets/fonts")

def load(p): return Image.open(p).convert("RGB")

def cover(im, w, h):
    s = max(w/im.width, h/im.height)
    im = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
    x = (im.width-w)//2; y = (im.height-h)//2
    return im.crop((x, y, x+w, y+h))

def duotone(im, dark, light, contrast=1.15):
    g = np.asarray(ImageOps.autocontrast(im.convert("L"), cutoff=1)).astype("float32")/255.0
    g = np.clip((g-0.5)*contrast+0.5, 0, 1)
    dark = np.array(dark, "float32"); light = np.array(light, "float32")
    out = dark[None,None,:]*(1-g[...,None]) + light[None,None,:]*g[...,None]
    return Image.fromarray(out.astype("uint8"))

def grain(im, amount=14):
    a = np.asarray(im).astype("int16")
    n = np.random.randint(-amount, amount+1, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a+n, 0, 255).astype("uint8"))

def halftone(im, cell=7, ink=(16,16,32), paper=(234,230,220), gain=1.3):
    """Classic dot-screen: dot radius grows with darkness. The signature print texture."""
    g = np.asarray(ImageOps.autocontrast(im.convert("L"), cutoff=1)).astype("float32")/255.0
    h, w = g.shape
    big = 3  # supersample for smooth dots
    canvas = Image.new("RGB", (w*big, h*big), paper); d = ImageDraw.Draw(canvas)
    for cy in range(0, h, cell):
        for cx in range(0, w, cell):
            block = g[cy:cy+cell, cx:cx+cell]
            dark = 1.0 - float(block.mean())
            r = (cell*0.75) * math.sqrt(min(1.0, dark*gain))
            if r > 0.35:
                ccx, ccy = (cx+cell/2)*big, (cy+cell/2)*big
                rr = r*big
                d.ellipse([ccx-rr, ccy-rr, ccx+rr, ccy+rr], fill=ink)
    return canvas.resize((w, h), Image.LANCZOS)

def paper(w, h, base=(234,230,220), fleck=7):
    a = np.ones((h, w, 3), "float32")*np.array(base, "float32")
    a += np.random.randint(-fleck, fleck+1, (h, w, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))

def riso_offset(im, dx=4, dy=3):
    """Fake screen-print misregistration: nudge the red channel."""
    a = np.asarray(im).astype("uint8")
    r = np.roll(a[..., 0], (dy, dx), (0, 1))
    a = a.copy(); a[..., 0] = r
    return Image.fromarray(a)

def vignette(im, strength=0.55):
    w, h = im.size
    yy, xx = np.mgrid[0:h, 0:w].astype("float32")
    cx, cy = w/2, h/2
    d = np.sqrt(((xx-cx)/(w/2))**2 + ((yy-cy)/(h/2))**2)
    m = np.clip(1 - (d-0.6)*strength, 0, 1)[..., None]
    return Image.fromarray((np.asarray(im).astype("float32")*m).clip(0,255).astype("uint8"))

def scrim(im, frm=0.5, alpha=210, top=False):
    """Dark gradient from bottom (or top) for text legibility."""
    w, h = im.size
    a = np.zeros((h, w, 4), "uint8")
    for row in range(h):
        t = (row/h)
        if top: v = max(0, (frm - t)/frm)
        else:   v = max(0, (t - (1-frm))/frm)
        a[row, :, 3] = int(v*alpha)
    base = im.convert("RGBA"); base.alpha_composite(Image.fromarray(a))
    return base.convert("RGB")

# --- fonts ---
def bric(sz, w=850):
    f = ImageFont.truetype(f"{REPO_FONTS}/BricolageGrotesque.ttf", sz)
    try: f.set_variation_by_axes([96, w, 100])
    except Exception: pass
    return f
def mono(sz): return ImageFont.truetype(f"{REPO_FONTS}/SpaceMono-Bold.ttf", sz)
def didot(sz): return ImageFont.truetype(SYS+"Didot.ttc", sz)
def deva(sz):  return ImageFont.truetype(SYS+"Kohinoor.ttc", sz)          # Devanagari
def tamil(sz): return ImageFont.truetype(SYS+"Tamil Sangam MN.ttc", sz)
def bangla(sz):return ImageFont.truetype(SYS+"KohinoorBangla.ttc", sz)
def gurmukhi(sz):return ImageFont.truetype(SYS+"Gurmukhi Sangam MN.ttc", sz)

def tw(d,t,f): return d.textlength(t,font=f)
def trk(d,pos,txt,f,fill,t):
    x,y=pos
    for ch in txt: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+t
