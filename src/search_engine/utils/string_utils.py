"""
This file will contain some utility methods for string operations.
"""

from urllib.parse import urlparse, urlunparse

from src.search_engine.utils.loggers import get_logger

logger = get_logger(__name__)


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing trailing slashes and "#" and converting to lowercase.

    Args:
        url (str): The URL to normalize.
    Returns:
        str: The normalized URL.
    """

    logger.debug(f"Normalizing URL: {url}")

    # Parse the URL into components
    parsed = urlparse(url.strip())
    
    # Normalize scheme and netloc to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Normalize path: remove trailing slash (except for root "/")
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    
    # Keep query parameters as-is
    query = parsed.query
    
    # Remove fragment (the "#" part)
    fragment = ''
    
    # Reconstruct the URL without fragment
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
    logger.debug(f"Normalized URL: {normalized}")
    
    return normalized
