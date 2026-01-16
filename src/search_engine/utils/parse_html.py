"""
This file will contain the code to extaract useful information from the crawled web pages
"""

from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.variables import CommonVariables

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
    links = []

    for link in link_tags:
        href = link.get("href")

        if not href or not href.startswith("https://"):
            continue

        # Skip if URL ends with non-HTML file extensions
        if any(href.lower().endswith(ext) for ext in CommonVariables.SKIP_EXTENSIONS):
            continue

        try:
            parsed_url = urlparse(href)
            domain = parsed_url.netloc

            if any(
                domain.endswith(accepted_domain)
                for accepted_domain in CommonVariables.ACCEPTED_DOMAINS
            ):
                links.append(href)
            else:
                logger.debug(f"Skipping URL from non-accepted domain: {domain}")

        except Exception as e:
            logger.debug(f"Error parsing URL {href}: {e}")
            continue

    logger.debug(f"Found {len(links)} valid links from accepted domains")
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
    headings = [
        tag.get_text(strip=True) for tag in heading_tags if tag.get_text(strip=True)
    ]
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
