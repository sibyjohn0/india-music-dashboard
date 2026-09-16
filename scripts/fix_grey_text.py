#!/usr/bin/env python3
"""fix_grey_text.py — remap leftover dark-theme light-grey text colors to readable values.

The guide/tool/toolkit pages were authored dark-theme (light-grey body text on dark),
then flipped to a cream theme via poppy.css. Text colors that poppy didn't override are
now light-grey on cream (contrast ~1.6:1, illegible). This rewrites only `color:` decls,
mapping the grey family to a readable dark-grey and light accent text to deeper accents.

index.html and featured/index.html are SKIPPED (they still have real dark sections where
the light text is correct) and handled by hand.

Run: python3 scripts/fix_grey_text.py
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP = {REPO/"index.html", REPO/"featured"/"index.html"}

GREY = "#574C63"     # readable dark-grey, 7.5:1 on cream / 6.8:1 on tints
VIOLET = "#7C3AED"   # deeper violet, ~4.9:1 on cream
BLUE = "#2563EB"     # readable blue

MAP = {}
for h in ["c6c6d8","c2c2d4","c0c0d8","c9c9d6","c9bee0","b6b6cc","b0b0c8","b6b6c8",
          "9a94a6","9090a8","8888a8","8080a0","7878a0","7070a0"]:
    MAP[h] = GREY
for h in ["a78bfa","c4b5fd","c084fc","8b5cf6"]:
    MAP[h] = VIOLET
MAP["7aa8ff"] = BLUE

# match  color: #hex  (optional space), only inside color declarations
PAT = re.compile(r'(color\s*:\s*)#([0-9a-fA-F]{6})')

def fix(text):
    def repl(m):
        h = m.group(2).lower()
        return m.group(1)+MAP[h] if h in MAP else m.group(0)
    return PAT.sub(repl, text)

def main():
    files = list(REPO.rglob("*.html")) + list(REPO.rglob("*.css"))
    changed = 0; hits = 0
    for f in files:
        if f in SKIP or "/node_modules/" in str(f): continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        n = sum(1 for m in PAT.finditer(t) if m.group(2).lower() in MAP)
        if n:
            f.write_text(fix(t), encoding="utf-8"); changed += 1; hits += n
    print(f"remapped {hits} color decls across {changed} files (skipped {len(SKIP)} dark-mixed)")

if __name__ == "__main__":
    main()
