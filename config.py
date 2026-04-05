import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-3.1-flash-lite-preview"

# ── Bluesky ──────────────────────────────────────────────────────────────────
BLUESKY_HANDLE       = os.getenv("BLUESKY_HANDLE", "")       # 例: yourname.bsky.social
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "") # App Password推奨

# ── Bot settings ──────────────────────────────────────────────────────────────
COLLECTION_INTERVAL_HOURS = 2  # 収集間隔（時間）
POSTS_PER_COLLECTION      = 16  # Geminiが生成する投稿数/収集
CARRYOVER_MAX             = 8  # 持ち越し候補の最大件数
CARRYOVER_TTL_HOURS       = 8  # 持ち越し有効期限（時間）
QUEUE_MAX                 = 96  # キューの最大件数
QUEUE_TTL_HOURS           = 24  # キューの有効期限（時間）
SLEEP_MAX_SECONDS         = 300  # ランダム待機の上限（秒）

# ── Category colors (for internal use) ────────────────────────────────────────
CATEGORY_COLORS = {
    "world":         "#E24B4A",
    "tech":          "#378ADD",
    "science":       "#1D9E75",
    "sports":        "#BA7517",
    "entertainment": "#7F77DD",
    "lifestyle":     "#D85A30",
    "psychology":    "#D4537E",
    "business":      "#888780",
    "sex":           "#E8527A",
    "trivia":        "#20A89A",
    "other":         "#5F5E5A",
}
