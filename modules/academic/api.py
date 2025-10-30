"""
Academic module API endpoints.

Provides search, citation, and export functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .providers import search_openalex, search_arxiv, search_semanticscholar, multi_search
from .citations.harvard import cite_from_dois, work_to_csl, render_bibliography
from logger import get_logger

log = get_logger("academic_api")

router = APIRouter(prefix="/academic", tags=["academic"])


class CiteRequest(BaseModel):
    """Request model for citation generation"""
    dois: List[str]
    polite_email: str = "user@example.com"


class ExportBibRequest(BaseModel):
    """Request model for BibTeX export"""
    dois: List[str]
    polite_email: str = "user@example.com"


@router.get("/search")
def search_papers(q: str, providers: str = "openalex,arxiv", polite_email: str = "user@example.com"):
    """
    Search for academic papers across multiple providers.
    
    Args:
        q: Search query
        providers: Comma-separated provider list (openalex, arxiv, semanticscholar)
        polite_email: Email for polite API access
    
    Returns:
        List of unified work objects
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    
    provider_list = [p.strip() for p in providers.split(",")]
    
    log.info(f"Academic search: '{q}' via {provider_list}")
    
    # Provider config (simplified for API)
    config = {
        "openalex": {"enabled": "openalex" in provider_list, "polite_email": polite_email},
        "arxiv": {"enabled": "arxiv" in provider_list},
        "semanticscholar": {"enabled": "semanticscholar" in provider_list, "api_key": None}
    }
    
    try:
        works = multi_search(q, provider_list, config)
        
        # Convert to dicts
        results = [work.to_dict() for work in works]
        
        log.info(f"Found {len(results)} papers")
        
        return {
            "query": q,
            "providers": provider_list,
            "count": len(results),
            "results": results
        }
    
    except Exception as e:
        log.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cite")
def generate_citations(request: CiteRequest):
    """
    Generate Harvard citations from DOIs.
    
    Returns:
        Dictionary with inline citations and full bibliography
    """
    if not request.dois:
        raise HTTPException(status_code=400, detail="At least one DOI required")
    
    try:
        result = cite_from_dois(request.dois, request.polite_email)
        
        log.info(f"Generated citations for {result['count']} DOIs")
        
        return result
    
    except Exception as e:
        log.error(f"Citation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resolve_pdf")
def resolve_pdf_url(doi: str, polite_email: str = "user@example.com"):
    """
    Resolve best open access PDF URL for a DOI.
    
    Args:
        doi: Document DOI
        polite_email: Email for Unpaywall polite pool
    
    Returns:
        Dictionary with pdf_url, landing_url, oa_status
    """
    if not doi:
        raise HTTPException(status_code=400, detail="DOI parameter required")
    
    try:
        from .providers import unpaywall_best
        
        result = unpaywall_best(doi, polite_email)
        
        if result:
            return {
                "doi": doi,
                "pdf_url": result.get("pdf_url"),
                "landing_url": result.get("landing_url"),
                "oa_status": result.get("oa_status"),
                "license": result.get("license"),
                "version": result.get("version")
            }
        else:
            # Construct publisher URL as fallback
            publisher_url = f"https://doi.org/{doi}"
            
            return {
                "doi": doi,
                "pdf_url": None,
                "landing_url": publisher_url,
                "oa_status": "closed",
                "message": "No open access version found"
            }
    
    except Exception as e:
        log.error(f"PDF resolution failed for {doi}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export_bib")
def export_bibtex(request: ExportBibRequest):
    """
    Export DOIs as BibTeX.
    
    Returns:
        BibTeX string
    """
    if not request.dois:
        raise HTTPException(status_code=400, detail="At least one DOI required")
    
    try:
        from .providers import fetch_crossref
        from pybtex.database import BibliographyData, Entry
        
        bib_db = BibliographyData()
        
        for doi in request.dois:
            metadata = fetch_crossref(doi, request.polite_email)
            
            if not metadata:
                continue
            
            # Generate citation key (simple: first_author_year)
            authors = metadata.get("author", [])
            year = None
            
            if authors:
                first_author = authors[0].get("family", "unknown")
            else:
                first_author = "unknown"
            
            published = metadata.get("published") or metadata.get("published-print")
            if published and "date-parts" in published:
                parts = published["date-parts"][0]
                if parts:
                    year = parts[0]
            
            key = f"{first_author.lower()}{year or 'nd'}"
            
            # Build BibTeX entry
            entry_type = metadata.get("type", "article")
            
            # Map common fields
            fields = {
                "title": metadata.get("title", ["Untitled"])[0],
                "doi": doi
            }
            
            if year:
                fields["year"] = str(year)
            
            if authors:
                author_names = []
                for author in authors[:10]:  # Limit to 10
                    family = author.get("family", "")
                    given = author.get("given", "")
                    if family:
                        author_names.append(f"{family}, {given}" if given else family)
                fields["author"] = " and ".join(author_names)
            
            container = metadata.get("container-title", [])
            if container:
                fields["journal"] = container[0]
            
            if "volume" in metadata:
                fields["volume"] = str(metadata["volume"])
            
            if "issue" in metadata:
                fields["number"] = str(metadata["issue"])
            
            if "page" in metadata:
                fields["pages"] = metadata["page"]
            
            # Create entry
            entry = Entry(entry_type, fields=[(k, v) for k, v in fields.items()])
            bib_db.entries[key] = entry
        
        # Convert to BibTeX string
        from io import StringIO
        output = StringIO()
        bib_db.to_file(output, bib_format='bibtex')
        bibtex_str = output.getvalue()
        
        log.info(f"Exported {len(bib_db.entries)} entries to BibTeX")
        
        return {
            "bibtex": bibtex_str,
            "count": len(bib_db.entries)
        }
    
    except ImportError as e:
        log.error(f"Missing dependency: {e}")
        raise HTTPException(status_code=500, detail=f"Missing dependency: {e}")
    except Exception as e:
        log.error(f"BibTeX export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

