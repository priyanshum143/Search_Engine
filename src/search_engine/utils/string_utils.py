"""
This file will contain some utility methods for string operations.
"""

from urllib.parse import urlparse, urlunparse, urljoin
from typing import List
import hashlib

from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.variables import CommonVariables

logger = get_logger(__name__)


def normalize_url(url: str, source_url: str = None) -> str:
    """
    Normalize a URL by removing trailing slashes and "#" and converting to lowercase.

    Args:
        url (str): The URL to normalize.
        source_url (str): Source URL
    Returns:
        str: The normalized URL.
    """

    logger.debug(f"Normalizing URL: {url}")

    # Parse the URL into components
    url = url.strip()
    parsed = urlparse(url.strip())

    # Joining the relative link with its source
    if not parsed.scheme:
        if not source_url:
            return ""
        url = urljoin(source_url, url)
        parsed = urlparse(url)

    # Normalize scheme and netloc to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Normalize path: remove trailing slash (except for root "/")
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

    # Keep query parameters as-is
    query = parsed.query

    # Remove fragment (the "#" part)
    fragment = ""

    # Reconstruct the URL without fragment
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
    logger.debug(f"Normalized URL: {normalized}")

    return normalized


def generate_content_hash(content: str) -> str:
    """
    Generate an SHA-256 hash of the content.

    Args:
        content (str): The content to hash.

    Returns:
        str: The hexadecimal hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def tokenize_content_into_list_of_words(content: str) -> List[str]:
    """
    This method will tokenize the content into words using regex

    Args:
        content: content of the webpage

    Returns:
        tokenize set of words
    """

    return [token.lower() for token in CommonVariables.TOKEN_PATTERN.findall(content)]
