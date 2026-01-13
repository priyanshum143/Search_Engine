"""
This class will contain some common gobal variables used across the search engine project.
"""

from pathlib import Path

class CommonVariables:
    """
    Initialize the variables module.
    """

    SEED_URLS = [
        "https://en.wikipedia.org/wiki/Main_Page",
    ]
    MAX_LIMIT = 5000

    ROOT_DIR = Path(__file__).parent.parent.parent
    JSONL_FILE_PATH = ROOT_DIR / "src" / "search_engine" / "models" / "PageModel.jsonl"
