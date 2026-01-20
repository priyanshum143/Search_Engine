"""
This file will act as a main file to run our search engine
"""

import asyncio

from src.search_engine.crawler import WebCrawler
from src.search_engine.indexer import Indexer
from src.search_engine.query_response import QueryParser
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

            logger.info(f"Got the query [{query}], Looking for appropriate response")
            result = await QueryParser.generate_response_for_query(
                query, indexer.inverted_index, indexer.doc_store
            )
            if not result:
                print("\nNo results found.\n")
            else:
                print("\nSearch Results:\n")
                for i, doc in enumerate(result, 1):
                    print(f"{i}. {doc.get('title', '[NO TITLE]')}")
                    print(f"   URL: {doc.get('url', '')}\n")

    except KeyboardInterrupt:
        logger.info("Shutdown signal received...")

    finally:
        await crawler_task
        await indexer_task
        await crawler.async_rest_client.aclose()
        logger.info("Search Engine stopped gracefully.")


if __name__ == "__main__":
    asyncio.run(main())
