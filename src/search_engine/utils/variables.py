"""
This class will contain some common gobal variables used across the search engine project.
"""

import re
from pathlib import Path


class CommonVariables:
    """
    Initialize the variables module.
    """

    SEED_URLS = [
        "https://en.wikipedia.org/wiki/Main_Page",
    ]
    MAX_LIMIT = 10000
    BATCH_SIZE = 20
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    ACCEPTED_DOMAINS = ["wikipedia.org", "en.wikipedia.org"]
    SKIP_EXTENSIONS = [
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".pdf",
    ]

    STOP_WORDS = [
        "a", "an", "the", "and", "or", "but",
        "is", "am", "are", "was", "were",
        "have", "has", "had",
        "of", "to", "in", "on", "for", "at", "by"
    ]
    TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9]+\b")

    ROOT_DIR = Path(__file__).parent.parent.parent.parent
    JSONL_FILE_PATH = ROOT_DIR / "src" / "search_engine" / "data" / "PageModel.jsonl"
