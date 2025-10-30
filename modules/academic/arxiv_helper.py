"""
ArXiv helper utilities for downloading and processing papers.

Provides:
- PDF download from ArXiv
- ArXiv ID to DOI-like identifier conversion
- Integration with GROBID for reference extraction
"""

import os
import requests
from typing import Optional, Dict, Any
from pathlib import Path

from logger import get_logger

log = get_logger("arxiv_helper")


def arxiv_id_to_pseudo_doi(arxiv_id: str) -> str:
    """
    Convert ArXiv ID to pseudo-DOI for CSL compatibility.
    
    Args:
        arxiv_id: ArXiv ID (e.g., "2301.12345" or "2301.12345v2")
    
    Returns:
        Pseudo-DOI: "arxiv:2301.12345"
    """
    # Strip version suffix if present
    clean_id = arxiv_id.split('v')[0]
    return f"arxiv:{clean_id}"


def get_arxiv_pdf_url(arxiv_id: str) -> str:
    """
    Get PDF URL for ArXiv paper.
    
    Args:
        arxiv_id: ArXiv ID
    
    Returns:
        PDF download URL
    """
    clean_id = arxiv_id.split('v')[0]
    return f"https://arxiv.org/pdf/{clean_id}.pdf"


def download_arxiv_pdf(arxiv_id: str, output_dir: str = "data/arxiv") -> Optional[str]:
    """
    Download ArXiv PDF to local directory.
    
    Args:
        arxiv_id: ArXiv ID
        output_dir: Directory to save PDF
    
    Returns:
        Path to downloaded PDF or None if failed
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        clean_id = arxiv_id.split('v')[0]
        pdf_url = get_arxiv_pdf_url(arxiv_id)
        
        # Download PDF
        log.info(f"Downloading ArXiv PDF: {arxiv_id}")
        
        response = requests.get(pdf_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Save to file
        filename = f"arxiv_{clean_id.replace('/', '_')}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        log.info(f"Downloaded {filename} ({file_size_mb:.2f} MB)")
        
        return filepath
    
    except requests.exceptions.RequestException as e:
        log.error(f"Failed to download ArXiv PDF {arxiv_id}: {e}")
        return None
    except Exception as e:
        log.error(f"Error downloading ArXiv PDF {arxiv_id}: {e}")
        return None


def download_and_index(arxiv_id: str, output_dir: str = "data/arxiv") -> Dict[str, Any]:
    """
    Download ArXiv PDF, extract metadata and references via GROBID, and prepare for indexing.
    
    Args:
        arxiv_id: ArXiv ID
        output_dir: Directory to save PDF
    
    Returns:
        Dictionary with:
            - pdf_path: Local PDF path
            - metadata: Extracted metadata from GROBID
            - references: Extracted references
            - success: Boolean
    """
    result = {
        "arxiv_id": arxiv_id,
        "pdf_path": None,
        "metadata": None,
        "references": None,
        "success": False
    }
    
    # Download PDF
    pdf_path = download_arxiv_pdf(arxiv_id, output_dir)
    
    if not pdf_path:
        result["error"] = "Download failed"
        return result
    
    result["pdf_path"] = pdf_path
    
    # Extract metadata with GROBID
    try:
        from .grobid_pipe import parse_header, parse_references
        
        log.info(f"Extracting metadata from {arxiv_id} via GROBID...")
        
        metadata = parse_header(pdf_path)
        if metadata:
            result["metadata"] = metadata
            log.info(f"Extracted metadata: {metadata.get('title', 'N/A')[:50]}")
        
        references = parse_references(pdf_path)
        if references:
            result["references"] = references
            log.info(f"Extracted {len(references)} references")
        
        result["success"] = True
        
    except ImportError:
        log.warning("GROBID pipe not available, skipping metadata extraction")
        result["warning"] = "GROBID not available"
        result["success"] = True  # Download succeeded
    except Exception as e:
        log.error(f"GROBID processing failed: {e}")
        result["error"] = str(e)
        result["success"] = True  # Download succeeded but processing failed
    
    return result


def bulk_download_arxiv(arxiv_ids: List[str], output_dir: str = "data/arxiv") -> Dict[str, Any]:
    """
    Download multiple ArXiv PDFs in batch.
    
    Args:
        arxiv_ids: List of ArXiv IDs
        output_dir: Directory to save PDFs
    
    Returns:
        Summary dict with successes, failures, paths
    """
    from typing import List
    
    results = {
        "total": len(arxiv_ids),
        "successes": 0,
        "failures": 0,
        "paths": [],
        "errors": []
    }
    
    for arxiv_id in arxiv_ids:
        pdf_path = download_arxiv_pdf(arxiv_id, output_dir)
        
        if pdf_path:
            results["successes"] += 1
            results["paths"].append(pdf_path)
        else:
            results["failures"] += 1
            results["errors"].append(f"Failed: {arxiv_id}")
    
    log.info(f"Bulk download: {results['successes']}/{results['total']} succeeded")
    
    return results

