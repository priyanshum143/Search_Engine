# Search-Engine 🔍

A simple **search engine built in Python** to understand how search engines work internally.

At a high level, a **search engine** does three things:
1) **Crawls** pages (collects content)
2) **Indexes** pages (builds data structures for fast lookup)
3) **Searches** (answers user queries with ranked results)


---

## What’s inside

- **Crawler:** Fetches web pages and extracts outgoing links to discover more pages.
- **Indexer:** Converts crawled content into an **inverted index** for fast search.
- **Query Engine:** Tokenizes the query, finds matching documents, ranks them, and returns results.
- **Web UI:** A minimal Flask UI to enter queries and view results.

---

## Project Structure
```
Search-Engine/
├── .github/workflows/black.yml
├── src/
│   └── search_engine/
│       ├── models/
│       │   ├── PageModel.py
│       │   └── TokenType.py
│       ├── utils/
│       │   ├── loggers.py
│       │   ├── parse_html.py
│       │   ├── requests.py
│       │   ├── string_utils.py
│       │   └── variables.py
│       ├── crawler.py
│       ├── indexer.py
│       └── query_response.py
├── templates/
│   └── index.html
├── app.py
├── pyproject.toml
├── uv.lock
└── README.md
```
You do not need to update any of the project structure to start the search engine.

## Dependencies & Package Management (uv)

This project uses **uv** as the Python package manager.

All dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

### Install dependencies

From the project root, run:

```bash
uv sync
```

## Running the Search Engine

After installing dependencies, start the backend server using:

```bash
uv run python app.py
```

## The application will be available at

```bash
http://127.0.0.1:5000
```

## How the System Works

1. A background asyncio event loop is created
2. The crawler starts discovering web pages
3. The indexer builds an inverted index
4. Flask serves HTTP requests
5. Queries are executed against the in-memory index

Crawling, indexing, and searching run concurrently.

## Configuration (CommonVariables)
Configuration (CommonVariables)
```bash
src/search_engine/utils/variables.py
```

## CI / Code Quality

GitHub Actions enforces code formatting using Black.

Workflow location:
```bash
.github/workflows/black.yml
```

To run formatting locally:
```bash
uv run black .
```
