import logging
import requests
from bs4 import BeautifulSoup, Tag

import config

logger = logging.getLogger(__name__)


def _find_main_article(soup: BeautifulSoup) -> Tag | None:
    """
    dantri dùng Tailwind utility classes (dt-*).
    Content article có class dt-flex dt-flex-col dt-gap-6.
    Related article items có class dt-py-5 dt-flex dt-gap-[15px]...
    """
    for article in soup.find_all("article"):
        classes = article.get("class") or []
        if "dt-flex-col" in classes:
            return article
    # Fallback: <main class="body container"> → first <article>
    main = soup.find("main", class_="body")
    if main:
        return main.find("article")
    return None


def _extract_content(soup: BeautifulSoup) -> str:
    """Extract main article body text."""
    article = _find_main_article(soup)
    if not article:
        return ""
    paragraphs = article.find_all("p")
    return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))


def _extract_images(soup: BeautifulSoup) -> list[dict]:
    """Extract images with captions from article body."""
    article = _find_main_article(soup)
    if not article:
        return []

    images = []
    for figure in article.find_all("figure"):
        img = figure.find("img")
        caption_el = figure.find("figcaption")
        if img:
            src = img.get("src") or img.get("data-src", "")
            images.append({
                "url": src,
                "caption": caption_el.get_text(strip=True) if caption_el else img.get("alt", ""),
            })

    # Fallback: standalone img tags (không nằm trong figure)
    if not images:
        for img in article.find_all("img"):
            if img.find_parent("figure"):
                continue
            src = img.get("src") or img.get("data-src", "")
            if src and "cdnphoto" in src:
                images.append({"url": src, "caption": img.get("alt", "")})

    return images


def _extract_tags(soup: BeautifulSoup) -> list[str]:
    """
    dantri dùng /tim-kiem/[keyword].htm làm link cho các từ khóa trong bài.
    """
    import re
    article = _find_main_article(soup)
    if not article:
        return []
    tag_links = [
        a.get_text(strip=True)
        for a in article.find_all("a", href=re.compile(r"/tim-kiem/"))
        if a.get_text(strip=True)
    ]
    return tag_links


def _extract_categories(soup: BeautifulSoup) -> list[str]:
    """Extract breadcrumb categories."""
    # dantri breadcrumb thường là ol hoặc nav với các a tags
    for sel in ["ol.breadcrumb a", "nav[aria-label='breadcrumb'] a", "div.breadcrumb a"]:
        crumbs = [a.get_text(strip=True) for a in soup.select(sel) if a.get_text(strip=True)]
        if crumbs:
            return crumbs

    # Fallback: tìm các a link nằm trong phần đầu bài với dạng /[category]/
    import re
    main = soup.find("main")
    if main:
        # Lấy các link đầu trang trước article chính
        header_links = main.find_all("a", href=re.compile(r'^https://dantri\.com\.vn/[a-z\-]+\.htm$'))
        cats = [a.get_text(strip=True) for a in header_links if a.get_text(strip=True)]
        if cats:
            return cats[:3]
    return []


def parse(url: str) -> dict:
    """Fetch và parse một trang bài viết dantri. Trả về dict các field extracted."""
    try:
        resp = requests.get(
            url,
            headers=config.REQUEST_HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("Failed to fetch article %s: %s", url, e)
        return {}

    soup = BeautifulSoup(resp.text, "lxml")

    return {
        "content": _extract_content(soup),
        "images": _extract_images(soup),
        "tags": _extract_tags(soup),
        "categories": _extract_categories(soup),
    }
