"""
This file will contain the code to read the data collected by the crawler
and to make an inverted index
"""

import asyncio
from typing import Any
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.search_engine.utils.variables import CommonVariables
from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.string_utils import (
    tokenize_content_into_list_of_words,
)
from src.search_engine.models.PageModel import PageModel
from src.search_engine.models.TokenType import TokenType, TOKEN_TYPE_WEIGHTS

logger = get_logger(__name__)


class Indexer:
    """
    This class will contain the code to make an inverted indexer out of raw data collected by crawler
    """

    def __init__(self):
        """
        Constructor for our indexer
        """

        self.inverted_index: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.doc_store: dict[str, dict[str, Any]] = defaultdict(dict)

    async def _create_inverted_index_for_page_model(self, model: PageModel) -> None:
        """
        This method will create an inverted index for the words present in the given page model

        Args:
            model: PageModel object for the page

        Returns:
            None
        """

        doc_id = model.doc_id
        logger.debug(
            f"Making an inverted index for tokens present in page with id {doc_id}"
        )

        # Accumulate total weighted score per term for this document
        term_scores = defaultdict(int)

        # Tokenizing the content and getting frequency of each word
        content = model.content or ""
        tokens = tokenize_content_into_list_of_words(content)
        term_freq = Counter(tokens)
        weightage = TOKEN_TYPE_WEIGHTS[TokenType.CONTENT]
        for term, freq in term_freq.items():
            if term in CommonVariables.STOP_WORDS:
                continue
            term_scores[term] += freq * weightage

        # Tokenizing the headings and getting frequency of each word
        headings = model.headings or []
        headings = " ".join(headings)
        tokens = tokenize_content_into_list_of_words(headings)
        term_freq = Counter(tokens)
        weightage = TOKEN_TYPE_WEIGHTS[TokenType.HEADING]
        for term, freq in term_freq.items():
            if term in CommonVariables.STOP_WORDS:
                continue
            term_scores[term] += freq * weightage

        # Tokenizing the title and getting frequency of each word
        title = model.title or ""
        tokens = tokenize_content_into_list_of_words(title)
        term_freq = Counter(tokens)
        weightage = TOKEN_TYPE_WEIGHTS[TokenType.TITLE]
        for term, freq in term_freq.items():
            if term in CommonVariables.STOP_WORDS:
                continue
            term_scores[term] += freq * weightage

        # Merge into global inverted index
        for term, score in term_scores.items():
            self.inverted_index[term][doc_id] += score

        logger.debug(f"Indexed doc_id={doc_id}")

    async def _write_inverted_index_in_json(self) -> None:
        """
        This method will write the complete inverted index

        Returns:
            None
        """

        json_path = Path(CommonVariables.INVERTED_INDEX_FILE_PATH)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.touch(exist_ok=True)

        inverted_index_dict = {
            term: dict(postings) for term, postings in self.inverted_index.items()
        }
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(inverted_index_dict, f, ensure_ascii=False, indent=4)
            f.flush()

    async def _create_doc_store_for_page_model(self, model: PageModel) -> None:
        """
        This method will create a doc store for the given page model
        which will provide the necessary details from page model, final_url, title, some content

        Args:
            model:
                Page model

        Returns:
            None
        """

        self.doc_store[model.doc_id] = {
            "url": model.final_url,
            "title": model.title,
            "content": model.content,
        }

    async def _write_doc_store_in_json(self) -> None:
        """
        This method will write the doc store in a json file

        Returns:
            None
        """

        json_path = Path(CommonVariables.DOC_STORE_FILE_PATH)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.touch(exist_ok=True)

        doc_store = {term: dict(postings) for term, postings in self.doc_store.items()}
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(doc_store, f, ensure_ascii=False, indent=4)
            f.flush()

    async def start_indexing(
        self,
        page_model_queue: asyncio.Queue,
        crawl_done: asyncio.Event,
    ) -> None:
        """
        This method will check if crawler is working or not, and if working
        will get the page model from queue and index the models

        Args:
            page_model_queue: page model queue
            crawl_done: crawler event

        Returns:
            None
        """

        while True:
            if crawl_done.is_set() and page_model_queue.empty():
                break

            try:
                model = await asyncio.wait_for(page_model_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            try:
                await self._create_inverted_index_for_page_model(model)
                await self._create_doc_store_for_page_model(model)
            finally:
                await self._write_inverted_index_in_json()
                await self._write_doc_store_in_json()
                page_model_queue.task_done()
