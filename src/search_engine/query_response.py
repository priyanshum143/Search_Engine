"""
This file contains the code to make a response according to the user's query
"""

from collections import defaultdict

from src.search_engine.utils.string_utils import tokenize_content_into_list_of_words
from src.search_engine.utils.variables import CommonVariables


class QueryParser:
    """
    This class contains the code to make a response according to the user's query
    """

    @staticmethod
    async def generate_response_for_query(
        query: str, inverted_index: dict, doc_store: dict
    ) -> list[dict]:
        """
        This method will prepare a response for the user's query

        Args:
            query: user's query
            inverted_index: inverted index
            doc_store: doc store

        Returns:
            list of documents to show to user in form of dict
        """
        # -----------------------------
        # 1) Accumulate scores per doc
        # -----------------------------

        doc_scores = defaultdict(int)
        doc_sets = []

        tokens = tokenize_content_into_list_of_words(query)
        for token in tokens:
            if token in CommonVariables.STOP_WORDS:
                continue

            token_result = inverted_index.get(token, {})
            if not token_result:
                # doc_sets.append(set())
                continue

            doc_sets.append(set(token_result.keys()))
            for doc_id, score in token_result.items():
                doc_scores[doc_id] += score

        # ------------------------------------
        # 2) Intersection of documents (AND)
        # ------------------------------------

        if doc_sets:
            common_set = set.intersection(*doc_sets)
        else:
            common_set = set()

        # Order common docs by total score descending for deterministic ranking
        common_docs_ordered = sorted(
            common_set, key=lambda d: doc_scores.get(d, 0), reverse=True
        )

        # ------------------------------------
        # 3) Backfill with top-scoring OR results
        # ------------------------------------
        resp_size = int(CommonVariables.RESPONSE_SIZE)

        # If we already have enough common docs, return top RESPONSE_SIZE of them
        if len(common_docs_ordered) >= resp_size:
            selected_doc_ids = common_docs_ordered[:resp_size]
        else:
            selected_doc_ids = list(common_docs_ordered)

            # how many more docs we need
            required_docs = resp_size - len(selected_doc_ids)

            # sort all docs by score descending
            sorted_docs_by_score = sorted(
                doc_scores.items(), key=lambda it: it[1], reverse=True
            )

            for doc_id, _score in sorted_docs_by_score:
                if doc_id in selected_doc_ids:
                    continue
                selected_doc_ids.append(doc_id)

                # Decrease the required count
                required_docs -= 1
                if required_docs == 0:
                    break

        # ------------------------------------
        # 4) Build result objects from doc_store
        # ------------------------------------

        results = []
        for doc_id in selected_doc_ids:
            meta = doc_store.get(doc_id)
            if not meta:
                continue

            results.append(
                {
                    "doc_id": doc_id,
                    "url": meta.get("url", ""),
                    "title": meta.get("title", "[COULD NOT FIND TITLE]"),
                }
            )

        return results
