"""
Citation export utilities.

Supports multiple formats:
- BibTeX (via pybtex)
- RIS (Research Information Systems)
- Markdown bibliography (formatted with CSL)
- CSV (for spreadsheet import)
"""

import io
from typing import List, Dict, Any
from datetime import datetime

from logger import get_logger

log = get_logger("exporters")


def to_bibtex(works: List[Dict[str, Any]]) -> str:
    """
    Convert works to BibTeX format.
    
    Args:
        works: List of work dictionaries
    
    Returns:
        BibTeX string
    """
    try:
        from pybtex.database import BibliographyData, Entry
        
        bib_db = BibliographyData()
        
        for idx, work in enumerate(works):
            # Generate citation key
            authors = work.get("authors", [])
            year = work.get("year")
            
            if authors and isinstance(authors, list) and len(authors) > 0:
                first_author = authors[0].split()[-1].lower() if isinstance(authors[0], str) else "unknown"
            else:
                first_author = "unknown"
            
            key = f"{first_author}{year or 'nd'}_{idx}"
            
            # Determine entry type
            source = work.get("source", "")
            if source == "arxiv" or work.get("arxiv_id"):
                entry_type = "article"
            else:
                entry_type = "article"
            
            # Build fields
            fields = {}
            
            if work.get("title"):
                fields["title"] = work["title"]
            
            if authors:
                # Convert to "Last1, First1 and Last2, First2" format
                author_strs = []
                for author in authors[:10]:  # Limit to 10
                    if isinstance(author, str):
                        parts = author.strip().split()
                        if len(parts) >= 2:
                            family = parts[-1]
                            given = " ".join(parts[:-1])
                            author_strs.append(f"{family}, {given}")
                        else:
                            author_strs.append(author)
                
                if author_strs:
                    fields["author"] = " and ".join(author_strs)
            
            if year:
                fields["year"] = str(year)
            
            if work.get("doi"):
                fields["doi"] = work["doi"]
            
            if work.get("url"):
                fields["url"] = work["url"]
            
            if work.get("venue"):
                fields["journal"] = work["venue"]
            
            if work.get("abstract"):
                fields["abstract"] = work["abstract"]
            
            # ArXiv specific
            if work.get("arxiv_id"):
                fields["eprint"] = work["arxiv_id"]
                fields["archivePrefix"] = "arXiv"
            
            # Create entry
            if fields:
                entry = Entry(entry_type, fields=[(k, v) for k, v in fields.items()])
                bib_db.entries[key] = entry
        
        # Convert to string
        output = io.StringIO()
        bib_db.to_file(output, bib_format='bibtex')
        bibtex_str = output.getvalue()
        
        log.info(f"Exported {len(bib_db.entries)} entries to BibTeX")
        return bibtex_str
    
    except ImportError:
        log.error("pybtex not installed. Run: pip install pybtex")
        return "% Error: pybtex not installed\n"
    except Exception as e:
        log.error(f"BibTeX export failed: {e}")
        return f"% Error: {e}\n"


def to_ris(works: List[Dict[str, Any]]) -> str:
    """
    Convert works to RIS format.
    
    Args:
        works: List of work dictionaries
    
    Returns:
        RIS formatted string
    """
    lines = []
    
    for work in works:
        # Start entry
        source = work.get("source", "")
        if source == "arxiv":
            lines.append("TY  - JOUR")  # Journal article
            lines.append("T2  - arXiv preprint")
        else:
            lines.append("TY  - JOUR")  # Journal article
        
        # Title
        if work.get("title"):
            lines.append(f"TI  - {work['title']}")
        
        # Authors
        for author in work.get("authors", [])[:20]:
            if isinstance(author, str):
                lines.append(f"AU  - {author}")
        
        # Year
        if work.get("year"):
            lines.append(f"PY  - {work['year']}")
        
        # Venue/Journal
        if work.get("venue"):
            lines.append(f"JO  - {work['venue']}")
        
        # DOI
        if work.get("doi"):
            lines.append(f"DO  - {work['doi']}")
        
        # URL
        if work.get("url"):
            lines.append(f"UR  - {work['url']}")
        
        # Abstract
        if work.get("abstract"):
            abstract = work["abstract"].replace("\n", " ")
            lines.append(f"AB  - {abstract}")
        
        # PDF URL
        if work.get("pdf_url"):
            lines.append(f"L1  - {work['pdf_url']}")
        
        # End entry
        lines.append("ER  - ")
        lines.append("")  # Blank line between entries
    
    ris_str = "\n".join(lines)
    log.info(f"Exported {len(works)} entries to RIS")
    
    return ris_str


def to_markdown_bibliography(works: List[Dict[str, Any]], style: str = "harvard") -> str:
    """
    Convert works to Markdown-formatted bibliography.
    
    Args:
        works: List of work dictionaries
        style: Citation style (currently only "harvard" supported)
    
    Returns:
        Markdown formatted bibliography
    """
    try:
        from .citations.harvard import work_to_csl, render_bibliography
        
        # Convert to CSL items
        csl_items = []
        for idx, work in enumerate(works):
            csl_item = work_to_csl(work, f"work-{idx}")
            csl_items.append(csl_item)
        
        # Render bibliography
        bib_entries = render_bibliography(csl_items)
        
        # Format as Markdown
        lines = [
            "# Bibliography",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Style: {style.title()}*",
            f"*Count: {len(works)} items*",
            "",
            "---",
            ""
        ]
        
        for idx, entry in enumerate(bib_entries, 1):
            # Strip HTML tags for plain text
            import re
            plain_entry = re.sub(r'<[^>]+>', '', entry)
            
            lines.append(f"{idx}. {plain_entry}")
            lines.append("")
        
        markdown = "\n".join(lines)
        log.info(f"Exported {len(works)} entries to Markdown ({style})")
        
        return markdown
    
    except Exception as e:
        log.error(f"Markdown bibliography export failed: {e}")
        return f"# Error\n\n{e}\n"


def to_csv(works: List[Dict[str, Any]]) -> str:
    """
    Convert works to CSV format.
    
    Args:
        works: List of work dictionaries
    
    Returns:
        CSV string
    """
    import csv
    import io
    
    output = io.StringIO()
    
    # Define columns
    fieldnames = [
        "title", "year", "authors", "venue", "doi", "url", "pdf_url",
        "citation_count", "source", "oa_status", "arxiv_id"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for work in works:
        # Flatten authors list
        row = work.copy()
        if isinstance(row.get("authors"), list):
            row["authors"] = "; ".join(row["authors"])
        
        writer.writerow(row)
    
    csv_str = output.getvalue()
    log.info(f"Exported {len(works)} entries to CSV")
    
    return csv_str

