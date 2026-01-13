"""
This file will contain the code to crawl the web pages
"""

import httpx
from bs4 import BeautifulSoup
import asyncio
from typing import List

# Add project root to path
# import sys
# from pathlib import Path
# project_root = Path(__file__).resolve().parent.parent.parent
# sys.path.insert(0, str(project_root))

from src.search_engine.utils.variables import CommonVariables
from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.string_utils import normalize_url
from src.search_engine.utils.requests import prepare_async_requests, hit_async_requests

logger = get_logger(__name__)


class WebCrawler:
    """
    This class is responsible for crawling web pages.
    """
    
    def __init__(self) -> None:
        # Initalizing some variables which we will need for crawling
        self.async_rest_client = httpx.AsyncClient(follow_redirects=True)
        self.visited_urls = set()
        self.urls_crawled = 0

        # Initializing URL frontier with seed URLs
        self.url_frontier = asyncio.Queue()
        logger.debug(f"Initializing URL frontier with seed URLs: {CommonVariables.SEED_URLS}")
        for url in CommonVariables.SEED_URLS:
            self.url_frontier.put_nowait(url)
    
    async def fetch_pages_for_urls_and_return_response(self) -> List[httpx.Response]:
        """
        This method will fetch the web pages for the URLs in the URL frontier.

        Returns:
            List[httpx.Response]: A list of HTTP responses for the fetched web pages.
        """

        urls = []

        logger.debug("Fetching the URLs from the queue for crawling.")
        while not self.url_frontier.empty():
            url = self.url_frontier.get_nowait()
            url = normalize_url(url)
            logger.debug(f"Picked up URL: {url} for crawling from the queue.")

            logger.debug(f"Checking if URL: {url} has already been visited.")
            if url in self.visited_urls:
                logger.debug(f"URL: {url} has already been visited. Skipping.")
                continue

            urls.append(url)
            self.visited_urls.add(url)

        requests = prepare_async_requests(urls, self.async_rest_client)
        responses = await hit_async_requests(requests, self.async_rest_client)
