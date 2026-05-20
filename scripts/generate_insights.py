#!/usr/bin/env python3
"""
Generates per-language (and per-language/genre) insights from accumulated
daily history files. Runs after fetch_youtube.py each day.

Output: data/insights.json
"""
import json, os, glob
from datetime import datetime, timezone
from collections import defaultdict

DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data")
HISTORY_DIR  = os.path.join(DATA_DIR, "history")
OUTPUT_PATH  = os.path.join(DATA_DIR, "insights.json")

LANGUAGES = ["Tamil","Telugu","Kannada","Malayalam","Bengali","Punjabi","Marathi","Hindi","English"]


def load_history():
    """Return sorted list of (date_str, videos) from all history files."""
    days = []
    for path in sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json"))):
        date = os.path.basename(path).replace(".json", "")
        try:
            with open(path) as f:
                data = json.load(f)
            videos = data.get("videos", [])
            if videos:
                days.append((date, videos))
        except Exception:
            pass
    return days


def channel_key(v):
    return v.get("channel_id") or v.get("channel", "")


def build_language_insights(days):
    """
    For each language, accumulate channel appearances, genre counts,
    engagement, and velocity across all history days.
    """
    # lang → { channel_id → {name, appearances, total_views, total_eng, genres} }
    lang_channels   = defaultdict(lambda: defaultdict(lambda: {
        "name": "", "appearances": 0, "total_views": 0,
        "total_eng": 0.0, "genres": defaultdict(int)
    }))
    lang_genre_days = defaultdict(lambda: defaultdict(int))  # lang → genre → day_count
    lang_day_views  = defaultdict(lambda: defaultdict(int))  # lang → date → views
    lang_day_count  = defaultdict(lambda: defaultdict(int))  # lang → date → video count

    for date, videos in days:
        for v in videos:
            lang  = v.get("language") or "Hindi"
            genre = v.get("genre")   or "Indie"
            ckey  = channel_key(v)
            ch    = lang_channels[lang][ckey]
            ch["name"]         = v.get("channel", "")
            ch["appearances"]  += 1
            ch["total_views"]  += v.get("views", 0)
            ch["total_eng"]    += v.get("engagement_rate", 0)
            ch["genres"][genre] += 1
            lang_genre_days[lang][genre] += 1
            lang_day_views[lang][date]   += v.get("views", 0)
            lang_day_count[lang][date]   += 1

    insights = {}
    num_days  = len(days)

    for lang in LANGUAGES:
        channels = lang_channels.get(lang, {})
        if not channels:
            insights[lang] = {"days_tracked": num_days, "status": "no data yet"}
            continue

        # Top recurring artists (appeared most days)
        sorted_ch = sorted(channels.values(), key=lambda c: (-c["appearances"], -c["total_views"]))
        top_artists = [
            {
                "name":        c["name"],
                "appearances": c["appearances"],
                "avg_views":   round(c["total_views"] / max(c["appearances"], 1)),
                "avg_eng":     round(c["total_eng"]   / max(c["appearances"], 1), 1),
                "top_genre":   max(c["genres"], key=c["genres"].get) if c["genres"] else "Indie",
            }
            for c in sorted_ch[:5]
        ]

        # Genre breakdown (how many day-appearances each genre has)
        genre_counts = lang_genre_days.get(lang, {})
        sorted_genres = sorted(genre_counts.items(), key=lambda x: -x[1])
        dominant_genre = sorted_genres[0][0] if sorted_genres else "Indie"

        # Per-genre sub-insights
        genre_insights = {}
        for genre, _ in sorted_genres[:5]:
            genre_ch = {
                ckey: c for ckey, c in channels.items()
                if c["genres"].get(genre, 0) > 0
            }
            genre_top = sorted(genre_ch.values(), key=lambda c: -c["genres"].get(genre, 0))[:3]
            genre_insights[genre] = {
                "day_appearances": genre_counts[genre],
                "top_artists": [{"name": c["name"], "appearances": c["genres"][genre]} for c in genre_top],
            }

        # Total views trend across days
        day_views = lang_day_views.get(lang, {})
        sorted_days = sorted(day_views.items())
        view_trend = [{"date": d, "views": v, "videos": lang_day_count[lang].get(d, 0)}
                      for d, v in sorted_days]

        # Simple text narrative
        recs = [c["name"] for c in sorted_ch if c["appearances"] >= 2]
        narrative_parts = []
        if num_days == 1:
            narrative_parts.append(f"First day of tracking {lang} indie.")
        elif recs:
            narrative_parts.append(
                f"Recurring artists across {num_days} days: {', '.join(recs[:3])}."
            )
        else:
            narrative_parts.append(f"No artists yet appearing across multiple days.")
        narrative_parts.append(
            f"Dominant genre: {dominant_genre} "
            f"({sorted_genres[0][1]} video-appearances across {num_days} day(s))."
        )
        if len(sorted_genres) > 1:
            others = ", ".join(f"{g} ({c})" for g, c in sorted_genres[1:4])
            narrative_parts.append(f"Also tracked: {others}.")

        insights[lang] = {
            "days_tracked":    num_days,
            "dominant_genre":  dominant_genre,
            "top_artists":     top_artists,
            "genre_breakdown": [{"genre": g, "day_appearances": c} for g, c in sorted_genres],
            "genre_insights":  genre_insights,
            "view_trend":      view_trend,
            "narrative":       " ".join(narrative_parts),
        }

    return insights


def main():
    days = load_history()
    if not days:
        print("No history files found — skipping insights generation.")
        return

    print(f"Generating insights from {len(days)} history day(s): {[d for d,_ in days]}")
    insights = build_language_insights(days)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days_of_data": len(days),
        "date_range":   {"from": days[0][0], "to": days[-1][0]},
        "languages":    insights,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written → {OUTPUT_PATH}")
    for lang in LANGUAGES:
        ins = insights.get(lang, {})
        if ins.get("status") == "no data yet":
            print(f"  {lang}: no data")
        else:
            print(f"  {lang}: {ins['dominant_genre']} dominant | top: {[a['name'] for a in ins['top_artists'][:2]]}")


if __name__ == "__main__":
    main()
