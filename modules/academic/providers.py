"""
Academic provider clients for paper search and metadata retrieval.

Implements thin clients for:
- OpenAlex (open scholarly metadata)
- Crossref (DOI metadata)
- ArXiv (preprints)
- Semantic Scholar (AI2 paper search)
- Unpaywall (open access URLs)

All clients include:
- Rate limiting and polite headers
- Robust error handling
- Unified data model
"""

import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from logger import get_logger

log = get_logger("academic")

# Rate limiting
_last_request = {}
_MIN_DELAY = 0.1  # 100ms between requests per provider


def _rate_limit(provider: str):
    """Simple rate limiter - wait if needed"""
    global _last_request
    
    last = _last_request.get(provider, 0)
    elapsed = time.time() - last
    
    if elapsed < _MIN_DELAY:
        time.sleep(_MIN_DELAY - elapsed)
    
    _last_request[provider] = time.time()


@dataclass
class Work:
    """Unified work/paper model"""
    title: str
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    abstract: Optional[str] = None
    source: str = "unknown"  # openalex, crossref, arxiv, s2, etc.
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    influential_citation_count: Optional[int] = None  # S2 metric
    openalex_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    oa_status: Optional[str] = None  # gold, green, hybrid, bronze, closed
    embedding: Optional[List[float]] = None  # SPECTER2 embedding from S2
    
    @property
    def is_highly_cited(self) -> bool:
        """Check if paper is highly cited (>= 100 citations)"""
        return self.citation_count is not None and self.citation_count >= 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "year": self.year,
            "authors": self.authors,
            "doi": self.doi,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "abstract": self.abstract,
            "source": self.source,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "openalex_id": self.openalex_id,
            "arxiv_id": self.arxiv_id,
            "oa_status": self.oa_status,
            "influential_citation_count": self.influential_citation_count,
            "is_highly_cited": self.is_highly_cited,
            "has_embedding": self.embedding is not None
        }


def search_openalex(query: str, polite_email: str, per_page: int = 25) -> List[Work]:
    """
    Search OpenAlex for scholarly works.
    
    Args:
        query: Search query
        polite_email: Polite pool email (gets faster rate limits)
        per_page: Results per page (max 25)
    
    Returns:
        List of Work objects
    """
    _rate_limit("openalex")
    
    try:
        url = "https://api.openalex.org/works"
        params = {
            "search": query,
            "per_page": min(per_page, 25),
            "mailto": polite_email
        }
        
        headers = {
            "User-Agent": f"RAGGITY/2.0 (mailto:{polite_email})"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        works = []
        for item in results:
            # Extract authors
            authors = []
            for authorship in item.get("authorships", [])[:5]:  # Limit to 5 authors
                author = authorship.get("author", {})
                name = author.get("display_name")
                if name:
                    authors.append(name)
            
            # Extract year
            pub_year = item.get("publication_year")
            
            # Get best OA location
            oa_location = item.get("primary_location") or item.get("best_oa_location") or {}
            pdf_url = oa_location.get("pdf_url")
            
            # OA status
            oa = item.get("open_access", {})
            oa_status = oa.get("oa_status")
            
            work = Work(
                title=item.get("title", "Untitled"),
                year=pub_year,
                authors=authors,
                doi=item.get("doi", "").replace("https://doi.org/", ""),
                url=item.get("id"),  # OpenAlex ID URL
                pdf_url=pdf_url,
                abstract=item.get("abstract"),
                source="openalex",
                venue=oa_location.get("source", {}).get("display_name"),
                citation_count=item.get("cited_by_count"),
                openalex_id=item.get("id"),
                oa_status=oa_status
            )
            works.append(work)
        
        log.info(f"OpenAlex: found {len(works)} works for '{query}'")
        return works
    
    except requests.exceptions.RequestException as e:
        log.error(f"OpenAlex request failed: {e}")
        return []
    except Exception as e:
        log.error(f"OpenAlex error: {e}")
        return []


def fetch_crossref(doi: str, polite_email: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata from Crossref by DOI.
    
    Args:
        doi: Document DOI
        polite_email: Polite pool email
    
    Returns:
        Raw Crossref metadata dict or None
    """
    _rate_limit("crossref")
    
    try:
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").strip()
        
        url = f"https://api.crossref.org/works/{doi}"
        params = {"mailto": polite_email}
        headers = {
            "User-Agent": f"RAGGITY/2.0 (mailto:{polite_email})"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        message = data.get("message", {})
        
        log.info(f"Crossref: fetched metadata for DOI {doi}")
        return message
    
    except requests.exceptions.RequestException as e:
        log.error(f"Crossref request failed for {doi}: {e}")
        return None
    except Exception as e:
        log.error(f"Crossref error for {doi}: {e}")
        return None


def search_arxiv(query: str, max_results: int = 25) -> List[Work]:
    """
    Search ArXiv for preprints.
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        List of Work objects
    """
    _rate_limit("arxiv")
    
    try:
        import arxiv
        
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        works = []
        for result in client.results(search):
            work = Work(
                title=result.title,
                year=result.published.year if result.published else None,
                authors=[author.name for author in result.authors],
                doi=result.doi,
                url=result.entry_id,
                pdf_url=result.pdf_url,
                abstract=result.summary,
                source="arxiv",
                venue="arXiv",
                arxiv_id=result.get_short_id()
            )
            works.append(work)
        
        log.info(f"ArXiv: found {len(works)} preprints for '{query}'")
        return works
    
    except ImportError:
        log.error("arxiv package not installed. Run: pip install arxiv")
        return []
    except Exception as e:
        log.error(f"ArXiv error: {e}")
        return []


def search_semanticscholar(query: str, api_key: Optional[str] = None, limit: int = 25, 
                          include_embeddings: bool = False) -> List[Work]:
    """
    Search Semantic Scholar for papers with optional citation metrics and embeddings.
    
    Args:
        query: Search query
        api_key: Optional S2 API key for higher rate limits and advanced features
        limit: Maximum results
        include_embeddings: Include SPECTER2 embeddings (requires API key)
    
    Returns:
        List of Work objects with citation metrics
    """
    _rate_limit("semanticscholar")
    
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
        # Base fields
        fields = [
            "title", "year", "authors", "doi", "url", "abstract", "venue",
            "citationCount", "influentialCitationCount", "openAccessPdf"
        ]
        
        # Add embeddings if requested and API key available
        if include_embeddings and api_key:
            fields.append("embedding")
        
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": ",".join(fields)
        }
        
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get("data", [])
        
        works = []
        for paper in papers:
            # Extract authors
            authors = [a.get("name", "") for a in paper.get("authors", [])[:5]]
            
            # Get OA PDF
            oa_pdf = paper.get("openAccessPdf") or {}
            pdf_url = oa_pdf.get("url")
            
            # Get citation metrics
            citation_count = paper.get("citationCount")
            influential_count = paper.get("influentialCitationCount")
            
            # Get embedding if available
            embedding = paper.get("embedding", {})
            if isinstance(embedding, dict):
                embedding = embedding.get("vector")
            
            work = Work(
                title=paper.get("title", "Untitled"),
                year=paper.get("year"),
                authors=authors,
                doi=paper.get("doi"),
                url=paper.get("url"),
                pdf_url=pdf_url,
                abstract=paper.get("abstract"),
                source="semanticscholar",
                venue=paper.get("venue"),
                citation_count=citation_count,
                influential_citation_count=influential_count,
                oa_status="gold" if pdf_url else "closed",
                embedding=embedding
            )
            works.append(work)
        
        # Sort by citation count (descending) as secondary sort
        works.sort(key=lambda w: (w.citation_count or 0), reverse=True)
        
        log.info(f"Semantic Scholar: found {len(works)} papers for '{query}'")
        return works
    
    except requests.exceptions.RequestException as e:
        log.error(f"Semantic Scholar request failed: {e}")
        return []
    except Exception as e:
        log.error(f"Semantic Scholar error: {e}")
        return []


def unpaywall_best(doi: str, email: str) -> Optional[Dict[str, Any]]:
    """
    Get best open access location for a DOI via Unpaywall.
    
    Args:
        doi: Document DOI
        email: Email for polite pool
    
    Returns:
        Best OA location dict or None
    """
    _rate_limit("unpaywall")
    
    try:
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").strip()
        
        url = f"https://api.unpaywall.org/v2/{doi}"
        params = {"email": email}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            log.info(f"Unpaywall: DOI {doi} not found")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Get best OA location
        best_oa = data.get("best_oa_location")
        
        if best_oa:
            log.info(f"Unpaywall: found OA location for {doi}")
            return {
                "pdf_url": best_oa.get("url_for_pdf"),
                "landing_url": best_oa.get("url_for_landing_page"),
                "license": best_oa.get("license"),
                "version": best_oa.get("version"),  # publishedVersion, acceptedVersion, submittedVersion
                "oa_status": data.get("oa_status")
            }
        
        return None
    
    except requests.exceptions.RequestException as e:
        log.error(f"Unpaywall request failed for {doi}: {e}")
        return None
    except Exception as e:
        log.error(f"Unpaywall error for {doi}: {e}")
        return None


def unify_work(item: Dict[str, Any], source: str) -> Work:
    """
    Convert provider-specific format to unified Work model.
    
    Args:
        item: Raw item from provider
        source: Provider name (openalex, crossref, arxiv, etc.)
    
    Returns:
        Work object
    """
    if source == "crossref":
        # Crossref format
        authors = []
        for author in item.get("author", [])[:5]:
            given = author.get("given", "")
            family = author.get("family", "")
            if family:
                authors.append(f"{given} {family}".strip())
        
        # Extract year
        published = item.get("published") or item.get("published-print") or item.get("created")
        year = None
        if published and "date-parts" in published:
            parts = published["date-parts"][0]
            if parts:
                year = parts[0]
        
        return Work(
            title=item.get("title", ["Untitled"])[0],
            year=year,
            authors=authors,
            doi=item.get("DOI"),
            url=item.get("URL"),
            abstract=item.get("abstract"),
            source="crossref",
            venue=item.get("container-title", [""])[0] if item.get("container-title") else None
        )
    
    elif source == "openalex":
        # Already handled in search_openalex
        pass
    
    elif source == "arxiv":
        # Already handled in search_arxiv
        pass
    
    elif source == "semanticscholar":
        # Already handled in search_semanticscholar
        pass
    
    # Fallback: generic extraction
    return Work(
        title=item.get("title", "Untitled"),
        year=item.get("year"),
        authors=item.get("authors", []),
        doi=item.get("doi"),
        url=item.get("url"),
        pdf_url=item.get("pdf_url"),
        abstract=item.get("abstract"),
        source=source,
        venue=item.get("venue")
    )


def multi_search(query: str, providers: List[str], config: Dict[str, Any]) -> List[Work]:
    """
    Search across multiple providers and deduplicate by DOI.
    
    Args:
        query: Search query
        providers: List of provider names to query
        config: Provider configuration dict
    
    Returns:
        Deduplicated list of Work objects
    """
    all_works = []
    seen_dois = set()
    
    for provider in providers:
        if provider == "openalex":
            cfg = config.get("openalex", {})
            if cfg.get("enabled"):
                works = search_openalex(query, polite_email=cfg.get("polite_email", ""))
                all_works.extend(works)
        
        elif provider == "arxiv":
            cfg = config.get("arxiv", {})
            if cfg.get("enabled"):
                works = search_arxiv(query)
                all_works.extend(works)
        
        elif provider == "semanticscholar":
            cfg = config.get("semanticscholar", {})
            if cfg.get("enabled"):
                api_key = cfg.get("api_key")
                works = search_semanticscholar(query, api_key=api_key)
                all_works.extend(works)
    
    # Deduplicate by DOI
    unique_works = []
    for work in all_works:
        if work.doi and work.doi in seen_dois:
            continue
        
        if work.doi:
            seen_dois.add(work.doi)
        
        unique_works.append(work)
    
    log.info(f"Multi-search: {len(unique_works)} unique works from {len(all_works)} total")
    return unique_works

