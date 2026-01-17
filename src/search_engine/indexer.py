"""
This file will contain the code to read the data collected by the crawler
and to make an inverted index
"""

from src.search_engine.utils.loggers import get_logger
from src.search_engine.utils.string_utils import (
    tokenize_content_into_set_of_words,
    score_token_based_on_token_type,
)
from src.search_engine.models.PageModel import PageModel
from src.search_engine.models.TokenType import TokenType

logger = get_logger(__name__)


class Indexer:
    """
    This class will contain the code to make an inverted indexer out of raw data collected by crawler
    """

    def __init__(self):
        pass


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

        # Tokenizing the content and getting frequency of each word
        content = model.content
        tokens = tokenize_content_into_set_of_words(content)
        for token in tokens:
            score = score_token_based_on_token_type(content, token, TokenType.CONTENT)
            # Here we need to write score in DB

        # Tokenizing the headings and getting frequency of each word
        headings = model.headings
        headings = " ".join(headings)
        tokens = tokenize_content_into_set_of_words(headings)
        for token in tokens:
            score = score_token_based_on_token_type(content, token, TokenType.HEADING)
            # Here we need to write score in DB

        # Tokenizing the title and getting frequency of each word
        title = model.title
        tokens = tokenize_content_into_set_of_words(title)
        for token in tokens:
            score = score_token_based_on_token_type(content, token, TokenType.TITLE)
            # Here we need to write score in DB

    async def iterate_crawled_data_and_make_inverted_index(self) -> None:
        """
        This method will iterate through all the PageModels and will make an inverted index

        Returns:
            None
        """

