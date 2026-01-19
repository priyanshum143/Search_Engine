"""
This file will act as a main file to run our search engine
"""

import asyncio

from src.search_engine.crawler import WebCrawler
from src.search_engine.indexer import Indexer
from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.string_utils import tokenize_content_into_list_of_words

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

    logger.info("Starting crawler and indexer in background")
    crawler_task = asyncio.create_task(crawler.start_crawler())
    indexer_task = asyncio.create_task(
        indexer.start_indexing(crawler.page_model_frontier, crawler.crawl_done)
    )

    logger.info("Ready to accept queries.")
    try:
        while True:
            query = await asyncio.to_thread(input, "Enter the query: ")
            query = query.strip()
            if not query:
                continue

            tokens = tokenize_content_into_list_of_words(query)
            logger.info(f"Got the query [{tokens}], Looking for appropriate response")
            for token in tokens:
                logger.info(f"{token} -> {indexer.inverted_index.get(token, {})}")


    except KeyboardInterrupt:
        logger.info("Shutdown signal received...")

    finally:
        await crawler_task
        await indexer_task
        await crawler.async_rest_client.aclose()
        logger.info("Search Engine stopped gracefully.")


if __name__ == "__main__":
    asyncio.run(main())
