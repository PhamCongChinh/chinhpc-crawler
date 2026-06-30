import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "dantri_news")
CRAWL_DELAY_MIN_SECONDS = float(os.getenv("CRAWL_DELAY_MIN_SECONDS", "2"))
CRAWL_DELAY_MAX_SECONDS = float(os.getenv("CRAWL_DELAY_MAX_SECONDS", "5"))
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))

REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DantriCrawler/1.0)",
    "Accept-Language": "vi-VN,vi;q=0.9",
}
