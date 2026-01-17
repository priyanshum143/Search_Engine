"""
This file will act as a main file to run our search engine
"""

import asyncio

from src.search_engine.crawler import WebCrawler
from src.search_engine.indexer import Indexer
from src.search_engine.utils.loggers import get_logger

crawler = WebCrawler()
indexer = Indexer()
logger = get_logger(__name__)


async def main():
    """
    This method is the main method to start backend for the search engine
    1) Crawl
    2) Index
    3) Accept user queries
    """

    logger.info("Starting the search engine")

    try:
        logger.info("Crawling started")
        await crawler.start_crawler()
        logger.info("Crawling completed successfully.")

        logger.info("Starting indexing the raw crawled data")
        await indexer.iterate_crawled_data_and_make_inverted_index()
        logger.info("Indexing done, ready to accept queries.")

    except KeyboardInterrupt:
        logger.info("Shutdown signal received...")

    finally:
        await crawler.async_rest_client.aclose()
        logger.info("Search Engine stopped gracefully.")


if __name__ == "__main__":
    asyncio.run(main())
