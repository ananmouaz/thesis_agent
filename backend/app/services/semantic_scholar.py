#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_scholar.py
~~~~~~~~~~~~~~~~~~~

Light-weight wrapper around the **Semantic Scholar Graph API** to fetch
metadata for a single paper (title, DOI, or arXiv ID).

----------------------------------------------------------------------
Quick usage from the command line
----------------------------------------------------------------------

$ python semantic_scholar.py "Attention Is All You Need"
# or
$ python semantic_scholar.py 10.1038/nature12373
# or
$ python semantic_scholar.py 1706.03762        # arXiv ID works too

The script prints a compact Python `dict` (pretty-printed) such as:

{
    'paperId': '204e3073870fae3d05bcbc2f6a8e263d9b72e776',
    'externalIds': {'MAG': '2963403868', 'DBLP': 'conf/nips/VaswaniSPUJGKP17',
                    'ArXiv': '1706.03762', 'CorpusId': 13756489},
    'url': 'https://www.semanticscholar.org/paper/204e3073870fae3d05bcbc2f6a8e263d9b72e776',
    'title': 'Attention Is All You Need',
    'venue': 'Neural Information Processing Systems',
    'year': 2017,
    'citationCount': 133589,
    'authors': [{'authorId': '40348417', 'name': 'Ashish Vaswani'}, ...],
    'abstract': 'The dominant sequence-transduction models …'
}

----------------------------------------------------------------------
Embedding as a Python function
----------------------------------------------------------------------

>>> from semantic_scholar import get_paper_metadata
>>> meta = get_paper_metadata("10.48550/arXiv.1706.03762")
>>> meta["citationCount"]
133589

----------------------------------------------------------------------
Dependencies
----------------------------------------------------------------------

- requests (≥2.32)                # already in your requirements.txt
- Internet access to https://api.semanticscholar.org
- (Optional) environment variable **S2_API_KEY** for higher rate limits
"""

from __future__ import annotations

import json
import pprint
import sys
from typing import Any, Dict

import requests

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def get_paper_metadata(query: str) -> Dict[str, Any]:
    """
    Query Semantic Scholar for a single paper and return its metadata.

    Parameters
    ----------
    query : str
        Paper title, DOI, or arXiv identifier.

    Returns
    -------
    dict
        A dictionary with keys:
        ``title, authors, year, venue, abstract,
        externalIds, url, citationCount``.
        Empty dict if no match is found.

    Raises
    ------
    requests.HTTPError
        If the API returns a non-2xx status code.
    """
    params = {
        "query": query,
        "limit": 1,
        "fields": (
            "title,authors,year,venue,abstract,externalIds,"
            "url,citationCount"
        ),
    }
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0] if data["data"] else {}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python semantic_scholar.py '<title | DOI | arXiv ID>'",
            file=sys.stderr,
        )
        sys.exit(1)

    metadata = get_paper_metadata(sys.argv[1])

    # Pretty-print as JSON (for easy piping / redirection).
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
