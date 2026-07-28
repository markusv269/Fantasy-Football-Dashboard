import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

CHANNEL_ID = "UCMD4pfyYl2hxHez34eqnfkQ"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
_feed_cache: dict = {"entries": [], "fetched_at": 0}
CACHE_TTL = 600


def _rss_urls() -> list[str]:
    """Return configured RSS URLs in priority order without duplicates."""
    configured = os.environ.get("YOUTUBE_RSS_URLS", "")
    urls = [url.strip() for url in configured.split(",") if url.strip()]
    urls.append(RSS_URL)
    return list(dict.fromkeys(urls))


def fetch_youtube_feed(limit: int = 15) -> list[dict]:
    """Fetch the latest real videos from the Stoned Lack RSS feed."""
    import time

    now = time.time()
    cached_entries = _feed_cache.get("entries", [])
    if cached_entries and now - _feed_cache["fetched_at"] < CACHE_TTL:
        return cached_entries[:limit]

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }

    for url in _rss_urls():
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; StonedLack/1.0)"
                },
            )
            if response.status_code != 200:
                logging.warning(
                    "YouTube RSS request returned HTTP %s for %s",
                    response.status_code,
                    url,
                )
                continue
            root = ET.fromstring(response.content)
            entries = []
            for entry in root.findall("atom:entry", ns):
                video_id_element = entry.find("yt:videoId", ns)
                video_id = (
                    video_id_element.text
                    if video_id_element is not None
                    else ""
                )
                title_element = entry.find("atom:title", ns)
                title = title_element.text if title_element is not None else ""
                published_element = entry.find("atom:published", ns)
                published = (
                    published_element.text
                    if published_element is not None
                    else ""
                )
                link_element = entry.find("atom:link", ns)
                link = (
                    link_element.get("href", "")
                    if link_element is not None
                    else ""
                )
                media_group = entry.find("media:group", ns)
                thumbnail = ""
                description = ""
                views = 0
                if media_group is not None:
                    thumbnail_element = media_group.find("media:thumbnail", ns)
                    if thumbnail_element is not None:
                        thumbnail = thumbnail_element.get("url", "")
                    description_element = media_group.find(
                        "media:description", ns
                    )
                    if (
                        description_element is not None
                        and description_element.text
                    ):
                        description = description_element.text
                    statistics_element = media_group.find(
                        "media:community/media:statistics", ns
                    )
                    if statistics_element is not None:
                        try:
                            views = int(statistics_element.get("views", "0"))
                        except (TypeError, ValueError):
                            logging.warning(
                                "Invalid YouTube view count for video %s",
                                video_id or "unknown",
                            )
                date_str = ""
                if published:
                    try:
                        date_str = datetime.fromisoformat(
                            published.replace("Z", "+00:00")
                        ).strftime("%d. %b %Y")
                    except (TypeError, ValueError):
                        logging.warning(
                            "Invalid YouTube publication date for video %s",
                            video_id or "unknown",
                        )
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
                        "is_short": "/shorts/" in link,
                        "type": "Short" if "/shorts/" in link else "Video",
                    }
                )
            _feed_cache["entries"] = entries
            _feed_cache["fetched_at"] = now
            return entries[:limit]
        except ET.ParseError as e:
            logging.exception("Unexpected error")
            logging.warning("Invalid YouTube RSS response from %s: %s", url, e)
        except requests.RequestException as e:
            logging.exception("Unexpected error")
            logging.warning("YouTube RSS request failed for %s: %s", url, e)
        except Exception as e:
            logging.exception("Unexpected error")
            logging.warning(
                "YouTube RSS feed could not be read from %s: %s", url, e
            )

    return cached_entries[:limit]
