import time
from atproto import Client, client_utils
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD, CATEGORY_TAGS

def _get_client() -> Client:
    """Blueskyクライアントを生成してログイン"""
    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    return client


def refresh_token() -> bool:
    """Blueskyはセッションベースのためトークン更新不要"""
    print(f"  [Poster] Bluesky: no token refresh needed")
    return True


def post_tweet(tweet_text: str, topic_tag: str = "", original_url: str = "", category: str = "other") -> dict:
    """
    Blueskyに投稿する
    - 本投稿: テキスト + タグ + SourceURL（全て1投稿に統合）
    - リンクカードが本投稿に展開される
    """
    main_text = tweet_text.split("\nhttp")[0].split("\nhttps")[0].strip()

    # Geminiのタグを優先、なければカテゴリタグをフォールバック
    if topic_tag and topic_tag.startswith("#") and len(topic_tag) > 1:
        tag = topic_tag
    else:
        tag = CATEGORY_TAGS.get(category, "")

    # タグを改行して本文に追加
    if tag and tag.startswith("#") and len(tag) > 1:
        main_text = f"{main_text}\n\n{tag}"
        print(f"  [Poster] Topic tag: {tag}")

    for attempt in range(3):
        try:
            client = _get_client()

            # URLをリンクとして本文に追加（タグの下に改行して挿入）
            if original_url:
                post_text = client_utils.TextBuilder()                    .text(main_text)                    .text("\n\n🔗 ")                    .link("Source", original_url)
            else:
                post_text = main_text

            # 本投稿（URL統合・リンクカード付き）
            post = client.send_post(text=post_text)
            post_uri = post.uri
            print(f"  [Poster] Posted: {post_uri}")
            print(f"           Text: {main_text[:80]}...")

            return {"post_id": post_uri, "success": True}

        except Exception as e:
            print(f"  [Poster] Error on attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(5)

    print(f"  [Poster] post_tweet failed after 3 attempts")
    return {"success": False}
