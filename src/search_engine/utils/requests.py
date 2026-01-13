"""
This file will contain the code to handle HTTP requests
"""

from typing import List
import asyncio
import httpx

from src.search_engine.utils.loggers import get_logger

logger = get_logger(__name__)


def prepare_async_requests(urls: List[str], async_rest_client: httpx.AsyncClient) -> List[httpx.Request]:
    """
    This method will prepare asynchronous HTTP GET requests for a list of URLs.

    Args:
        urls (List[str]): A list of URLs to prepare requests for.
        async_rest_client (httpx.AsyncClient): An instance of httpx.AsyncClient to build requests.

    Returns:
        List[httpx.Request]: A list of prepared HTTP GET requests.
    """

    requests = []
    for url in urls:
        logger.debug(f"Preparing request for URL: {url}")
        request = async_rest_client.build_request(
            "GET", 
            url,
            follow_redirects=True
        )
        requests.append(request)

    logger.debug(f"Prepared {len(requests)} requests: {requests}")
    return requests


async def hit_async_requests(requests: List[httpx.Request], async_rest_client: httpx.AsyncClient) -> List[httpx.Response]:
    """
    This method will send asynchronous HTTP requests and return their responses.

    Args:
        requests (List[httpx.Request]): A list of prepared HTTP requests.
        async_rest_client (httpx.AsyncClient): An instance of httpx.AsyncClient to send requests.

    Returns:
        List[httpx.Response]: A list of HTTP responses.
    """

    logger.debug(f"Hitting {len(requests)} requests asynchronously: {requests}")
    tasks = [async_rest_client.send(req) for req in requests]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return responses
