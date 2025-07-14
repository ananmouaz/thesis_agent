#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bibtex_generator.py
~~~~~~~~~~~~~~~~~~~

Generate a BibTeX entry from either a DOI **or** an arXiv ID.
If the identifier contains a slash ("/") we treat it as a DOI and query
CrossRef; otherwise we fall back to the arXiv API.

----------------------------------------------------------------------
Quick CLI usage
----------------------------------------------------------------------

$ python bibtex_generator.py 10.1038/nature12373
@article{10.1038/nature12373,
  title   = { ... },
  author  = { ... },
  journal = {Nature},
  year    = {2013},
  doi     = {10.1038/nature12373}
}

$ python bibtex_generator.py 1706.03762      # arXiv ID
@article{1706.03762,
  title          = {Attention Is All You Need},
  author         = {Vaswani, Ashish and ...},
  year           = {2017},
  eprint         = {1706.03762},
  archivePrefix  = {arXiv}
}

----------------------------------------------------------------------
Embedding in code
----------------------------------------------------------------------

>>> from bibtex_generator import generate_bibtex
>>> print(generate_bibtex("10.48550/arXiv.1706.03762"))

----------------------------------------------------------------------
Dependencies
----------------------------------------------------------------------
- requests  (≥ 2.32)  — already in *requirements.txt*
- Internet access to:
    • https://api.crossref.org   (DOI look-ups)
    • https://export.arxiv.org   (arXiv IDs)
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from typing import Final

import requests

_CROSSREF_URL: Final = "https://api.crossref.org/works/"
_ARXIV_URL:   Final = "https://export.arxiv.org/api/query?id_list="


# ---- DOI branch --------------------------------------------------- #
def _from_crossref(doi: str) -> str:
    data = requests.get(f"{_CROSSREF_URL}{doi}", timeout=10).json()["message"]
    authors = " and ".join(
        f"{a['family']}, {a['given']}" for a in data["author"])
    year = data["issued"]["date-parts"][0][0]

    return (
        f"@article{{{data['DOI']}}},\n"
        f"  title   = {{ {data['title'][0]} }},\n"
        f"  author  = {{ {authors} }},\n"
        f"  journal = {{ {data.get('container-title', [''])[0]} }},\n"
        f"  year    = {{ {year} }},\n"
        f"  doi     = {{ {data['DOI']} }}\n"
        f"}}"
    )


# ---- arXiv branch -------------------------------------------------- #
_ARXIV_T = re.compile(r"<title>(.*?)</title>", re.S)
_ARXIV_N = re.compile(r"<name>(.*?)</name>")
_ARXIV_P = re.compile(r"<published>(.*?)</published>")


def _from_arxiv(arxiv_id: str) -> str:
    feed = requests.get(f"{_ARXIV_URL}{arxiv_id}", timeout=10).text
    title = _ARXIV_T.search(feed).group(1).split("\n")[0].strip()
    authors = _ARXIV_N.findall(feed)
    year = datetime.strptime(_ARXIV_P.search(
        feed).group(1)[:10], "%Y-%m-%d").year

    return (
        f"@article{{{arxiv_id}}},\n"
        f"  title          = {{ {title} }},\n"
        f"  author         = {{ {' and '.join(authors)} }},\n"
        f"  year           = {{ {year} }},\n"
        f"  eprint         = {{ {arxiv_id} }},\n"
        f"  archivePrefix  = {{ arXiv }}\n"
        f"}}"
    )


# ---- public façade ------------------------------------------------- #
def generate_bibtex(identifier: str) -> str:
    """
    Return a BibTeX entry for *identifier* (DOI or arXiv ID).

    Parameters
    ----------
    identifier : str
        - DOI  → looks like “10.1038/…” (contains a slash).
        - arXiv ID → numeric or “hep-th/0307071” (no slash for modern IDs).

    Raises
    ------
    requests.HTTPError
        On non-2xx responses from CrossRef or arXiv.
    """
    return _from_crossref(identifier) if "/" in identifier else _from_arxiv(identifier)


# ---- CLI interface ------------------------------------------------- #
def _cli() -> None:
    if len(sys.argv) != 2:
        print("Usage: python bibtex_generator.py <DOI | arXiv ID>", file=sys.stderr)
        sys.exit(1)
    print(generate_bibtex(sys.argv[1]))


if __name__ == "__main__":
    _cli()
