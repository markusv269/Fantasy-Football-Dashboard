import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime

CHANNEL_ID = "UCMD4pfyYl2hxHez34eqnfkQ"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
_feed_cache: dict = {"entries": [], "fetched_at": 0}
CACHE_TTL = 600


def fetch_youtube_feed(limit: int = 15) -> list[dict]:
    """Fetch latest videos from the Stoned Lack YouTube channel RSS feed."""
    import time

    now = time.time()
    if _feed_cache["entries"] and now - _feed_cache["fetched_at"] < CACHE_TTL:
        return _feed_cache["entries"][:limit]
    try:
        r = requests.get(RSS_URL, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }
        entries = []
        for entry in root.findall("atom:entry", ns):
            video_id = entry.find("yt:videoId", ns).text
            title = entry.find("atom:title", ns).text or ""
            published = entry.find("atom:published", ns).text or ""
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            media_group = entry.find("media:group", ns)
            thumbnail = ""
            description = ""
            views = 0
            if media_group is not None:
                thumb_el = media_group.find("media:thumbnail", ns)
                if thumb_el is not None:
                    thumbnail = thumb_el.get("url", "")
                desc_el = media_group.find("media:description", ns)
                if desc_el is not None and desc_el.text:
                    description = desc_el.text
                stats_el = media_group.find("media:community/media:statistics", ns)
                if stats_el is not None:
                    views = int(stats_el.get("views", "0"))
            is_short = "/shorts/" in link
            date_str = ""
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    date_str = dt.strftime("%d. %b %Y")
                except Exception:
                    logging.exception("Unexpected error")
                    date_str = published[:10]
            entries.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "published": published,
                    "date_str": date_str,
                    "link": link,
                    "thumbnail": thumbnail,
                    "description": description[:300],
                    "views": views,
                    "is_short": is_short,
                    "type": "Short" if is_short else "Video",
                }
            )
        _feed_cache["entries"] = entries
        _feed_cache["fetched_at"] = now
        return entries[:limit]
    except Exception as e:
        logging.exception(f"Error fetching YouTube feed: {e}")
        return _feed_cache.get("entries", [])[:limit]