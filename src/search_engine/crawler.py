"""
This file will contain the code to crawl the web pages
"""

import asyncio
import json
import httpx
from typing import List
from bs4 import BeautifulSoup
from dataclasses import asdict
from pathlib import Path

from src.search_engine.models.PageModel import PageModel

from src.search_engine.utils.variables import CommonVariables
from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.string_utils import normalize_url, generate_content_hash
from src.search_engine.utils.requests import prepare_async_requests, hit_async_requests
from src.search_engine.utils.parse_html import (
    extract_outgoing_links_from_soup,
    extract_headings_from_soup,
    extract_title_from_soup,
    extract_content_from_soup,
)

logger = get_logger(__name__)


class WebCrawler:
    """
    This class is responsible for crawling web pages.
    """
    
    def __init__(self) -> None:
        # Initialising some variables which we will need for crawling
        self.async_rest_client = httpx.AsyncClient(
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            timeout=30.0
        )
        self.visited_urls = set()
        self.urls_crawled = 0

        # Initializing URL frontier with seed URLs
        self.url_frontier = asyncio.Queue(maxsize=CommonVariables.MAX_LIMIT)
        logger.debug(f"Initializing URL frontier with seed URLs: {CommonVariables.SEED_URLS}")
        for url in CommonVariables.SEED_URLS:
            self.url_frontier.put_nowait(url)
    
    async def _fetch_pages_for_urls_and_return_response(self) -> List[httpx.Response]:
        """
        This method will fetch the web pages for the URLs in the URL frontier.

        Returns:
            List[httpx.Response]: A list of HTTP responses for the fetched web pages.
        """

        urls = []

        logger.debug("Fetching the URLs from the queue for crawling.")
        count = 0
        while not self.url_frontier.empty() and count < CommonVariables.BATCH_SIZE:
            url = self.url_frontier.get_nowait()
            url = normalize_url(url)

            logger.debug(f"Checking if URL: {url} has already been visited.")
            if url in self.visited_urls:
                logger.debug(f"URL: {url} has already been visited. Skipping.")
                continue
            logger.debug(f"Picked up URL: {url} for crawling from the queue.")


            urls.append(url)
            self.visited_urls.add(url)
            count += 1

        requests = prepare_async_requests(urls, self.async_rest_client)
        responses = await hit_async_requests(requests, self.async_rest_client)
        return responses

    async def _add_urls_in_queue(self, urls: List[str]) -> None:
        """
        This method will check the queue capacity and accordingly will add the given URLs in the queue

        Args:
            urls: List of URLs needs to be added

        Returns:
            None
        """

        # Calculate available space
        queue_size = self.url_frontier.qsize()
        available_space = CommonVariables.MAX_LIMIT - queue_size
        logger.debug(
            f"Attempting to add {len(urls)} URLs. Queue: {queue_size}/{CommonVariables.MAX_LIMIT}, Available: {available_space}"
        )
        if available_space <= 0:
            logger.debug(f"Queue is full. Current size: {queue_size}, Max limit: {CommonVariables.MAX_LIMIT}")
            return

        # Determine how many URLs we can add
        urls_len = len(urls)
        urls_to_add = min(urls_len, available_space)

        # Add URLs to queue
        added_count = 0
        for url in urls[:urls_to_add]:
            normalized = normalize_url(url)
            if normalized not in self.visited_urls:
                await self.url_frontier.put(normalized)
                added_count += 1

        logger.debug(
            f"Successfully added {added_count} new URLs to queue (skipped {urls_to_add - added_count} duplicates)"
        )
        logger.debug(f"New queue size: {self.url_frontier.qsize()}/{CommonVariables.MAX_LIMIT}")

        # Log if we couldn't add all URLs
        if urls_to_add < urls_len:
            logger.debug(f"Could not add {urls_len - urls_to_add} URLs due to queue capacity limit")

    async def _parse_response_and_make_page_model(self, responses: List[httpx.Response]) -> None:
        """
        This method will parse the list of http responses and extract useful information
        and will make a page model for each page
        
        Args:
            responses (List[httpx.Response]): List of HTTP responses to parse.

        Returns:
            None
        """

        # Checking if the JSONL file present or not, if not then create a file
        Path(CommonVariables.JSONL_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

        # Parsing each response and making a PageModel for each response
        with open(CommonVariables.JSONL_FILE_PATH, 'a', encoding='utf-8') as f:
            iterator = 0
            for response in responses:
                if not isinstance(response, httpx.Response):
                    logger.debug(f"Skipping invalid response object: {type(response)}")
                    continue

                logger.debug(f"Iterating response {iterator}/{len(responses)}")
                # Checking the status code of the response
                url = str(response.request.url)
                if response.status_code != httpx.codes.OK:
                    logger.debug(f"Status code for URL [{url}] is {response.status_code}\n content: {response.content}")
                    continue

                # Creating a soup object based on content type
                content_type = response.headers.get('Content-Type', '').lower()
                if 'xml' in content_type:
                    parser = 'xml'
                else:
                    parser = 'html.parser'
                soup = BeautifulSoup(response.content, parser)

                # Fetching required details
                content = extract_content_from_soup(soup)
                doc_id = generate_content_hash(content)
                links = extract_outgoing_links_from_soup(soup)

                # Building the PageModel
                page_model = PageModel(
                    doc_id=doc_id,
                    url=url,
                    final_url=str(response.url),
                    http_status=response.status_code,
                    title=extract_title_from_soup(soup),
                    headings=extract_headings_from_soup(soup),
                    content=content,
                    links=links
                )

                # Adding the fetched URLs in the frontier queue
                await self._add_urls_in_queue(links)

                # Writing the data in JSONL file
                f.write(json.dumps(asdict(page_model), ensure_ascii=False) + '\n')
                f.flush()

                # Increasing the iterator
                iterator += 1

    async def start_crawler(self) -> None:
        """
        This method is main method to start our crawler
        """
        iteration = 0

        while not self.url_frontier.empty():
            iteration += 1
            logger.debug(f"=== ITERATION {iteration} START ===")
            logger.debug(f"Queue size at start: {self.url_frontier.qsize()}")
            logger.debug(f"Visited URLs count: {len(self.visited_urls)}")

            responses = await self._fetch_pages_for_urls_and_return_response()
            logger.debug(f"Fetched {len(responses)} responses")
            logger.debug(f"Queue size after fetch: {self.url_frontier.qsize()}")

            await self._parse_response_and_make_page_model(responses)
            logger.debug(f"Queue size after parsing: {self.url_frontier.qsize()}")
            logger.debug(f"=== ITERATION {iteration} END ===\n")

        logger.debug(f"Crawler stopped. Final queue size: {self.url_frontier.qsize()}")
        logger.debug(f"Total URLs visited: {len(self.visited_urls)}")
