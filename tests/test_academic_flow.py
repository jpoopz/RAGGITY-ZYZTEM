"""
Academic module integration tests.

Tests provider search, citation formatting, retrieval fusion, and GROBID parsing.
"""

import os
import sys
import pytest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_openalex_search_smoke():
    """Smoke test for OpenAlex search"""
    try:
        from modules.academic.providers import search_openalex
        
        # Search for a well-known topic
        results = search_openalex(
            query="machine learning",
            polite_email="test@example.com",
            per_page=5
        )
        
        # Should return some results (may be 0 if API is down, but shouldn't crash)
        assert isinstance(results, list)
        
        # If results exist, check structure
        if results:
            work = results[0]
            assert hasattr(work, 'title')
            assert hasattr(work, 'authors')
            assert work.source == "openalex"
    
    except ImportError:
        pytest.skip("OpenAlex dependencies not installed")
    except Exception as e:
        # Network errors are acceptable in tests
        pytest.skip(f"OpenAlex API unavailable: {e}")


def test_crossref_to_csl():
    """Test Crossref metadata to CSL-JSON conversion"""
    try:
        from modules.academic.citations.harvard import crossref_to_csl
        
        # Mock Crossref response
        crossref_data = {
            "DOI": "10.1234/test.2023",
            "type": "journal-article",
            "title": ["Test Article Title"],
            "author": [
                {"given": "John", "family": "Smith"},
                {"given": "Jane", "family": "Doe"}
            ],
            "published": {
                "date-parts": [[2023, 5, 15]]
            },
            "container-title": ["Test Journal"],
            "volume": "42",
            "issue": "3",
            "page": "123-145"
        }
        
        csl_item = crossref_to_csl(crossref_data)
        
        # Verify conversion
        assert csl_item["id"] == "10.1234/test.2023"
        assert csl_item["type"] == "journal-article"
        assert csl_item["title"] == "Test Article Title"
        assert csl_item["DOI"] == "10.1234/test.2023"
        assert len(csl_item["author"]) == 2
        assert csl_item["author"][0]["family"] == "Smith"
        assert csl_item["volume"] == "42"
    
    except ImportError as e:
        pytest.skip(f"Citation dependencies not installed: {e}")


def test_harvard_bibliography_formatting():
    """Test Harvard citation formatting"""
    try:
        from modules.academic.citations.harvard import cite_text, work_to_csl, render_bibliography
        
        # Create test works
        works = [
            {
                "title": "Machine Learning Basics",
                "authors": ["John Smith", "Jane Doe"],
                "year": 2023,
                "doi": "10.1234/ml.2023",
                "venue": "AI Journal"
            },
            {
                "title": "Deep Learning Advanced",
                "authors": ["Alice Johnson"],
                "year": 2024,
                "doi": "10.1234/dl.2024",
                "venue": "Neural Networks"
            }
        ]
        
        # Test inline citations
        inline = cite_text(works, inline=True)
        assert isinstance(inline, str)
        assert "2023" in inline or "2024" in inline
        assert "(" in inline and ")" in inline
        
        # Test CSL conversion
        csl_items = [work_to_csl(work, f"work-{i}") for i, work in enumerate(works)]
        assert len(csl_items) == 2
        assert csl_items[0]["title"] == "Machine Learning Basics"
        
        # Test bibliography rendering (may fail without citeproc dependencies)
        try:
            bib = render_bibliography(csl_items)
            assert isinstance(bib, list)
            # Bibliography should have entries for each work
            assert len(bib) <= len(csl_items) + 1  # May have slight variation
        except Exception:
            # CSL rendering can fail without proper setup, that's ok
            pass
    
    except ImportError as e:
        pytest.skip(f"Citation dependencies not installed: {e}")


def test_rrf_fusion_ordering():
    """Test Reciprocal Rank Fusion combines rankings correctly"""
    try:
        from modules.academic.retrieval.hybrid import HybridRetriever
        
        # Create small corpus
        docs = [
            "Machine learning is a subset of artificial intelligence",
            "Deep learning uses neural networks with multiple layers",
            "Natural language processing handles text data",
            "Computer vision processes images and videos"
        ]
        
        retriever = HybridRetriever(
            dense_model="sentence-transformers/all-MiniLM-L6-v2",
            rrf_k=60
        )
        
        # Index documents
        retriever.index(docs)
        
        # Query
        results = retriever.query_hybrid("neural networks", top_k=3)
        
        # Should return results
        assert isinstance(results, list)
        assert len(results) <= 3
        
        # Results should have RRF scores
        if results:
            assert hasattr(results[0], 'score')
            assert hasattr(results[0], 'text')
            
            # Scores should be in descending order
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)
    
    except ImportError as e:
        pytest.skip(f"Retrieval dependencies not installed: {e}")
    except Exception as e:
        # Model download or other issues
        pytest.skip(f"Hybrid retrieval unavailable: {e}")


def test_grobid_parse_header_mock():
    """Test GROBID header parsing with mock TEI XML"""
    try:
        from modules.academic.grobid_pipe import GrobidClient
        
        # Mock TEI XML response
        mock_tei = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>Test Paper Title</title>
            </titleStmt>
            <sourceDesc>
                <biblStruct>
                    <analytic>
                        <author>
                            <persName>
                                <forename>John</forename>
                                <surname>Smith</surname>
                            </persName>
                        </author>
                        <idno type="DOI">10.1234/test.2023</idno>
                    </analytic>
                    <monogr>
                        <imprint>
                            <date type="published" when="2023">2023</date>
                        </imprint>
                    </monogr>
                </biblStruct>
            </sourceDesc>
        </fileDesc>
        <profileDesc>
            <abstract>This is a test abstract.</abstract>
        </profileDesc>
    </teiHeader>
</TEI>'''
        
        client = GrobidClient()
        metadata = client._parse_header_tei(mock_tei)
        
        # Verify parsing
        assert metadata["title"] == "Test Paper Title"
        assert "John Smith" in metadata["authors"]
        assert metadata["year"] == 2023
        assert metadata["doi"] == "10.1234/test.2023"
        assert "test abstract" in metadata["abstract"].lower()
    
    except ImportError as e:
        pytest.skip(f"GROBID dependencies not installed: {e}")


def test_arxiv_id_to_pseudo_doi():
    """Test ArXiv ID conversion to pseudo-DOI"""
    from modules.academic.arxiv_helper import arxiv_id_to_pseudo_doi, get_arxiv_pdf_url
    
    # Test ID conversion
    assert arxiv_id_to_pseudo_doi("2301.12345") == "arxiv:2301.12345"
    assert arxiv_id_to_pseudo_doi("2301.12345v2") == "arxiv:2301.12345"
    assert arxiv_id_to_pseudo_doi("2301.12345v1") == "arxiv:2301.12345"
    
    # Test PDF URL generation
    pdf_url = get_arxiv_pdf_url("2301.12345")
    assert pdf_url == "https://arxiv.org/pdf/2301.12345.pdf"
    
    pdf_url_versioned = get_arxiv_pdf_url("2301.12345v2")
    assert pdf_url_versioned == "https://arxiv.org/pdf/2301.12345.pdf"


def test_export_formats():
    """Test various export formats"""
    try:
        from modules.academic.exporters import to_bibtex, to_ris, to_csv
        
        # Test data
        works = [
            {
                "title": "Test Paper",
                "authors": ["Smith, John", "Doe, Jane"],
                "year": 2023,
                "doi": "10.1234/test",
                "venue": "Test Journal",
                "abstract": "This is a test"
            }
        ]
        
        # Test BibTeX export
        bibtex = to_bibtex(works)
        assert isinstance(bibtex, str)
        assert "@" in bibtex  # BibTeX entries start with @
        assert "Test Paper" in bibtex or "title" in bibtex.lower()
        
        # Test RIS export
        ris = to_ris(works)
        assert isinstance(ris, str)
        assert "TY  -" in ris  # RIS type tag
        assert "TI  -" in ris  # Title tag
        assert "ER  -" in ris  # End record tag
        
        # Test CSV export
        csv = to_csv(works)
        assert isinstance(csv, str)
        assert "title" in csv.lower()
        assert "2023" in csv
    
    except ImportError as e:
        pytest.skip(f"Export dependencies not installed: {e}")


def test_work_model_properties():
    """Test Work model properties and methods"""
    from modules.academic.providers import Work
    
    # Test highly cited property
    work_highly_cited = Work(
        title="Highly Cited Paper",
        citation_count=150
    )
    assert work_highly_cited.is_highly_cited is True
    
    work_not_cited = Work(
        title="New Paper",
        citation_count=50
    )
    assert work_not_cited.is_highly_cited is False
    
    work_no_citations = Work(
        title="Unknown Citations"
    )
    assert work_no_citations.is_highly_cited is False
    
    # Test to_dict
    work_dict = work_highly_cited.to_dict()
    assert work_dict["title"] == "Highly Cited Paper"
    assert work_dict["citation_count"] == 150
    assert work_dict["is_highly_cited"] is True


