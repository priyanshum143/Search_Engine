"""
This file will contain the Page Model, which will used to store a page's data in proper format while crawling.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class PageModel:
    doc_id: str
    url: str
    final_url: str
    http_status: int
    title: str
    headings: List[str]
    content: str
    links: List[str]
