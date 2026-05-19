#!/usr/bin/env python3
"""
One-time backfill: add genre + language to existing videos in latest.json,
recompute breakdowns, and regenerate the monthly summary.
"""
import json, os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def detect_language(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Tamil",     ["tamil", "thamizh", "kollywood"]),
        ("Telugu",    ["telugu", "tollywood"]),
        ("Punjabi",   ["punjabi", "panjabi"]),
        ("Bengali",   ["bengali", "bangla"]),
        ("Kannada",   ["kannada", "sandalwood"]),
        ("Malayalam", ["malayalam", "mollywood"]),
        ("Marathi",   ["marathi"]),
    ]
    for lang, keywords in checks:
        if any(k in text for k in keywords):
            return lang
    return "Hindi"

def detect_genre(title, tags, description):
    text = (title + " " + " ".join(tags) + " " + description).lower()
    checks = [
        ("Lo-Fi",           ["lo-fi", "lofi", "lo fi", "chill beats", "study beats"]),
        ("Hip Hop / Rap",   ["hip hop", "hip-hop", "rap", "rapper", "trap", "drill", "freestyle"]),
        ("Jazz / Blues",    ["jazz", "blues", "fusion jazz", "swing"]),
        ("Folk / Acoustic", ["folk", "acoustic", "unplugged", "sufi", "baul"]),
        ("Electronic",      ["electronic", "edm", "techno", "house", "ambient", "synthwave", "downtempo"]),
        ("R&B / Soul",      ["r&b", "rnb", "soul", "neo soul", "rhythm and blues"]),
        ("Indie Pop",       ["indie pop", "bedroom pop", "dream pop", "shoegaze"]),
        ("Rock / Alt",      ["rock", "metal", "punk", "alternative", "grunge", "post-rock"]),
        ("Classical/Fusion",["classical", "carnatic", "hindustani", "raag", "fusion classical"]),
    ]
    for genre, keywords in checks:
        if any(k in text for k in keywords):
            return genre
    return "Indie"

def build_breakdowns(videos):
    genre_count, lang_count = {}, {}
    for v in videos:
        g = v.get("genre") or "Indie"
        l = v.get("language") or "Hindi"
        genre_count[g] = genre_count.get(g, 0) + 1
        lang_count[l]  = lang_count.get(l,  0) + 1
    return (
        sorted(genre_count.items(), key=lambda x: -x[1]),
        sorted(lang_count.items(),  key=lambda x: -x[1]),
    )

def main():
    path = os.path.join(DATA_DIR, "latest.json")
    with open(path) as f:
        data = json.load(f)

    videos = data["videos"]
    updated = 0
    for v in videos:
        if not v.get("genre") or not v.get("language"):
            tags = v.get("tags") or []
            desc = v.get("description") or ""
            title = v.get("title") or ""
            v["language"] = detect_language(title, tags, desc)
            v["genre"]    = detect_genre(title, tags, desc)
            updated += 1

    genre_b, lang_b = build_breakdowns(videos)
    data["genre_breakdown"]    = genre_b
    data["language_breakdown"] = lang_b

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Updated {updated}/{len(videos)} videos with genre/language")
    print("Genre spread:", ", ".join(f"{g}:{c}" for g,c in genre_b))
    print("Language spread:", ", ".join(f"{l}:{c}" for l,c in lang_b))

    # Regenerate monthly summary
    fetched = data.get("fetched_at", "")
    month_key = fetched[:7] if fetched else datetime.now(timezone.utc).strftime("%Y-%m")
    date_str  = fetched[:10] if fetched else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    top_channels = {}
    for v in videos:
        top_channels[v["channel"]] = top_channels.get(v["channel"], 0) + 1
    summary = {
        "month":            month_key,
        "last_updated":     date_str,
        "total_videos":     len(videos),
        "total_views":      sum(v["views"] for v in videos),
        "genre_breakdown":  genre_b,
        "language_breakdown": lang_b,
        "top_channels":     sorted(top_channels.items(), key=lambda x: -x[1])[:10],
    }
    monthly_path = os.path.join(DATA_DIR, "monthly", f"{month_key}.json")
    os.makedirs(os.path.dirname(monthly_path), exist_ok=True)
    with open(monthly_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Monthly summary written → {monthly_path}")
    print(f"  {summary['total_videos']} videos, {summary['total_views']:,} views")

if __name__ == "__main__":
    main()
