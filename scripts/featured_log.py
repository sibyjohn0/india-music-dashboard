#!/usr/bin/env python3
"""Persistent no-repeat ledger for IIM social content.
Records every artist/venue/topic that has been featured, so generators never
repeat one that's already gone out.

data/featured_log.json shape:
  {"radar": ["name", ...],
   "venues": {"mumbai": ["Venue", ...], ...},
   "topics": ["release-playbook", ...]}

Matching is case-insensitive + whitespace-trimmed.
"""
import json, os
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "data" / "featured_log.json"

def _load():
    try:
        return json.load(open(LOG))
    except Exception:
        return {"radar": [], "venues": {}, "topics": []}

def _save(d):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(LOG, "w"), indent=2, ensure_ascii=False)

def featured_radar():
    """Lowercased set of artist names already featured."""
    return {n.strip().lower() for n in _load().get("radar", [])}

def featured_venues(city):
    return {n.strip().lower() for n in _load().get("venues", {}).get(city.lower(), [])}

def featured_topics():
    return {t.strip().lower() for t in _load().get("topics", [])}

def record_radar(names):
    d = _load(); seen = {n.strip().lower() for n in d["radar"]}
    for n in names:
        if n.strip().lower() not in seen:
            d["radar"].append(n); seen.add(n.strip().lower())
    _save(d)

def record_venues(city, names):
    d = _load(); v = d.setdefault("venues", {}); lst = v.setdefault(city.lower(), [])
    seen = {n.strip().lower() for n in lst}
    for n in names:
        if n.strip().lower() not in seen:
            lst.append(n); seen.add(n.strip().lower())
    _save(d)

def record_topic(topic):
    d = _load()
    if topic.strip().lower() not in {t.strip().lower() for t in d["topics"]}:
        d["topics"].append(topic); _save(d)
