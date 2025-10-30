"""
Harvard citation formatting using CSL (Citation Style Language).

Loads harvard-cite-them-right style and formats citations via citeproc-py.
Integrates with Crossref for metadata retrieval.
"""

from pathlib import Path
import json
import requests
from typing import List, Dict, Any, Optional

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc.source.json import CiteProcJSON

from logger import get_logger

log = get_logger("citations")

# CSL style repository
STYLE_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/harvard-cite-them-right.csl"
LOCALE = "en-GB"

# Default cache location
CACHE_DIR = Path(__file__).parent / "styles"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def ensure_style(style_name: str = "harvard-cite-them-right") -> Path:
    """
    Download CSL style file if not cached locally.
    
    Args:
        style_name: CSL style name
    
    Returns:
        Path to local CSL file
    """
    style_path = CACHE_DIR / f"{style_name}.csl"
    
    if not style_path.exists():
        try:
            log.info(f"Downloading CSL style: {style_name}")
            
            url = f"https://raw.githubusercontent.com/citation-style-language/styles/master/{style_name}.csl"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            style_path.write_text(response.text, encoding="utf-8")
            log.info(f"Cached CSL style to: {style_path}")
        
        except Exception as e:
            log.error(f"Failed to download CSL style {style_name}: {e}")
            raise
    
    return style_path


def work_to_csl(work: Dict[str, Any], item_id: str = None) -> Dict[str, Any]:
    """
    Convert Work metadata to CSL-JSON format.
    
    Args:
        work: Work dictionary (from providers or unified model)
        item_id: Citation key/ID (defaults to DOI or generated)
    
    Returns:
        CSL-JSON item
    """
    # Generate ID
    if not item_id:
        item_id = work.get("doi") or work.get("arxiv_id") or f"item-{hash(work.get('title', ''))}"
    
    # Parse authors
    authors = []
    for author_name in work.get("authors", []):
        # Simple name parsing (assumes "Given Family" format)
        parts = author_name.strip().split()
        if len(parts) >= 2:
            family = parts[-1]
            given = " ".join(parts[:-1])
        else:
            family = parts[0] if parts else ""
            given = ""
        
        authors.append({"family": family, "given": given})
    
    # Build CSL item
    csl_item = {
        "id": item_id,
        "type": "article-journal",  # Default type
        "title": work.get("title", "Untitled"),
        "author": authors
    }
    
    # Add optional fields
    if work.get("year"):
        csl_item["issued"] = {"date-parts": [[work["year"]]]}
    
    if work.get("doi"):
        csl_item["DOI"] = work["doi"]
    
    if work.get("url"):
        csl_item["URL"] = work["url"]
    
    if work.get("venue"):
        csl_item["container-title"] = work["venue"]
    
    if work.get("abstract"):
        csl_item["abstract"] = work["abstract"]
    
    # Determine type based on source
    source = work.get("source", "")
    if source == "arxiv" or work.get("arxiv_id"):
        csl_item["type"] = "article"
        csl_item["genre"] = "preprint"
    
    return csl_item


def crossref_to_csl(crossref_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Crossref metadata to CSL-JSON format.
    
    Args:
        crossref_data: Raw Crossref API response
    
    Returns:
        CSL-JSON item
    """
    item_id = crossref_data.get("DOI", f"crossref-{hash(str(crossref_data))}")
    
    # Crossref already uses CSL-like format, mostly pass-through
    csl_item = {
        "id": item_id,
        "type": crossref_data.get("type", "article"),
        "title": crossref_data.get("title", ["Untitled"])[0],
        "author": crossref_data.get("author", [])
    }
    
    # Add optional fields
    for key in ["DOI", "URL", "container-title", "volume", "issue", "page", "abstract"]:
        if key in crossref_data:
            csl_item[key] = crossref_data[key]
    
    # Handle dates
    if "published" in crossref_data:
        csl_item["issued"] = crossref_data["published"]
    elif "published-print" in crossref_data:
        csl_item["issued"] = crossref_data["published-print"]
    
    return csl_item


def render_bibliography(csl_items: List[Dict[str, Any]], 
                       style_path: Optional[Path] = None) -> List[str]:
    """
    Render bibliography from CSL-JSON items.
    
    Args:
        csl_items: List of CSL-JSON items
        style_path: Path to CSL file (defaults to Harvard)
    
    Returns:
        List of formatted bibliography entries
    """
    if not csl_items:
        return []
    
    try:
        # Ensure style is available
        if style_path is None:
            style_path = ensure_style("harvard-cite-them-right")
        
        # Create bibliography
        bib_source = CiteProcJSON(csl_items)
        style = CitationStylesStyle(str(style_path), validate=False, locale=LOCALE)
        bib = CitationStylesBibliography(style, bib_source, formatter.html)
        
        # Register all citations
        for item in csl_items:
            bib.register(Citation([CitationItem(item["id"])]))
        
        # Generate bibliography
        return [str(entry) for entry in bib.bibliography()]
    
    except Exception as e:
        log.error(f"Failed to render bibliography: {e}")
        return []


def cite_text(works: List[Dict[str, Any]], inline: bool = True) -> str:
    """
    Generate inline citation text.
    
    Args:
        works: List of work dictionaries
        inline: If True, return (Author Year), else full reference
    
    Returns:
        Citation string
    """
    if not works:
        return ""
    
    if inline:
        # Simple (Author Year) format
        citations = []
        for work in works:
            authors = work.get("authors", [])
            year = work.get("year", "n.d.")
            
            if authors:
                # First author surname
                first_author = authors[0].split()[-1] if authors[0] else "Unknown"
                
                if len(authors) == 1:
                    citations.append(f"{first_author}, {year}")
                elif len(authors) == 2:
                    second_author = authors[1].split()[-1]
                    citations.append(f"{first_author} and {second_author}, {year}")
                else:
                    citations.append(f"{first_author} et al., {year}")
            else:
                citations.append(f"Unknown, {year}")
        
        return "(" + "; ".join(citations) + ")"
    else:
        # Full bibliography entry
        csl_items = [work_to_csl(work, f"work-{i}") for i, work in enumerate(works)]
        bib = render_bibliography(csl_items)
        return "\n".join(bib)


def cite_from_dois(dois: List[str], polite_email: str) -> Dict[str, Any]:
    """
    Fetch metadata for DOIs and generate citations.
    
    Args:
        dois: List of DOIs
        polite_email: Email for polite pool
    
    Returns:
        Dictionary with inline citations and full bibliography
    """
    from .providers import fetch_crossref
    
    works = []
    csl_items = []
    
    for doi in dois:
        # Fetch metadata
        metadata = fetch_crossref(doi, polite_email)
        
        if metadata:
            # Convert to CSL
            csl_item = crossref_to_csl(metadata)
            csl_items.append(csl_item)
            
            # Also keep as work dict for inline citations
            work = {
                "title": metadata.get("title", [""])[0],
                "year": None,
                "authors": [],
                "doi": doi
            }
            
            # Extract year
            published = metadata.get("published") or metadata.get("published-print")
            if published and "date-parts" in published:
                parts = published["date-parts"][0]
                if parts:
                    work["year"] = parts[0]
            
            # Extract authors
            for author in metadata.get("author", [])[:3]:
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    work["authors"].append(f"{given} {family}".strip())
            
            works.append(work)
    
    # Generate citations
    inline = cite_text(works, inline=True)
    bibliography = render_bibliography(csl_items)
    
    return {
        "inline": inline,
        "bibliography": bibliography,
        "count": len(works)
    }


# Required for citeproc
from citeproc import Citation, CitationItem

