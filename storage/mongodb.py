import logging
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection

import config

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_collection: Collection | None = None


def get_collection() -> Collection:
    global _client, _collection
    if _collection is None:
        _client = MongoClient(config.MONGODB_URI)
        db = _client[config.MONGODB_DB]
        _collection = db["articles"]
        _collection.create_index([("published_at", DESCENDING)])
        _collection.create_index("rss_category")
        logger.info("Connected to MongoDB: %s / %s", config.MONGODB_DB, "articles")
    return _collection


def exists(url: str) -> bool:
    col = get_collection()
    return col.count_documents({"_id": url}, limit=1) > 0


def upsert(article: dict) -> None:
    col = get_collection()
    doc = {**article, "crawled_at": datetime.now(timezone.utc)}
    col.update_one({"_id": article["_id"]}, {"$set": doc}, upsert=True)


def close() -> None:
    global _client, _collection
    if _client:
        _client.close()
        _client = None
        _collection = None
