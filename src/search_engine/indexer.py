"""
This file will contain the code to read the data collected by the crawler
and to make an inverted index
"""

import json
from collections import Counter, defaultdict

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
        self.inverted_index: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    async def _create_inverted_index_for_page_model(self, model: PageModel) -> None:
        """
        This method will create an inverted index for the words present in the given page model

        Args:
            model: PageModel object for the page

        Returns:
            None
        """

        doc_id = model.doc_id
        logger.debug(f"Making an inverted index for tokens present in page with id {doc_id}")

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

    async def iterate_crawled_data_and_make_inverted_index(self) -> None:
        """
        This method will iterate through all the PageModels and will make an inverted index

        Returns:
            None
        """

        indexed = 0
        skipped = 0

        with open(CommonVariables.JSONL_FILE_PATH, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                logger.debug(f"Iterating the line number {line_no} to make an inverted index")

                # Fetching the line
                line = line.strip()

                # Trying to load line as JSON
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.debug(f"Skipping bad JSON at line {line_no}: {e}")
                    skipped += 1
                    continue

                # Trying to convert the JSON as PageModel
                try:
                    model = PageModel(**record)
                except TypeError as e:
                    logger.debug(f"Skipping line {line_no}: not matching PageModel fields: {e}")
                    skipped += 1
                    continue

                await self._create_inverted_index_for_page_model(model)
                indexed += 1

                logger.debug(f"Successfully made an inverted index out of line number {line_no}")

            logger.debug(f"Indexing complete, Indexed {indexed} PageModels, Skipped {skipped}")
