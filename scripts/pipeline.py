#!/usr/bin/env python3
"""
Unified pipeline orchestrator for India Indie Music Dashboard.

Runs all data sources with per-source try/except. On failure, copies the
last successful data file as a fallback so the site never goes empty.
Appends one entry to data/pipeline-log.json (never overwrites).
Writes data/pipeline-status.json with the latest run summary.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
SCRIPTS_DIR = REPO_ROOT / "scripts"

LOG_PATH = DATA_DIR / "pipeline-log.json"
STATUS_PATH = DATA_DIR / "pipeline-status.json"

# Map source name -> (script, env vars required, fallback file pairs)
# fallback_pairs: list of (primary_output, fallback_source_glob)
SOURCES = [
    {
        "name": "youtube",
        "script": "fetch_youtube.py",
        "env_required": ["YOUTUBE_API_KEY"],
        "outputs": ["data/latest.json"],
        "history_glob": "data/history/*.json",
    },
    {
        "name": "lastfm",
        "script": "enrich_lastfm.py",
        "env_required": ["LASTFM_API_KEY"],
        "outputs": ["data/lastfm_enrichment.json"],
    },
    {
        "name": "radar",
        "script": "build_radar.py",
        "env_required": [],
        "outputs": ["data/tracked_artists.json"],
    },
    {
        "name": "insights",
        "script": "generate_insights.py",
        "env_required": [],
        "outputs": ["data/insights.json"],
    },
    {
        "name": "venue_analysis",
        "script": "analyze_venues.py",
        "env_required": [],
        "outputs": ["data/venue-insights.json"],
    },
    {
        "name": "spotify",
        "script": "fetch_spotify.py",
        "env_required": ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"],
        "outputs": ["data/spotify_enrichment.json"],
    },
    {
        "name": "social",
        "script": "fetch_social.py",
        "env_required": [],
        "outputs": ["data/social.json"],
    },
    {
        "name": "playboard",
        "script": "fetch_playboard.py",
        "env_required": [],
        "outputs": ["data/playboard.json"],
    },
    {
        "name": "jiosaavn",
        "script": "fetch_jiosaavn.py",
        "env_required": [],
        "outputs": ["data/jiosaavn.json"],
    },
    {
        "name": "events_paytm",
        "script": "fetch_events_paytm.py",
        "env_required": [],
        "outputs": ["data/events-paytm.json"],
    },
    {
        "name": "news_rss",
        "script": "fetch_news_rss.py",
        "env_required": [],
        "outputs": ["data/news-rss.json"],
    },
    {
        "name": "events_district",
        "script": "fetch_events_district.py",
        "env_required": [],
        "outputs": ["data/events-district.json"],
    },
    {
        "name": "spotify_playwright",
        "script": "fetch_spotify_playwright.py",
        "env_required": [],
        "outputs": ["data/spotify_playwright.json"],
    },
    {
        "name": "bookmyshow",
        "script": "fetch_bookmyshow.py",
        "env_required": [],
        "outputs": ["data/events-bookmyshow.json"],
    },
    {
        "name": "skillboxes",
        "script": "fetch_skillboxes.py",
        "env_required": [],
        "outputs": ["data/events-skillboxes.json"],
    },
    {
        "name": "highape",
        "script": "fetch_highape.py",
        "env_required": [],
        "outputs": ["data/events-highape.json"],
    },
    # Weekly reviewer sources — included here so pipeline tracks them.
    # These are only triggered on Sunday via the --reviewers flag or directly.
    {
        "name": "reviewers_editorial",
        "script": "fetch_reviewers_editorial.py",
        "env_required": [],
        "outputs": [],
        "reviewers_only": True,
    },
    {
        "name": "reviewers_podcasts",
        "script": "fetch_reviewers_podcasts.py",
        "env_required": [],
        "outputs": [],
        "reviewers_only": True,
    },
    {
        "name": "reviewers_spotify",
        "script": "fetch_reviewers_spotify.py",
        "env_required": ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"],
        "outputs": [],
        "reviewers_only": True,
    },
    {
        "name": "reviewers_youtube",
        "script": "fetch_reviewers_youtube.py",
        "env_required": ["YOUTUBE_API_KEY"],
        "outputs": [],
        "reviewers_only": True,
    },
    {
        "name": "reviewers_merge",
        "script": "merge_reviewers.py",
        "env_required": [],
        "outputs": ["data/reviewers.json"],
        "reviewers_only": True,
    },
]


def find_fallback(output_path: str):
    """
    Find the most recent file that could serve as a fallback for output_path.
    For data/latest.json, tries data/history/*.json.
    For other files, uses the file itself (if it already exists from a prior run).
    """
    p = REPO_ROOT / output_path
    if p.exists():
        return str(p)
    # For latest.json specifically, pull from history
    if output_path == "data/latest.json":
        history_dir = DATA_DIR / "history"
        if history_dir.exists():
            snapshots = sorted(history_dir.glob("*.json"))
            if snapshots:
                return str(snapshots[-1])
    return None


def copy_fallback(output_path: str, source: dict) -> bool:
    """Copy existing file as fallback if primary output is missing or failed."""
    p = REPO_ROOT / output_path
    fb = find_fallback(output_path)
    if fb and str(fb) != str(p):
        try:
            os.makedirs(p.parent, exist_ok=True)
            shutil.copy2(fb, p)
            print(f"  [fallback] copied {fb} -> {p}")
            return True
        except Exception as e:
            print(f"  [fallback] FAILED to copy {fb} -> {p}: {e}", file=sys.stderr)
    return False


def run_source(source: dict) -> dict:
    """
    Run a single source script. Returns a result dict:
      status: "ok" | "failed" | "skipped"
      records: int or None
      ms: int
      error: str or None
    """
    name = source["name"]
    script = str(SCRIPTS_DIR / source["script"])
    env_required = source.get("env_required", [])

    t0 = time.monotonic()

    # Check required env vars
    missing = [v for v in env_required if not os.environ.get(v)]
    if missing:
        ms = int((time.monotonic() - t0) * 1000)
        msg = f"Missing env vars: {', '.join(missing)}"
        print(f"[{name}] SKIPPED — {msg}")
        return {"status": "skipped", "records": None, "ms": ms, "error": msg}

    print(f"[{name}] Running {source['script']}...")
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(REPO_ROOT),
        )
        ms = int((time.monotonic() - t0) * 1000)

        if result.stdout:
            for line in result.stdout.strip().splitlines():
                print(f"  {line}")
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                print(f"  ERR: {line}", file=sys.stderr)

        if result.returncode != 0:
            error_msg = (result.stderr.strip().splitlines() or ["non-zero exit"])[-1]
            print(f"[{name}] FAILED (exit {result.returncode}) after {ms}ms")
            # Activate fallback for each output
            for out in source.get("outputs", []):
                copy_fallback(out, source)
            return {"status": "failed", "records": None, "ms": ms, "error": error_msg}

        # Count records from primary output if it exists
        records = count_records(source)
        print(f"[{name}] OK in {ms}ms | records={records}")
        return {"status": "ok", "records": records, "ms": ms, "error": None}

    except subprocess.TimeoutExpired:
        ms = int((time.monotonic() - t0) * 1000)
        print(f"[{name}] TIMEOUT after {ms}ms")
        for out in source.get("outputs", []):
            copy_fallback(out, source)
        return {"status": "failed", "records": None, "ms": ms, "error": "timeout"}

    except Exception as e:
        ms = int((time.monotonic() - t0) * 1000)
        print(f"[{name}] ERROR: {e}")
        for out in source.get("outputs", []):
            copy_fallback(out, source)
        return {"status": "failed", "records": None, "ms": ms, "error": str(e)}


def count_records(source: dict):
    """Try to extract a record count from the source's primary output file."""
    for out in source.get("outputs", []):
        p = REPO_ROOT / out
        if not p.exists():
            continue
        try:
            with open(p) as f:
                data = json.load(f)
            # Try common keys for record counts
            for key in ("total", "videos", "artists", "entries", "items",
                        "enrichment", "posts", "reviewers"):
                val = data.get(key)
                if isinstance(val, int):
                    return val
                if isinstance(val, (list, dict)):
                    return len(val)
        except Exception:
            pass
    return None


def load_log() -> list:
    """Load the existing pipeline log (returns [] if missing or corrupt)."""
    if not LOG_PATH.exists():
        return []
    try:
        with open(LOG_PATH) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_log(entries: list) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def save_status(entry: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATUS_PATH, "w") as f:
        json.dump(entry, f, indent=2)


def overall_status(results: dict) -> str:
    statuses = [r["status"] for r in results.values()]
    if all(s == "ok" for s in statuses):
        return "ok"
    if all(s == "failed" for s in statuses):
        return "failed"
    return "partial"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="India Music Dashboard pipeline orchestrator")
    parser.add_argument(
        "--reviewers",
        action="store_true",
        help="Also run reviewer refresh sources (weekly cadence)",
    )
    args = parser.parse_args()

    run_at = datetime.now(timezone.utc).isoformat()
    print(f"=== India Music Dashboard Pipeline ===")
    print(f"Started: {run_at}")
    print(f"Reviewer refresh: {'yes' if args.reviewers else 'no'}")
    print()

    source_results = {}

    for source in SOURCES:
        is_reviewers_only = source.get("reviewers_only", False)
        if is_reviewers_only and not args.reviewers:
            # Skip but don't log it — it wasn't scheduled to run
            continue
        result = run_source(source)
        source_results[source["name"]] = result
        print()

    overall = overall_status(source_results)
    print(f"=== Pipeline complete: {overall.upper()} ===")
    for name, r in source_results.items():
        rec = f"records={r['records']}" if r["records"] is not None else ""
        err = f" | error={r['error']}" if r.get("error") else ""
        print(f"  {name}: {r['status']} | {r['ms']}ms {rec}{err}")

    log_entry = {
        "run_at": run_at,
        "overall": overall,
        "sources": source_results,
    }

    # Append to log (never overwrite)
    log = load_log()
    log.append(log_entry)
    save_log(log)
    print(f"\nAppended to {LOG_PATH} (total entries: {len(log)})")

    # Overwrite status (always latest)
    status_entry = {
        "last_run": run_at,
        "overall": overall,
        "sources": source_results,
    }
    save_status(status_entry)
    print(f"Written {STATUS_PATH}")

    # Exit non-zero only if everything failed — partial runs are acceptable
    if overall == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
