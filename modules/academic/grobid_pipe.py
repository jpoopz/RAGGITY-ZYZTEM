"""
GROBID integration for PDF metadata and reference extraction.

Requires GROBID server running on localhost:8070.
Start with: scripts/dev/run_grobid.bat
"""

import os
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path

from logger import get_logger

log = get_logger("grobid")


class GrobidClient:
    """
    Client for GROBID server.
    
    GROBID extracts structured metadata and references from PDFs.
    """
    
    def __init__(self, grobid_url: str = "http://localhost:8070"):
        self.base_url = grobid_url.rstrip("/")
        self.timeout = 60
    
    def is_alive(self) -> bool:
        """Check if GROBID server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/isalive",
                timeout=5
            )
            return response.ok
        except Exception:
            return False
    
    def process_header(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract header metadata from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with title, authors, year, DOI, abstract
        """
        if not os.path.exists(pdf_path):
            log.error(f"PDF not found: {pdf_path}")
            return None
        
        try:
            url = f"{self.base_url}/api/processHeaderDocument"
            
            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                response = requests.post(
                    url,
                    files=files,
                    timeout=self.timeout
                )
            
            if not response.ok:
                log.error(f"GROBID header extraction failed: HTTP {response.status_code}")
                return None
            
            # Parse TEI XML response
            tei_xml = response.text
            metadata = self._parse_header_tei(tei_xml)
            
            log.info(f"Extracted metadata from {Path(pdf_path).name}: {metadata.get('title', 'N/A')[:50]}")
            return metadata
        
        except requests.exceptions.Timeout:
            log.error(f"GROBID timeout processing {pdf_path}")
            return None
        except Exception as e:
            log.error(f"GROBID error processing {pdf_path}: {e}")
            return None
    
    def process_references(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract references from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of reference dictionaries
        """
        if not os.path.exists(pdf_path):
            log.error(f"PDF not found: {pdf_path}")
            return []
        
        try:
            url = f"{self.base_url}/api/processReferences"
            
            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                response = requests.post(
                    url,
                    files=files,
                    timeout=self.timeout
                )
            
            if not response.ok:
                log.error(f"GROBID reference extraction failed: HTTP {response.status_code}")
                return []
            
            # Parse TEI XML response
            tei_xml = response.text
            references = self._parse_references_tei(tei_xml)
            
            log.info(f"Extracted {len(references)} references from {Path(pdf_path).name}")
            return references
        
        except requests.exceptions.Timeout:
            log.error(f"GROBID timeout processing references in {pdf_path}")
            return []
        except Exception as e:
            log.error(f"GROBID error processing references in {pdf_path}: {e}")
            return []
    
    def _parse_header_tei(self, tei_xml: str) -> Dict[str, Any]:
        """
        Parse TEI XML from header extraction.
        
        Returns minimal metadata dict.
        """
        try:
            from lxml import etree
            
            # Parse XML
            root = etree.fromstring(tei_xml.encode('utf-8'))
            
            # Namespace
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            # Extract title
            title_elem = root.find('.//tei:titleStmt/tei:title', ns)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else None
            
            # Extract authors
            authors = []
            for author in root.findall('.//tei:sourceDesc//tei:author', ns):
                persName = author.find('.//tei:persName', ns)
                if persName is not None:
                    forename = persName.find('tei:forename', ns)
                    surname = persName.find('tei:surname', ns)
                    
                    name_parts = []
                    if forename is not None and forename.text:
                        name_parts.append(forename.text.strip())
                    if surname is not None and surname.text:
                        name_parts.append(surname.text.strip())
                    
                    if name_parts:
                        authors.append(" ".join(name_parts))
            
            # Extract year
            year = None
            date_elem = root.find('.//tei:sourceDesc//tei:date', ns)
            if date_elem is not None and date_elem.get('when'):
                try:
                    year = int(date_elem.get('when')[:4])
                except (ValueError, TypeError):
                    pass
            
            # Extract DOI
            doi = None
            for idno in root.findall('.//tei:sourceDesc//tei:idno', ns):
                if idno.get('type') == 'DOI':
                    doi = idno.text.strip() if idno.text else None
                    break
            
            # Extract abstract
            abstract = None
            abstract_elem = root.find('.//tei:profileDesc/tei:abstract', ns)
            if abstract_elem is not None:
                # Get all text content
                abstract = ''.join(abstract_elem.itertext()).strip()
            
            return {
                "title": title,
                "authors": authors,
                "year": year,
                "doi": doi,
                "abstract": abstract
            }
        
        except ImportError:
            log.error("lxml not installed. Run: pip install lxml")
            return {}
        except Exception as e:
            log.error(f"Error parsing GROBID TEI: {e}")
            return {}
    
    def _parse_references_tei(self, tei_xml: str) -> List[Dict[str, Any]]:
        """
        Parse TEI XML from reference extraction.
        
        Returns list of reference dicts.
        """
        try:
            from lxml import etree
            
            root = etree.fromstring(tei_xml.encode('utf-8'))
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            references = []
            
            for biblStruct in root.findall('.//tei:listBibl/tei:biblStruct', ns):
                ref = {}
                
                # Title
                title_elem = biblStruct.find('.//tei:title[@level="a"]', ns)
                if title_elem is not None and title_elem.text:
                    ref["title"] = title_elem.text.strip()
                
                # Authors
                authors = []
                for author in biblStruct.findall('.//tei:author', ns):
                    persName = author.find('.//tei:persName', ns)
                    if persName is not None:
                        surname = persName.find('tei:surname', ns)
                        if surname is not None and surname.text:
                            authors.append(surname.text.strip())
                
                if authors:
                    ref["authors"] = authors
                
                # Year
                date_elem = biblStruct.find('.//tei:date', ns)
                if date_elem is not None and date_elem.get('when'):
                    try:
                        ref["year"] = int(date_elem.get('when')[:4])
                    except (ValueError, TypeError):
                        pass
                
                # DOI
                for idno in biblStruct.findall('.//tei:idno', ns):
                    if idno.get('type') == 'DOI' and idno.text:
                        ref["doi"] = idno.text.strip()
                        break
                
                if ref:  # Only add if we extracted something
                    references.append(ref)
            
            return references
        
        except ImportError:
            log.error("lxml not installed. Run: pip install lxml")
            return []
        except Exception as e:
            log.error(f"Error parsing GROBID references: {e}")
            return []


# Global client instance
_grobid_client = None


def get_grobid_client(grobid_url: str = None) -> Optional[GrobidClient]:
    """
    Get or create GROBID client instance.
    
    Args:
        grobid_url: GROBID server URL (default from config)
    
    Returns:
        GrobidClient instance or None if unavailable
    """
    global _grobid_client
    
    if _grobid_client is None:
        if grobid_url is None:
            # Try to get from config
            try:
                from core.config import CFG
                grobid_url = "http://localhost:8070"  # Default
                if hasattr(CFG, 'grobid_url'):
                    grobid_url = CFG.grobid_url
            except:
                grobid_url = "http://localhost:8070"
        
        _grobid_client = GrobidClient(grobid_url)
        
        # Check if alive
        if not _grobid_client.is_alive():
            log.warning(f"GROBID server not reachable at {grobid_url}")
            log.warning("Start GROBID with: scripts/dev/run_grobid.bat")
            return None
    
    return _grobid_client


def parse_header(pdf_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract header metadata from PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Metadata dict with title, authors, year, doi, abstract
    """
    client = get_grobid_client()
    if client is None:
        return None
    
    return client.process_header(pdf_path)


def parse_references(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract references from PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        List of reference dicts
    """
    client = get_grobid_client()
    if client is None:
        return []
    
    return client.process_references(pdf_path)


def enrich_with_doi(metadata: Dict[str, Any], polite_email: str) -> Dict[str, Any]:
    """
    Enrich metadata by fetching additional info via DOI.
    
    Args:
        metadata: Metadata dict from GROBID
        polite_email: Email for polite API requests
    
    Returns:
        Enriched metadata dict
    """
    doi = metadata.get("doi")
    if not doi:
        return metadata
    
    enriched = metadata.copy()
    
    try:
        # Try Crossref for canonical metadata
        from .providers import fetch_crossref
        crossref_data = fetch_crossref(doi, polite_email)
        
        if crossref_data:
            # Merge Crossref data (prefer GROBID for extracted fields)
            if not enriched.get("abstract"):
                enriched["abstract"] = crossref_data.get("abstract")
            
            # Add venue if missing
            if not enriched.get("venue"):
                container = crossref_data.get("container-title", [])
                if container:
                    enriched["venue"] = container[0]
            
            log.info(f"Enriched metadata from Crossref for DOI: {doi}")
        
        # Try Unpaywall for OA PDF
        from .providers import unpaywall_best
        unpaywall_data = unpaywall_best(doi, polite_email)
        
        if unpaywall_data and unpaywall_data.get("pdf_url"):
            enriched["pdf_url"] = unpaywall_data["pdf_url"]
            enriched["oa_status"] = unpaywall_data.get("oa_status")
            log.info(f"Found OA PDF via Unpaywall for DOI: {doi}")
    
    except Exception as e:
        log.error(f"Error enriching metadata: {e}")
    
    return enriched


