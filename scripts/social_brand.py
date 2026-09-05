#!/usr/bin/env python3
"""social_brand.py — shared poppy brand for all social graphics.

The website is the bright "poppy" identity (cream, ink, candy accents); social
used to be a separate dark look. This module is the single source of truth so
every generated image speaks the same visual language as indiemusicindia.com.
Import the palette + helpers here rather than redefining colours per script.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"
W, H = 1080, 1350  # IG portrait 4:5

# --- poppy palette (matches assets/poppy.css) --------------------------------
CREAM=(255,247,238); INK=(36,27,46); PINK=(255,77,141); YELLOW=(255,210,63)
MINT=(31,207,158); VIOLET=(139,92,246); PAPER=(255,255,255)
DARK=(58,49,66); MUT=(107,96,118)
YELLOW_S=(255,243,206); VIOLET_S=(237,228,255); MINT_S=(210,246,236)

HEAD="BricolageGrotesque.ttf"; BODY="Inter.ttf"; MONO="SpaceMono-Bold.ttf"

def F(name, size):
    return ImageFont.truetype(str(FONTS/name), size)

def wrap(d, text, font, maxw):
    out=[]; cur=""
    for w in text.split():
        s=(cur+" "+w).strip()
        if d.textlength(s, font=font) <= maxw: cur=s
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def base(bg=CREAM, bar=PINK):
    """Cream canvas with the site's pink top rule."""
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,14],fill=bar)
    return im,d

def logo_mark(d, cx, cy, r=13, color=INK):
    """The IIM circular mark (Space Mono has no glyph for it, so we draw it)."""
    d.ellipse([cx-r,cy-r,cx+r,cy+r], outline=color, width=4)
    d.ellipse([cx-4,cy-4,cx+4,cy+4], fill=color)

def chip(d, x, y, text, fill=YELLOW, fg=INK):
    """A pill label with an ink border, like the site's tabs/stickers."""
    f=F(MONO,26); tw=d.textlength(text, font=f)
    d.rounded_rectangle([x,y,x+tw+44,y+54], radius=999, fill=fill, outline=INK, width=3)
    d.text((x+22,y+12), text, font=f, fill=fg)
    return y+54

def shadow_card(d, box, radius=20, fill=PAPER, off=7):
    """White rounded card with the site's hard offset ink shadow."""
    x0,y0,x1,y1=box
    d.rounded_rectangle([x0+off,y0+off,x1+off,y1+off], radius=radius, fill=INK)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=INK, width=3)

def footer(d, left="@indiemusicindia.co", right="indiemusicindia.com"):
    y=H-72
    logo_mark(d, 84+13, y+14, 13, INK)
    d.text((84+40,y), left, font=F(MONO,26), fill=INK)
    if right:
        d.text((W-84,y), right, font=F(MONO,24), fill=MUT, anchor="ra")
