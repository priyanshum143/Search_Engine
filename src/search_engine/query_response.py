"""
This file contains the code to make a response according to the user's query
"""

from collections import defaultdict
import heapq

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

        resp_size = int(CommonVariables.RESPONSE_SIZE)
        tokens = tokenize_content_into_list_of_words(query)

        posting_sets = []  # list of sets of doc_ids for each token found
        token_postings = {}  # token -> posting dict (doc_id -> score)
        posting_sizes = []  # list of (size, token) for sorting

        for token in tokens:
            if token in CommonVariables.STOP_WORDS:
                continue

            posting = inverted_index.get(token)
            if not posting:
                continue

            token_postings[token] = posting
            posting_sets.append(set(posting.keys()))
            posting_sizes.append((len(posting), token))

        # If no token matched at all
        if not posting_sets:
            return []

        # Intersect smallest-first
        posting_sizes.sort(key=lambda x: x[0])
        sorted_tokens_by_size = [tok for _size, tok in posting_sizes]

        # Build intersection iteratively (start from smallest)
        common_set = None
        for tok in sorted_tokens_by_size:
            s = set(token_postings[tok].keys())
            if common_set is None:
                common_set = s
            else:
                common_set &= s
            if not common_set:
                break

        # If we have AND hits, compute scores only for those docs.
        results = []
        selected_doc_ids = []
        selected_doc_ids_set = set()

        if common_set:
            # compute score only for docs in common_set
            doc_scores = defaultdict(int)
            for tok, posting in token_postings.items():
                # posting is dict doc_id->score
                for doc_id in common_set:
                    # use .get to avoid KeyError; most terms may not have all docs in common_set but that's OK
                    s = posting.get(doc_id)
                    if s:
                        doc_scores[doc_id] += s

            # rank AND results
            common_docs_ordered = sorted(
                common_set, key=lambda d: doc_scores.get(d, 0), reverse=True
            )
            for doc_id in common_docs_ordered:
                if len(selected_doc_ids) >= resp_size:
                    break
                if doc_id in selected_doc_ids_set:
                    continue
                selected_doc_ids.append(doc_id)
                selected_doc_ids_set.add(doc_id)

            # if filled, return
            if len(selected_doc_ids) >= resp_size:
                pass  # go to build results below
            else:
                # Need OR backfill: compute doc_scores for remaining documents but limit work
                # We'll build doc_scores only for top-K postings per term to approximate top-scoring OR docs
                remaining_needed = resp_size - len(selected_doc_ids)
                # accumulate scores (but only from top K postings per term)
                for tok, posting in token_postings.items():
                    # posting: dict doc->score; get top K doc-score pairs
                    if len(posting) <= CommonVariables.TOP_K_PER_TERM:
                        candidates = posting.items()
                    else:
                        # faster to use heapq.nlargest on dict.items()
                        candidates = heapq.nlargest(
                            CommonVariables.TOP_K_PER_TERM,
                            posting.items(),
                            key=lambda it: it[1],
                        )
                    for doc_id, s in candidates:
                        if doc_id in selected_doc_ids_set:
                            continue

                        # add to a global doc_scores (only for OR candidate pool)
                        # we can use a dict for accumulation
                        # to avoid recomputing, reuse the earlier doc_scores for AND candidates
                        # ensure doc_scores exists:
                        try:
                            doc_scores  # if defined earlier
                        except NameError:
                            doc_scores = defaultdict(int)
                        doc_scores[doc_id] += s

                    # pick top (remaining_needed) docs from doc_scores
                    if doc_scores:
                        top_or = heapq.nlargest(
                            remaining_needed, doc_scores.items(), key=lambda it: it[1]
                        )
                        for doc_id, _score in top_or:
                            if doc_id in selected_doc_ids_set:
                                continue
                            selected_doc_ids.append(doc_id)
                            selected_doc_ids_set.add(doc_id)
        else:
            # No AND hits → do OR-only approach but limit per-term scanning
            doc_scores = defaultdict(int)
            for tok, posting in token_postings.items():
                if len(posting) <= CommonVariables.TOP_K_PER_TERM:
                    candidates = posting.items()
                else:
                    candidates = heapq.nlargest(
                        CommonVariables.TOP_K_PER_TERM,
                        posting.items(),
                        key=lambda it: it[1],
                    )
                for doc_id, s in candidates:
                    doc_scores[doc_id] += s

            # pick top resp_size docs
            top_docs = heapq.nlargest(
                resp_size, doc_scores.items(), key=lambda it: it[1]
            )
            for doc_id, _score in top_docs:
                selected_doc_ids.append(doc_id)
                selected_doc_ids_set.add(doc_id)

        # Build result objects from doc_store
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
