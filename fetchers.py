import feedparser
import requests
from datetime import datetime, timezone

# ── RSS Sources ───────────────────────────────────────────────────────────────
RSS_SOURCES = [
    # World News
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml",           "source": "BBC World",       "category": "world"},
    {"url": "https://feeds.reuters.com/reuters/topNews",             "source": "Reuters",          "category": "world"},
    {"url": "https://feeds.npr.org/1001/rss.xml",                    "source": "NPR News",         "category": "world"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",             "source": "Al Jazeera",       "category": "world"},
    {"url": "https://www.theguardian.com/world/rss",                 "source": "The Guardian",     "category": "world"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml","source": "NYT World",        "category": "world"},

    # Tech
    {"url": "https://techcrunch.com/feed/",                          "source": "TechCrunch",       "category": "tech"},
    {"url": "https://www.theverge.com/rss/index.xml",                "source": "The Verge",        "category": "tech"},
    {"url": "http://feeds.arstechnica.com/arstechnica/index",        "source": "Ars Technica",     "category": "tech"},
    {"url": "https://www.wired.com/feed/rss",                        "source": "Wired",            "category": "tech"},

    # Science
    {"url": "https://www.sciencedaily.com/rss/all.xml",              "source": "ScienceDaily",     "category": "science"},
    {"url": "https://www.newscientist.com/feed/home/",               "source": "New Scientist",    "category": "science"},

    # Entertainment / Youth culture
    {"url": "https://www.rollingstone.com/feed/",                    "source": "Rolling Stone",    "category": "entertainment"},
    {"url": "https://variety.com/feed/",                             "source": "Variety",          "category": "entertainment"},
    {"url": "https://deadline.com/feed/",                            "source": "Deadline",         "category": "entertainment"},
    {"url": "https://www.billboard.com/feed/",                       "source": "Billboard",        "category": "entertainment"},
    {"url": "https://www.ign.com/rss/articles.rss",                  "source": "IGN",              "category": "entertainment"},
    {"url": "https://kotaku.com/rss",                                "source": "Kotaku",           "category": "entertainment"},

    # Sports
    {"url": "https://www.espn.com/espn/rss/news",                    "source": "ESPN",             "category": "sports"},
    {"url": "http://feeds.bbci.co.uk/sport/rss.xml",                 "source": "BBC Sport",        "category": "sports"},
    {"url": "https://www.theringer.com/rss/index.xml",               "source": "The Ringer",       "category": "sports"},

    # Psychology / Mental health
    {"url": "https://www.psychologytoday.com/us/front-page/feed",    "source": "Psychology Today", "category": "psychology"},
    {"url": "https://psypost.org/feed",                              "source": "PsyPost",          "category": "psychology"},

    # Lifestyle / Relationships
    {"url": "https://www.refinery29.com/en-us/rss.xml",             "source": "Refinery29",       "category": "lifestyle"},
    {"url": "https://www.cosmopolitan.com/feed/",                    "source": "Cosmopolitan",     "category": "lifestyle"},

    # Lifehacks / Tips
    {"url": "https://lifehacker.com/feed/rss",                       "source": "Lifehacker",       "category": "lifestyle"},

    # Business
    {"url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",          "source": "WSJ",              "category": "business"},

    # Feel-good / Chaos
    {"url": "https://www.upworthy.com/feed",                         "source": "Upworthy",         "category": "lifestyle"},
    {"url": "https://www.goodnewsnetwork.org/feed/",                 "source": "Good News Network","category": "lifestyle"},

    # Gen Z / Youth culture
    {"url": "https://www.vulture.com/rss/all.xml",                   "source": "Vulture",          "category": "entertainment"},
    {"url": "https://www.thecut.com/rss/all.xml",                    "source": "The Cut",          "category": "lifestyle"},
    {"url": "https://www.complex.com/rss",                           "source": "Complex",          "category": "entertainment"},
    {"url": "https://hypebeast.com/feed",                            "source": "Hypebeast",        "category": "entertainment"},
    {"url": "https://www.polygon.com/rss/index.xml",                 "source": "Polygon",          "category": "entertainment"},
    {"url": "https://www.inverse.com/rss",                           "source": "Inverse",          "category": "science"},
    {"url": "https://ew.com/feed/",                                  "source": "Entertainment Weekly", "category": "entertainment"},
    {"url": "https://www.indiewire.com/feed/",                       "source": "IndieWire",        "category": "entertainment"},

    # Netflix
    {"url": "https://usa.newonnetflix.info/feed",                    "source": "New on Netflix",   "category": "entertainment"},
    {"url": "https://www.theverge.com/rss/netflix/index.xml",        "source": "The Verge Netflix","category": "entertainment"},

    # Sex & Relationships（新規）
    {"url": "https://www.cosmopolitan.com/sex-love/rss/",            "source": "Cosmo Sex & Love", "category": "sex"},
    {"url": "https://www.menshealth.com/rss/sex-women.xml",          "source": "Men's Health Sex", "category": "sex"},
    {"url": "https://www.bustle.com/rss",                            "source": "Bustle",           "category": "sex"},

    # Lifestyle TIPS
    {"url": "https://www.menshealth.com/rss/all.xml",                "source": "Men's Health",     "category": "lifestyle"},

    # Trivia & Facts（新規）
    {"url": "https://www.mentalfloss.com/feed",                      "source": "Mental Floss",     "category": "trivia"},
    {"url": "https://bigthink.com/feed",                             "source": "Big Think",        "category": "trivia"},
    {"url": "https://knowablemagazine.org/rss",                      "source": "Knowable Magazine","category": "trivia"},
]

# ── HackerNews ────────────────────────────────────────────────────────────────
HN_MIN_SCORE = 150


def _freshness_weight(entry: dict) -> int:
    """記事の公開日時から鮮度スコアを計算（0〜10）"""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return 5  # 日時不明は中間値
    try:
        pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
        hours_old = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
        if hours_old <= 6:
            return 5
        elif hours_old <= 12:
            return 3
        elif hours_old <= 24:
            return 2
        elif hours_old <= 48:
            return 1
        else:
            return 0
    except Exception:
        return 5


def fetch_rss(seen_urls: set) -> list[dict]:
    stories = []
    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            count = 0
            for entry in feed.entries:
                if count >= 10:
                    break
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "")[:300]
                if not title:
                    continue
                stories.append({
                    "title":    title,
                    "url":      url,
                    "summary":  summary,
                    "source":   src["source"],
                    "category": src["category"],
                    "weight":   _freshness_weight(entry),  # 鮮度スコアをweightに反映
                })
                count += 1
        except Exception as e:
            print(f"  [RSS] {src['source']} error: {e}")
    return stories


def fetch_hackernews(seen_urls: set) -> list[dict]:
    stories = []
    try:
        res = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        )
        ids = res.json()[:60]
        for item_id in ids:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=5
                ).json()
                if not item or item.get("type") != "story":
                    continue
                score = item.get("score", 0)
                if score < HN_MIN_SCORE:
                    continue
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                title = item.get("title", "").strip()

                # HNはtimeフィールド（UNIXタイムスタンプ）で鮮度を計算
                hn_time = item.get("time")
                if hn_time:
                    pub_dt = datetime.fromtimestamp(hn_time, tz=timezone.utc)
                    hours_old = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                    if hours_old <= 6:
                        freshness = 5
                    elif hours_old <= 12:
                        freshness = 3
                    elif hours_old <= 24:
                        freshness = 2
                    elif hours_old <= 48:
                        freshness = 1
                    else:
                        freshness = 0
                else:
                    freshness = 3

                stories.append({
                    "title":    title,
                    "url":      url,
                    "summary":  f"HN Score: {score} | Comments: {item.get('descendants', 0)}",
                    "source":   "HackerNews",
                    "category": "tech",
                    "weight":   min(10, freshness + (score // 200)),  # 鮮度 + HNスコアの加算
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [HN] error: {e}")
    return stories


def collect_all(state: dict) -> list[dict]:
    seen = set(state.get("seen_urls", []))
    stories = []

    print("  [Fetcher] Fetching RSS...")
    rss = fetch_rss(seen)
    print(f"  [Fetcher] RSS: {len(rss)} stories")
    stories.extend(rss)

    print("  [Fetcher] Fetching HackerNews...")
    hn = fetch_hackernews(seen)
    print(f"  [Fetcher] HN: {len(hn)} stories")
    stories.extend(hn)

    print(f"  [Fetcher] Total: {len(stories)} stories collected")
    return stories
