"""
This file will contain the code to crawl the web pages
"""

import httpx
from bs4 import BeautifulSoup

class WebCrawler:
    """
    This class is responsible for crawling web pages.
    """
    
    def __init__(self, start_url):
        self.async_rest_client = httpx.AsyncClient()
        self.start_url = start_url
        self.visited_urls = set()
