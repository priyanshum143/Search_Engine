"""
This file will contain some utility methods for string operations.
"""

import re
from urllib.parse import urlparse, urlunparse
import hashlib

from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.variables import CommonVariables
from src.search_engine.models.TokenType import TokenType, TOKEN_TYPE_WEIGHTS

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


def tokenize_content_into_set_of_words(content: str) -> set[str]:
    """
    This method will tokenize the content into words using regex

    Args:
        content: content of the webpage

    Returns:
        tokenize set of words
    """

    return {
        token.lower()
        for token in CommonVariables.TOKEN_PATTERN.findall(content)
    }


def score_token_based_on_token_type(
    text: str,
    token: str,
    token_type: TokenType = TokenType.CONTENT
) -> int:
    """
    This method will get the count of a word present in a text content

    Args:
        text: text from which, we need count
        token: token, whose freq we need
        token_type: token type, so that we can score

    Returns:
        score of the token
    """

    weight = TOKEN_TYPE_WEIGHTS[token_type]

    pattern = rf"\b{re.escape(token.lower())}\b"
    count = len(re.findall(pattern, text.lower()))

    return count * weight
