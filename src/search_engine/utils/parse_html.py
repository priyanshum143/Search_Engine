"""
This file will contain the code to extaract useful information from the crawled web pages
"""

from typing import List
from bs4 import BeautifulSoup

from src.search_engine.utils.loggers import get_logger

logger = get_logger(__name__)


def extract_outgoing_links(soup: BeautifulSoup) -> List[str]:
    """
    This method will extract all the outgoing links from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        List[str]: A list of outgoing links found in the HTML content.
    """

    link_tags = soup.find_all('a', href=True)
    links = [link.get('href') for link in link_tags if link.get('href')]
    logger.debug(f"Found {len(links)} links in the HTML content")
    return links
