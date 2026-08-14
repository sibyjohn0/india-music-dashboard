#!/usr/bin/env python3
"""Generate a 50-image explore batch via Pollinations (Flux, free) to find the
visual pattern for IMI hero content. No baked-in text. Curate-heavy: keep the
strongest, bin the rest. Saves to social/ai_explore/NN_label.png."""
import os, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(os.path.expanduser("~/music-india-dashboard/social/ai_explore"))
OUT.mkdir(parents=True, exist_ok=True)

STYLE = "heavy 35mm film grain, cinematic, editorial, muted rich colour, dreamlike, no text, no watermark, no words"

# (label, scene) — leaning Indian-indie-music surreal, across registers
SCENES = [
    ("water",      "a young Indian musician waist deep in dark still monsoon water at night, distant city neon reflections, muted teal"),
    ("rooftop",    "silhouette of a person wearing headphones on a Mumbai rooftop at dusk, sodium streetlight haze, moody"),
    ("wetstreet",  "a lone figure walking a wet Indian street at night, blurred neon shop signs, heavy rain, teal and amber"),
    ("bedroom",    "a bedroom music studio at night lit only by a laptop glow and fairy lights, tangled cables and tapes, teenager silhouette, intimate"),
    ("doghead",    "surreal, a young person with a stray Indian street-dog head wearing large headphones, sitting on a compound wall, bright blue sky, deadpan"),
    ("cassette",   "a giant cassette tape floating above a dusty Indian field at golden hour, surreal dreamlike"),
    ("wireman",    "a figure made of tangled headphone wires standing in an empty temple courtyard, surreal, soft light"),
    ("radio",      "a boy holding a glowing vintage transistor radio like a lantern in a dark alley, surreal, cinematic"),
    ("handtape",   "extreme macro of a hand holding a worn cassette tape, dust and fingerprints, warm low light, hyper detailed"),
    ("roots",      "macro of tangled earphones knotted like roots growing from cracked dry earth, surreal, moody"),
    ("vinylmud",   "a vinyl record half buried in monsoon mud, rain droplets, macro, cinematic"),
    ("earstage",   "extreme close up of an ear with a tiny lit stage and spotlight glowing inside it, surreal, dark, hyper detailed"),
    ("gelportrait","editorial portrait of a young Indian indie musician lit by a single harsh coloured gel light, dark background, confident"),
    ("venuehaze",  "a hazy small live-music venue, silhouettes of a crowd, coloured stage smoke, intimate, cinematic"),
    ("drummer",    "a drummer mid-motion with long-exposure light trails, dark stage, cinematic"),
    ("floatsleep", "surreal, a person floating asleep above a rooftop wrapped in headphone cables, night city glowing below"),
    ("chaigalaxy", "a cutting-chai glass with a tiny galaxy swirling inside it, on a roadside tapri table at night, surreal"),
    ("doubleexp",  "double exposure of a singer's face and a crowded small venue, moody teal, grainy"),
]

def fetch(prompt, seed, path, tries=2):
    q = urllib.parse.quote(f"{prompt}, {STYLE}")
    url = f"https://image.pollinations.ai/prompt/{q}?width=1024&height=1280&nologo=true&model=flux&seed={seed}"
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=150).read()
            if len(data) > 5000:
                open(path, "wb").write(data); return True
        except Exception as e:
            print("  retry", path.name, e); time.sleep(3)
    return False

def main():
    n = 50; made = 0
    for i in range(n):
        label, scene = SCENES[i % len(SCENES)]
        seed = 100 + i
        path = OUT / f"{i:02d}_{label}.png"
        if path.exists(): made += 1; continue
        ok = fetch(scene, seed, path)
        made += ok
        print(f"[{i+1}/{n}] {'ok ' if ok else 'FAIL'} {path.name}")
    print(f"DONE explore: {made}/{n} -> {OUT}")

if __name__ == "__main__":
    main()
