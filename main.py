"""
This file will act as a main file to run our search engine
"""

import asyncio

from src.search_engine.crawler import WebCrawler
from src.search_engine.utils.loggers import get_logger

crawler = WebCrawler()
logger = get_logger(__name__)


async def main():
    """
    This is the main method which we will call to run our search engine
    """

    logger.info("Starting the search engine")

    # Start crawler as background task
    logger.info("Crawling initiated")
    crawler_task = asyncio.create_task(crawler.start_crawler())

    try:
        await asyncio.Future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received...")
    finally:
        crawler_task.cancel()
        await crawler.async_rest_client.aclose()
        logger.info("Crawler stopped gracefully.")


if __name__ == "__main__":
    asyncio.run(main())
