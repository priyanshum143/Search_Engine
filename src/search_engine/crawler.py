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
            headers=CommonVariables.HEADERS,
            timeout=10,
        )
        self.visited_urls = set()
        self.urls_crawled = 0

        # Initializing URL frontier with seed URLs
        self.url_frontier = asyncio.Queue(maxsize=CommonVariables.MAX_LIMIT)
        logger.debug(
            f"Initializing URL frontier with seed URLs: [{CommonVariables.SEED_URLS}] "
            f"and with max limit [{CommonVariables.MAX_LIMIT}]"
        )
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

        count = 1
        while (
            not self.url_frontier.empty()
            and count <= CommonVariables.BATCH_SIZE
            and len(self.visited_urls) <= CommonVariables.MAX_LIMIT
        ):
            # Normalizing the URL
            url = self.url_frontier.get_nowait()
            url = normalize_url(url)

            # Adding the URL in list to get response
            self.visited_urls.add(url)
            urls.append(url)
            count += 1

        requests = prepare_async_requests(urls, self.async_rest_client)
        responses = await hit_async_requests(requests, self.async_rest_client)
        return responses

    async def _parse_response_and_make_page_model(
        self, response: httpx.Response
    ) -> PageModel | None:
        """
        This method will parse the http responses and extract useful information
        and will make a page model for each page

        Args:
            response httpx.Response: HTTP responses to parse.

        Returns:
            PageModel or None
        """

        try:
            # Checking if the response is proper or not
            if not isinstance(response, httpx.Response):
                logger.debug(f"Skipping invalid response object: {type(response)}")
                return None

            # Checking the status code of the response
            url = str(response.request.url)
            if response.status_code != httpx.codes.OK:
                logger.debug(
                    f"Status code for URL [{url}] is {response.status_code}\n content: {response.content}"
                )
                return None

            # Checking the content type
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type and "xml" not in content_type:
                logger.debug(
                    f"Skipping non-parseable content type [{content_type}] for URL [{url}]"
                )
                return None

            # Determine parser
            parser = "lxml-xml" if "xml" in content_type else "html.parser"
            try:
                soup = BeautifulSoup(response.content, parser)
            except Exception as parse_error:
                logger.warning(
                    f"Failed to parse {url} with {parser}, trying html.parser: {parse_error}"
                )
                soup = BeautifulSoup(response.content, "html.parser")

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
                links=links,
            )

            logger.debug(f"Successfully processed response for URL [{url}]")
            return page_model
        except Exception as e:
            logger.debug(f"Error processing response: {e}", exc_info=True)
            return None

    async def _write_page_to_jsonl(self, page_model: PageModel) -> None:
        """
        Ensures JSONL file exists and optionally appends a PageModel record.
        The file becomes visible immediately after creation, even if empty.

        Args:
            page_model: PageModel to write

        Returns:
            None
        """

        jsonl_path = Path(CommonVariables.JSONL_FILE_PATH)

        # Ensure parent directory exists
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # Touch the file so it exists immediately
        jsonl_path.touch(exist_ok=True)

        # Append JSONL record
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(page_model), ensure_ascii=False) + "\n")
            f.flush()

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
            logger.debug(
                f"Queue is full. Current size: {queue_size}, Max limit: {CommonVariables.MAX_LIMIT}"
            )
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
        logger.debug(
            f"New queue size: {self.url_frontier.qsize()}/{CommonVariables.MAX_LIMIT}"
        )

        # Log if we couldn't add all URLs
        if urls_to_add < urls_len:
            logger.debug(
                f"Could not add {urls_len - urls_to_add} URLs due to queue capacity limit"
            )

    async def start_crawler(self) -> None:
        """
        This method is main method to start our crawler
        """
        iteration = 0

        while (
            not self.url_frontier.empty()
            and len(self.visited_urls) < CommonVariables.MAX_LIMIT
        ):
            iteration += 1
            logger.debug(f"=== ITERATION {iteration} START ===")
            logger.debug(f"Queue size at start: {self.url_frontier.qsize()}")
            logger.debug(f"Visited URLs count: {len(self.visited_urls)}")

            responses = await self._fetch_pages_for_urls_and_return_response()
            logger.debug(f"Fetched {len(responses)} responses")

            for resp_count, response in enumerate(responses, 1):
                if len(self.visited_urls) > CommonVariables.MAX_LIMIT:
                    break

                logger.debug(f"Parsing response {resp_count}/{len(responses)}")
                page_model = await self._parse_response_and_make_page_model(response)

                if page_model:
                    logger.debug("Writing the page model in JSONL")
                    await self._write_page_to_jsonl(page_model)

                    # Adding outgoing URLs from the above page model in url frontier
                    links = page_model.links
                    logger.debug(
                        f"Adding links found from above page [{links}] in queue"
                    )
                    await self._add_urls_in_queue(links)

            logger.debug(f"=== ITERATION {iteration} END ===\n")

        if self.url_frontier.empty():
            logger.info(
                f"Crawler stopped. Final queue size: {self.url_frontier.qsize()}"
            )
            logger.info(f"Total URLs visited: {len(self.visited_urls)}")

        if len(self.visited_urls) > CommonVariables.MAX_LIMIT:
            logger.info(
                f"Crawler stopped. Reached the Max Limit to crawl URLs {len(self.visited_urls)}/{CommonVariables.MAX_LIMIT}"
            )
