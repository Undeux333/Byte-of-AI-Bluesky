import time
import requests
from bs4 import BeautifulSoup
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


def fetch_link_card(url: str) -> dict:
    """元記事からOGPメタデータを取得してリンクカード用データを返す"""
    try:
        res = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag       = soup.find("meta", property="og:title")
        description_tag = soup.find("meta", property="og:description")
        image_tag       = soup.find("meta", property="og:image")

        title       = title_tag["content"].strip()       if title_tag       else ""
        description = description_tag["content"].strip() if description_tag else ""
        image_url   = image_tag["content"].strip()       if image_tag       else ""

        # og:imageが相対パスの場合フルURLに変換
        if image_url and image_url.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"

        print(f"  [Poster] Link card: {title[:50]}...")
        return {"title": title, "description": description, "image_url": image_url}

    except Exception as e:
        print(f"  [Poster] Link card fetch error: {e}")
        return {"title": "", "description": "", "image_url": ""}


def upload_image_blob(client: Client, image_url: str) -> dict | None:
    """画像URLからBlueskyにblobとしてアップロード"""
    try:
        res = requests.get(image_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        content_type = res.headers.get("Content-Type", "image/jpeg").split(";")[0]
        blob = client.upload_blob(res.content)
        return {"$type": "blob", "ref": blob.blob.ref, "mimeType": content_type, "size": len(res.content)}
    except Exception as e:
        print(f"  [Poster] Image upload error: {e}")
        return None


def post_tweet(tweet_text: str, topic_tag: str = "", original_url: str = "", category: str = "other") -> dict:
    """
    Blueskyに投稿する
    - 本投稿: テキスト + タグ + リンクカード（画像埋め込み）
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

            # リンクカードを取得してembedを構築
            embed = None
            if original_url:
                card = fetch_link_card(original_url)

                # サムネイル画像をアップロード
                thumb_blob = None
                if card.get("image_url"):
                    thumb_blob = upload_image_blob(client, card["image_url"])

                # external embed（リンクカード）を構築
                external = {
                    "$type": "app.bsky.embed.external#external",
                    "uri":         original_url,
                    "title":       card.get("title", ""),
                    "description": card.get("description", ""),
                }
                if thumb_blob:
                    external["thumb"] = thumb_blob

                embed = {
                    "$type":    "app.bsky.embed.external",
                    "external": external,
                }

            # 本投稿（リンクカード付き）
            post_params = {"text": main_text}
            if embed:
                post_params["embed"] = embed

            post = client.send_post(**post_params)
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
