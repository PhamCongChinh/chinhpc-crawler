import re
import time
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

import config

logger = logging.getLogger(__name__)

VN_TZ = timezone(timedelta(hours=7))


def _parse_pub_date(entry) -> datetime | None:
    """Parse feedparser's published_parsed (UTC struct_time) → aware datetime."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return None


def _extract_thumbnail(description_html: str) -> str:
    """Extract first <img src> from RSS description HTML."""
    if not description_html:
        return ""
    soup = BeautifulSoup(description_html, "lxml")
    img = soup.find("img")
    if img:
        return img.get("src", "")
    return ""


def _extract_summary(description_html: str) -> str:
    """Extract plain text summary (excluding image) from RSS description HTML."""
    if not description_html:
        return ""
    soup = BeautifulSoup(description_html, "lxml")
    for img in soup.find_all("img"):
        img.decompose()
    return soup.get_text(separator=" ", strip=True)


def _extract_slug_and_id(url: str) -> tuple[str, str]:
    """Extract slug and numeric article ID from dantri URL."""
    match = re.search(r"/([^/]+)-(\d{17,})\.htm$", url)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def fetch_feed(category: str, rss_url: str) -> list[dict]:
    """Fetch and parse one RSS feed. Returns list of article metadata dicts."""
    try:
        resp = requests.get(
            rss_url,
            headers=config.REQUEST_HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Failed to fetch feed %s: %s", rss_url, e)
        return []

    feed = feedparser.parse(resp.content)
    articles = []

    for entry in feed.entries:
        url = entry.get("link", "").strip()
        if not url:
            continue

        slug, article_id = _extract_slug_and_id(url)
        description_html = entry.get("summary", "")
        categories = [t.get("term", "") for t in entry.get("tags", [])]

        articles.append({
            "_id": url,
            "url": url,
            "slug": slug,
            "article_id": article_id,
            "title": entry.get("title", "").strip(),
            "author": entry.get("author", "").strip(),
            "published_at": _parse_pub_date(entry),
            "rss_category": category,
            "categories": [c for c in categories if c],
            "summary": _extract_summary(description_html),
            "thumbnail_url": _extract_thumbnail(description_html),
            "source": "dantri",
        })

    logger.info("Feed [%s]: %d articles", category, len(articles))
    time.sleep(config.CRAWL_DELAY_SECONDS)
    return articles
