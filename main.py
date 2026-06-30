import argparse
import logging
import random
import time
import sys

import config
from crawlers.dantri.feeds import FEEDS
from crawlers.dantri import rss_fetcher, article_parser
from storage import mongodb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_once():
    logger.info("=== Bắt đầu crawl dantri.com.vn (%d feeds) ===", len(FEEDS))
    total_new = 0
    total_skip = 0

    for category, rss_url in FEEDS.items():
        articles = rss_fetcher.fetch_feed(category, rss_url)

        for meta in articles:
            url = meta["_id"]

            if mongodb.exists(url):
                total_skip += 1
                continue

            # Lấy nội dung đầy đủ từ trang bài viết
            detail = article_parser.parse(url)
            time.sleep(random.uniform(config.CRAWL_DELAY_MIN_SECONDS, config.CRAWL_DELAY_MAX_SECONDS))

            # Gộp metadata từ RSS + detail từ HTML
            article = {**meta, **detail}
            # Ưu tiên categories từ HTML (breadcrumb) nếu có, không thì giữ từ RSS
            if not detail.get("categories"):
                article["categories"] = meta.get("categories", [])

            mongodb.upsert(article)
            total_new += 1
            logger.info("  [+] %s", meta["title"][:80])

    logger.info("=== Xong: %d bài mới, %d bài bỏ qua (đã có) ===", total_new, total_skip)
    mongodb.close()


def main():
    parser = argparse.ArgumentParser(description="Crawler dantri.com.vn")
    parser.add_argument(
        "--once",
        action="store_true",
        default=True,
        help="Chạy 1 lần rồi thoát (mặc định)",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Chạy định kỳ theo SCHEDULE_INTERVAL_MINUTES",
    )
    args = parser.parse_args()

    if args.schedule:
        import scheduler as sched
        sched.start()
    else:
        run_once()


if __name__ == "__main__":
    main()
