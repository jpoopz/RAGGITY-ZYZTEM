# citations/harvard.py
from __future__ import annotations

from pathlib import Path
import requests, json
from typing import List, Dict, Any, Optional

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc.source.json import CiteProcJSON

STYLE_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/harvard-cite-them-right.csl"
STYLE_PATH = Path("citations/styles/harvard-cite-them-right.csl")
LOCALE = "en-GB"


def ensure_style() -> Path:
    STYLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STYLE_PATH.exists():
        r = requests.get(STYLE_URL, timeout=30)
        r.raise_for_status()
        STYLE_PATH.write_text(r.text, encoding="utf-8")
    return STYLE_PATH


def crossref_to_csl(doi_meta: Dict[str, Any]) -> Dict[str, Any]:
    m = doi_meta.get("message", {})
    authors = [{"family": a.get("family"), "given": a.get("given")} for a in m.get("author", []) if "family" in a]
    issued = {"date-parts": [[m.get("issued", {}).get("date-parts", [[None]])[0][0] or m.get("published-print", {}).get("date-parts", [[None]])[0][0]]]}
    title = (m.get("title") or [""])[0]
    container = (m.get("container-title") or [""])[0]
    return {
        "id": m.get("DOI") or title,
        "type": "article-journal" if container else "article",
        "title": title,
        "author": authors,
        "issued": issued,
        "container-title": container,
        "volume": m.get("volume"),
        "issue": m.get("issue"),
        "page": m.get("page"),
        "DOI": m.get("DOI"),
        "URL": (m.get("URL") or None),
        "publisher": m.get("publisher"),
    }


def render_bibliography(csl_items: List[Dict[str, Any]]) -> List[str]:
    style_path = ensure_style()
    source = CiteProcJSON(csl_items)
    style = CitationStylesStyle(str(style_path), validate=False, locale=LOCALE)
    bib = CitationStylesBibliography(style, source, formatter.plain)
    for it in csl_items:
        bib.register(citation=None, key=it["id"])
    return [str(x) for x in bib.bibliography()]


def inline_cite(authors: List[str], year: Optional[int]) -> str:
    if not authors:
        return f"({year})" if year else "(n.d.)"
    last = authors[0].split()[-1]
    if len(authors) == 1:
        return f"({last}, {year})" if year else f"({last}, n.d.)"
    return f"({last} et al., {year})" if year else f"({last} et al., n.d.)"

