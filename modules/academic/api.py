"""
Academic module API endpoints.

Provides search, citation, and export functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .providers import search_openalex, search_arxiv, search_semanticscholar, multi_search
from .citations.harvard import cite_from_dois, work_to_csl, render_bibliography
from .arxiv_helper import download_and_index, get_arxiv_pdf_url
from .exporters import to_bibtex, to_ris, to_markdown_bibliography, to_csv
from logger import get_logger

log = get_logger("academic_api")

router = APIRouter(prefix="/academic", tags=["academic"])


class DownloadArxivRequest(BaseModel):
    """Request model for ArXiv download"""
    arxiv_id: str
    output_dir: str = "data/arxiv"


class ExportRequest(BaseModel):
    """Request model for exporting works"""
    works: List[Dict[str, Any]]
    format: str  # bibtex, ris, markdown, csv


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


@router.post("/download_arxiv")
def download_arxiv_paper(request: DownloadArxivRequest):
    """
    Download ArXiv PDF and extract metadata via GROBID.
    
    Returns:
        Dictionary with pdf_path, metadata, references, success
    """
    if not request.arxiv_id:
        raise HTTPException(status_code=400, detail="arxiv_id required")
    
    try:
        result = download_and_index(request.arxiv_id, request.output_dir)
        
        return result
    
    except Exception as e:
        log.error(f"ArXiv download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
def export_works(request: ExportRequest):
    """
    Export works to various formats.
    
    Supports: bibtex, ris, markdown, csv
    
    Returns:
        Dictionary with exported content and metadata
    """
    if not request.works:
        raise HTTPException(status_code=400, detail="At least one work required")
    
    format_lower = request.format.lower()
    
    try:
        if format_lower == "bibtex":
            content = to_bibtex(request.works)
            content_type = "text/plain"
        
        elif format_lower == "ris":
            content = to_ris(request.works)
            content_type = "text/plain"
        
        elif format_lower == "markdown":
            content = to_markdown_bibliography(request.works, style="harvard")
            content_type = "text/markdown"
        
        elif format_lower == "csv":
            content = to_csv(request.works)
            content_type = "text/csv"
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}. Use: bibtex, ris, markdown, csv"
            )
        
        return {
            "format": format_lower,
            "content": content,
            "content_type": content_type,
            "count": len(request.works)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export_bib")
def export_bibtex_legacy(request: ExportBibRequest):
    """
    Legacy endpoint: Export DOIs as BibTeX.
    
    Deprecated: Use /export with format="bibtex" instead.
    
    Returns:
        BibTeX string
    """
    if not request.dois:
        raise HTTPException(status_code=400, detail="At least one DOI required")
    
    try:
        from .providers import fetch_crossref
        
        # Fetch metadata for each DOI
        works = []
        for doi in request.dois:
            metadata = fetch_crossref(doi, request.polite_email)
            if metadata:
                # Convert to work dict
                authors = []
                for author in metadata.get("author", [])[:5]:
                    given = author.get("given", "")
                    family = author.get("family", "")
                    if family:
                        authors.append(f"{given} {family}".strip())
                
                year = None
                published = metadata.get("published") or metadata.get("published-print")
                if published and "date-parts" in published:
                    parts = published["date-parts"][0]
                    if parts:
                        year = parts[0]
                
                work = {
                    "title": metadata.get("title", ["Untitled"])[0],
                    "authors": authors,
                    "year": year,
                    "doi": doi,
                    "venue": metadata.get("container-title", [""])[0] if metadata.get("container-title") else None
                }
                works.append(work)
        
        # Export to BibTeX
        bibtex_content = to_bibtex(works)
        
        return {
            "bibtex": bibtex_content,
            "count": len(works)
        }
    
    except Exception as e:
        log.error(f"BibTeX export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

