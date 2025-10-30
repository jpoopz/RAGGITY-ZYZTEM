# modules/academic/providers.py
from __future__ import annotations

import time, requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

DEFAULT_EMAIL = "julian.poopat@gmail.com"
UA = {"User-Agent": "RAGGITY-Academic/1.0 (+github.com/jpoopz/RAGGITY-ZYZTEM)"}


@dataclass
class Work:
    title: str
    doi: Optional[str]
    year: Optional[int]
    authors: List[str]
    venue: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    abstract: Optional[str]
    source: str
    extra: Dict[str, Any] = field(default_factory=dict)


def _http_get(url: str, params=None, headers=None, timeout=20):
    h = dict(UA)
    if headers: 
        h.update(headers)
    for i in range(3):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception:
            if i == 2: 
                raise
            time.sleep(0.8 + i*0.6)


def search_openalex(q: str, polite_email: str = DEFAULT_EMAIL, per_page: int = 25) -> List[Work]:
    base = "https://api.openalex.org/works"
    params = {"search": q, "per_page": per_page, "mailto": polite_email}
    data = _http_get(base, params=params)
    out: List[Work] = []
    for item in data.get("results", []):
        doi = item.get("doi")
        authors = [a.get("author", {}).get("display_name") for a in item.get("authorships", [])]
        venue = (item.get("primary_location") or {}).get("source", {}).get("display_name")
        pdf = (item.get("open_access") or {}).get("oa_url")
        out.append(Work(
            title=item.get("title"),
            doi=doi[16:] if (doi and doi.startswith("https://doi.org/")) else doi,
            year=item.get("publication_year"),
            authors=[a for a in authors if a],
            venue=venue,
            url=item.get("primary_location", {}).get("landing_page_url"),
            pdf_url=pdf,
            abstract=(item.get("abstract") or item.get("abstract_inverted_index")),
            source="openalex",
            extra={"openalex_id": item.get("id")}
        ))
    return out


def fetch_crossref_by_doi(doi: str, polite_email: str = DEFAULT_EMAIL) -> Dict[str, Any]:
    url = f"https://api.crossref.org/works/{doi}"
    return _http_get(url, headers={"mailto": polite_email})


def search_arxiv(q: str, max_results: int = 25) -> List[Work]:
    # lightweight client without external dep
    import feedparser
    feed = feedparser.parse(f"http://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={max_results}")
    out: List[Work] = []
    for e in feed.entries:
        aid = e.id.split("/abs/")[-1]
        pdf = f"https://arxiv.org/pdf/{aid}.pdf"
        authors = [a.name for a in e.authors] if hasattr(e, "authors") else []
        year = None
        if hasattr(e, "published") and e.published:
            year = int(e.published[:4])
        out.append(Work(
            title=e.title.strip(),
            doi=None,  # map as pseudo-doi: arxiv:{id} if needed
            year=year,
            authors=authors,
            venue="arXiv",
            url=e.link,
            pdf_url=pdf,
            abstract=getattr(e, "summary", None),
            source="arxiv",
            extra={"arxiv_id": aid}
        ))
    return out


def unpaywall_best(doi: str, email: str = DEFAULT_EMAIL) -> Optional[Dict[str, Any]]:
    try:
        url = f"https://api.unpaywall.org/v2/{doi}"
        j = _http_get(url, params={"email": email})
        loc = j.get("best_oa_location") or {}
        return {
            "url_for_pdf": loc.get("url_for_pdf"),
            "url": loc.get("url"),
            "host_type": loc.get("host_type"),
            "license": loc.get("license"),
        }
    except Exception:
        return None


def unify(items: List[Work]) -> List[Dict[str, Any]]:
    # Return plain dicts for API/UI
    out = []
    for w in items:
        out.append({
            "title": w.title, "doi": w.doi, "year": w.year, "authors": w.authors,
            "venue": w.venue, "url": w.url, "pdf_url": w.pdf_url,
            "abstract": w.abstract, "source": w.source, "extra": w.extra
        })
    return out
