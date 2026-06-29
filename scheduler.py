import logging
from apscheduler.schedulers.blocking import BlockingScheduler

import config
import main as crawler_main

logger = logging.getLogger(__name__)


def start():
    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        crawler_main.run_once,
        trigger="interval",
        minutes=config.SCHEDULE_INTERVAL_MINUTES,
        id="dantri_crawl",
        replace_existing=True,
    )
    logger.info(
        "Scheduler khởi động, chạy mỗi %d phút", config.SCHEDULE_INTERVAL_MINUTES
    )
    # Chạy ngay lần đầu khi start
    crawler_main.run_once()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler dừng.")
