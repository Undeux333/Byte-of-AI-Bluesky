#!/usr/bin/env python3

import sys
import time
from datetime import datetime, timezone, timedelta

import state_manager as sm
import fetchers
import scorer
import poster

from config import COLLECTION_INTERVAL_HOURS

DRY_RUN = "--dry-run" in sys.argv

def run():
    print(f"\n{'='*60}")
    print(f" BOT PIPELINE [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}]")
    print(f" DRY RUN: {DRY_RUN}")
    print(f"{'='*60}\n")

    state = sm.load()
    stats = sm.get_stats(state)
    print(f"[State] Queue={stats['queue_size']} Posted={stats['total_posted']} "
          f"SeenURLs={stats['seen_urls']} Carryover={stats['carryover']}")

    # 次回収集予定時刻を表示
    last = state.get("last_collected")
    if last:
        last_dt = datetime.fromisoformat(last)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        next_dt = last_dt + timedelta(hours=COLLECTION_INTERVAL_HOURS)
        JST = timezone(timedelta(hours=9))
        print(f"[State] Next collection: {next_dt.astimezone(JST).strftime('%Y-%m-%d %H:%M JST')}")
    else:
        print(f"[State] Next collection: running now (first time)")

    # ── Step 1: 収集 ──────────────────────────────────────────────
    if sm.collection_needed(state, COLLECTION_INTERVAL_HOURS):
        print(f"\n[Pipeline] Collection needed. Running...\n")

        if not DRY_RUN:
            poster.refresh_token()

        stories = fetchers.collect_all(state)
        for s in stories:
            sm.mark_seen(state, s["url"])

        if stories:
            candidates = scorer.score_all(stories, state)
            for c in candidates:
                sm.add_to_queue(state, {
                    "tweet":          c["tweet"],
                    "original_url":   c.get("original_url", c.get("url", "")),
                    "buzz_score":     c.get("buzz_score", 0),
                    "buzz_score2":    c.get("buzz_score2", 0),
                    "rewrite_count":  c.get("rewrite_count", 0),
                    "original_title": c.get("original_title", ""),
                    "source":         c.get("source", ""),
                    "category":       c.get("category", "other"),
                })
            state["stats"]["total_collected"] = \
                state["stats"].get("total_collected", 0) + len(candidates)
            print(f"\n[Pipeline] Added {len(candidates)} items to queue.")

        sm.mark_collected(state)
        sm.save(state)
        print("[Pipeline] State saved after collection.\n")
    else:
        print("[Pipeline] Collection not needed yet.\n")

    # ── Step 2: 投稿（2件）──────────────────────────────────────────────
    for post_num in range(1, 3):
        item = sm.pop_next(state)
        if not item:
            print(f"[Pipeline] Queue empty at post {post_num} — stopping.")
            break

        tweet_text   = item.get("tweet", "")
        original_url = item.get("original_url", "")
        category     = item.get("category", "other")

        print(f"[Pipeline] Posting item {post_num}/2...")
        print(f"  Tweet: {tweet_text[:100]}...")
        print(f"  URL:   {original_url[:80]}")

        if DRY_RUN:
            print(f"\n[Pipeline] DRY RUN — skipping actual post {post_num}.")
            print(f"\n--- TWEET PREVIEW {post_num} ---\n{tweet_text}\n")
            if original_url:
                print(f"--- REPLY (URL) ---\n🔗 Source: {original_url}\n---")
        else:
            result = poster.post_tweet(
                tweet_text=tweet_text,
                original_url=original_url,
                category=category,
            )
            if result.get("success"):
                sm.mark_posted(state)
                print(f"[Pipeline] Post {post_num} succeeded!")
            else:
                state["queue"].insert(0, item)
                print(f"[Pipeline] Post {post_num} failed — item returned to queue.")
                break

        # 2件目の前に5分待機（連投対策）
        if post_num == 1:
            print(f"[Pipeline] Waiting 5 minutes before next post...")
            time.sleep(300)

    sm.save(state)
    stats = sm.get_stats(state)
    print(f"\n[Stats] Queue={stats['queue_size']} TotalPosted={stats['total_posted']}")

if __name__ == "__main__":
    run()
