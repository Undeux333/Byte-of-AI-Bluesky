import json
import os
from datetime import datetime, timezone

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
    # buzz_score2の高い順に並び替え
    state["queue"].sort(
        key=lambda x: x.get("buzz_score2", x.get("buzz_score", 0)),
        reverse=True
    )

def pop_next(state: dict) -> dict | None:
    queue = state.get("queue", [])
    if not queue:
        return None
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
