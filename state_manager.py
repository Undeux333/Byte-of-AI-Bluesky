import json
import os
from datetime import datetime, timezone, timedelta

STATE_PATH = "data/state.json"

def _default_state() -> dict:
    return {
        "last_collected":       None,
        "queue":                [],
        "seen_urls":            [],
        "carryover_candidates": [],
        "stats": {
            "total_posted":    0,
            "total_collected": 0,
        }
    }

def load() -> dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            if "carryover_candidates" not in state:
                state["carryover_candidates"] = []
            return state
        except Exception as e:
            print(f"[State] Load error: {e} — using default")
    if os.path.exists("state.json"):
        try:
            with open("state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            if "carryover_candidates" not in state:
                state["carryover_candidates"] = []
            return state
        except Exception:
            pass
    return _default_state()

def save(state: dict):
    os.makedirs("data", exist_ok=True)
    # seen_urlsは最新1000件のみ保持
    if len(state.get("seen_urls", [])) > 1000:
        state["seen_urls"] = state["seen_urls"][-1000:]
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def collection_needed(state: dict, interval_hours: float) -> bool:
    last = state.get("last_collected")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
        return elapsed >= interval_hours
    except Exception:
        return True

def mark_collected(state: dict):
    state["last_collected"] = datetime.now(timezone.utc).isoformat()

def mark_seen(state: dict, url: str):
    if url and url not in state.get("seen_urls", []):
        state.setdefault("seen_urls", []).append(url)

def add_to_queue(state: dict, item: dict):
    state.setdefault("queue", []).append(item)

def _final_score(item: dict) -> float:
    """Post-time score: buzz_score2(70%) + buzz_score(10%) + freshness(20%)"""
    buzz2 = item.get("buzz_score2", 0)
    buzz1 = item.get("buzz_score", 0)

    added_at = item.get("added_at")
    if added_at:
        try:
            added_dt = datetime.fromisoformat(added_at)
            if added_dt.tzinfo is None:
                added_dt = added_dt.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - added_dt).total_seconds() / 3600
            freshness = max(0, 20 - age_hours * 2)
        except Exception:
            freshness = 10
    else:
        freshness = 10

    return buzz2 * 0.7 + buzz1 * 0.1 + freshness * 0.2


def pop_next(state: dict) -> dict | None:
    queue = state.get("queue", [])
    if not queue:
        return None
    queue.sort(key=_final_score, reverse=True)
    item = queue.pop(0)
    state["queue"] = queue
    return item

def mark_posted(state: dict):
    state.setdefault("stats", {})
    state["stats"]["total_posted"] = state["stats"].get("total_posted", 0) + 1

def get_stats(state: dict) -> dict:
    return {
        "queue_size":    len(state.get("queue", [])),
        "total_posted":  state.get("stats", {}).get("total_posted", 0),
        "seen_urls":     len(state.get("seen_urls", [])),
        "carryover":     len(state.get("carryover_candidates", [])),
    }
