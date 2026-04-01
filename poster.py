import time
import requests
from bs4 import BeautifulSoup
from atproto import Client
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD


def _get_client() -> Client:
    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    return client


def refresh_token() -> bool:
    print(f"  [Poster] Bluesky: no token refresh needed")
    return True


def fetch_link_card(url: str) -> dict:
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
    try:
        res = requests.get(image_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        content_type = res.headers.get("Content-Type", "image/jpeg").split(";")[0]
        blob = client.upload_blob(res.content)
        return {"$type": "blob", "ref": blob.blob.ref, "mimeType": content_type, "size": len(res.content)}
    except Exception as e:
        print(f"  [Poster] Image upload error: {e}")
        return None


def post_tweet(tweet_text: str, original_url: str = "", category: str = "other") -> dict:
    """
    Blueskyに投稿する
    - 本投稿: テキストのみ（URLはリンクカードembedで表示）
    - リンクカード（OGP画像）が自動展開される
    - タグなし
    """
    main_text = tweet_text.split("\nhttp")[0].split("\nhttps")[0].strip()

    # 本文は300文字以内に収める（URLはembedで表示するのでテキストには含めない）
    if len(main_text) > 300:
        main_text = main_text[:300].rstrip()
        print(f"  [Poster] Text trimmed to {len(main_text)} chars")

    full_text = main_text

    for attempt in range(3):
        try:
            client = _get_client()

            # リンクカードembedを構築
            embed = None
            if original_url:
                card = fetch_link_card(original_url)
                thumb_blob = None
                if card.get("image_url"):
                    thumb_blob = upload_image_blob(client, card["image_url"])
                external = {
                    "$type":       "app.bsky.embed.external#external",
                    "uri":         original_url,
                    "title":       card.get("title", ""),
                    "description": card.get("description", ""),
                }
                if thumb_blob:
                    external["thumb"] = thumb_blob
                embed = {"$type": "app.bsky.embed.external", "external": external}

            post_params = {"text": full_text}
            if embed:
                post_params["embed"] = embed

            post = client.send_post(**post_params)
            print(f"  [Poster] Posted: {post.uri}")
            print(f"           Text: {main_text[:80]}...")
            return {"post_id": post.uri, "success": True}

        except Exception as e:
            print(f"  [Poster] Error on attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(5)

    print(f"  [Poster] post_tweet failed after 3 attempts")
    return {"success": False}
