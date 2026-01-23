"""
This file will act as a main file to run our search engine
"""

import asyncio
import threading
from flask import Flask, request, jsonify, render_template

from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.variables import CommonVariables
from src.search_engine.crawler import WebCrawler
from src.search_engine.indexer import Indexer
from src.search_engine.query_response import QueryParser

app = Flask(__name__)
logger = get_logger(__name__)

crawler = WebCrawler()
indexer = Indexer()
bg_loop = asyncio.new_event_loop()


# -------------------------------- METHOD TO START AND STOP BACKGROUND TASK --------------------------------------------


def start_async_services():
    """
    This method will start the crawling and indexing in background
    """

    asyncio.set_event_loop(bg_loop)
    logger.info("Starting crawler and indexer in background event loop")

    bg_loop.create_task(crawler.start_crawler())
    bg_loop.create_task(
        indexer.start_indexing(crawler.page_model_frontier, crawler.crawl_done)
    )

    bg_loop.run_forever()


def shutdown_async_services():
    """
    This method will shut down the crawler and indexer
    """

    async def _shutdown():
        try:
            await crawler.async_rest_client.aclose()
        except (asyncio.TimeoutError, RuntimeError, OSError) as e:
            logger.warning(
                f"Failed to close the rest client being used by crawler with error: {e}"
            )

    asyncio.run_coroutine_threadsafe(_shutdown(), bg_loop).result(
        timeout=CommonVariables.TIMEOUT
    )
    bg_loop.call_soon_threadsafe(bg_loop.stop)


# ------------------------------------ METHOD TO RENDER SEARCH RESULTS -------------------------------------------------


@app.get("/")
def home():
    """
    This method will render the home page of our search engine
    """

    return render_template("index.html")


@app.get("/search")
def search():
    """
    This method will render the search results
    """

    query_text = request.args.get("q", "").strip()
    if not query_text:
        return jsonify([])

    # Submit the async search work to the background asyncio loop
    search_future = asyncio.run_coroutine_threadsafe(
        QueryParser.generate_response_for_query(
            query_text,
            indexer.inverted_index,
            indexer.doc_store,
        ),
        bg_loop,
    )

    try:
        search_results = search_future.result(timeout=120)
    except Exception as e:
        logger.exception("Search failed")
        return jsonify({"error": str(e)}), 500

    return jsonify(search_results)


# ----------------------------------------------------- MAIN METHOD ----------------------------------------------------


def main():
    """
    This is our main method to start our search engine
    Returns:

    """
    thread = threading.Thread(target=start_async_services, daemon=True)
    thread.start()
    try:
        app.run(debug=True, use_reloader=False)
    finally:
        shutdown_async_services()


if __name__ == "__main__":
    main()
