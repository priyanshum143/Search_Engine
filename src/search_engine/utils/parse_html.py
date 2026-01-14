"""
This file will contain the code to extaract useful information from the crawled web pages
"""

from typing import List
from bs4 import BeautifulSoup

from src.search_engine.utils.loggers import get_logger

logger = get_logger(__name__)


def extract_outgoing_links_from_soup(soup: BeautifulSoup) -> List[str]:
    """
    This method will extract all the outgoing links from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        List[str]: A list of outgoing links found in the HTML content.
    """

    link_tags = soup.find_all("a", href=True)
    links = [
        link.get("href")
        for link in link_tags
        if link.get("href") and link.get("href").startswith("https://")
    ]
    logger.debug(f"Found {len(links)} links in the HTML content")
    return links


def extract_headings_from_soup(soup: BeautifulSoup) -> List[str]:
    """
    This method will extract all the headings (h1-h6) from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        List[str]: A list of all heading texts found in the HTML content.
    """

    heading_tags = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    headings = [tag.get_text(strip=True) for tag in heading_tags if tag.get_text(strip=True)]
    logger.debug(f"Found {len(headings)} headings")
    return headings


def extract_title_from_soup(soup: BeautifulSoup) -> str:
    """
    This method will extract the page title from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        str: The page title, or an empty string if no title is found.
    """

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    logger.debug(f"Found title: {title}")
    return title


def extract_content_from_soup(soup: BeautifulSoup) -> str:
    """
    This method will extract the main text content from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

    Returns:
        str: The extracted text content from the page.
    """

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()

    # Get text content
    text = soup.get_text(separator=" ", strip=True)

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)
    logger.debug(f"Extracted content length: {len(text)} characters")
    return text
