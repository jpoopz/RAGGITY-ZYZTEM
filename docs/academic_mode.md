# Academic Mode - Scholarly Research Integration

**RAGGITY ZYZTEM 2.0 - Academic Research Module**

A comprehensive academic research toolkit integrated into RAGGITY for discovering, citing, and managing scholarly literature.

---

## 🎓 Overview

Academic Mode transforms RAGGITY into a powerful research assistant combining:
- **Multi-provider search** across OpenAlex, Crossref, ArXiv, Semantic Scholar, and Unpaywall
- **Harvard citation formatting** using CSL (Citation Style Language)
- **PDF metadata extraction** via GROBID
- **Hybrid retrieval** with BM25 + dense embeddings + Reciprocal Rank Fusion
- **Multiple export formats**: BibTeX, RIS, Markdown, CSV

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install academic dependencies
pip install -r requirements.txt

# Optional: Start GROBID for PDF extraction
.\scripts\dev\run_grobid.bat
```

### Basic Usage

**1. Search for Papers**
```python
from modules.academic.providers import search_openalex, search_arxiv

# OpenAlex (comprehensive scholarly database)
papers = search_openalex("machine learning", polite_email="you@example.com")

# ArXiv (preprints)
preprints = search_arxiv("neural networks", max_results=10)
```

**2. Generate Citations**
```python
from modules.academic.citations.harvard import cite_from_dois

result = cite_from_dois(
    dois=["10.1234/example.2023"],
    polite_email="you@example.com"
)

print(result["inline"])      # (Smith, 2023)
print(result["bibliography"]) # Full reference
```

**3. Export Bibliography**
```python
from modules.academic.exporters import to_bibtex, to_markdown_bibliography

# BibTeX for LaTeX
bibtex = to_bibtex(papers)

# Markdown for notes
markdown = to_markdown_bibliography(papers, style="harvard")
```

---

## 🔍 Provider Details

### OpenAlex
- **What**: Open scholarly metadata from 250M+ works
- **Auth**: Polite email (no API key needed)
- **Features**: OA status, citation counts, author affiliations, venues
- **Rate Limit**: 10 req/sec with polite email, 1/sec without
- **Config**: `academic.providers.openalex.enabled`, `polite_email`

**Example**:
```python
works = search_openalex(
    query="retrieval augmented generation",
    polite_email="julian.poopat@gmail.com",
    per_page=25
)

for work in works:
    print(f"{work.title} ({work.year})")
    print(f"  OA Status: {work.oa_status}")
    print(f"  Citations: {work.citation_count}")
```

### Crossref
- **What**: DOI metadata for 140M+ scholarly works
- **Auth**: Polite email (recommended)
- **Features**: Full bibliographic metadata, publisher info, funding
- **Rate Limit**: 50 req/sec with polite email
- **Config**: `academic.providers.crossref.enabled`, `polite_email`

**Example**:
```python
from modules.academic.providers import fetch_crossref

metadata = fetch_crossref("10.1038/nature12373", polite_email="you@example.com")
print(metadata["title"])
print(metadata["author"])
```

### ArXiv
- **What**: 2M+ preprints in physics, math, CS, etc.
- **Auth**: None required
- **Features**: PDF download, author info, categories, submission date
- **Rate Limit**: 3 req/sec
- **Config**: `academic.providers.arxiv.enabled`

**Example**:
```python
from modules.academic.arxiv_helper import download_and_index

# Download PDF and extract metadata
result = download_and_index("2301.12345", output_dir="data/arxiv")
print(result["metadata"])      # From GROBID
print(result["references"])    # Extracted citations
```

### Semantic Scholar
- **What**: AI-powered paper search with citation graphs
- **Auth**: Optional API key for higher limits and embeddings
- **Features**: Citation counts, influential citations, SPECTER2 embeddings
- **Rate Limit**: 100 req/5min (no key), 1000 req/5min (with key)
- **Config**: `academic.providers.semanticscholar.api_key`

**Example**:
```python
works = search_semanticscholar(
    query="transformers attention",
    api_key=os.getenv("S2_API_KEY"),  # Optional
    include_embeddings=True
)

for work in works:
    if work.is_highly_cited:
        print(f"⭐ {work.title} - {work.citation_count} citations")
```

### Unpaywall
- **What**: Open access PDF finder for 30M+ articles
- **Auth**: Email required
- **Features**: Legal OA PDFs, license info, version (published/accepted)
- **Rate Limit**: 100k req/day
- **Config**: `academic.providers.unpaywall.email`

**Example**:
```python
from modules.academic.providers import unpaywall_best

oa_location = unpaywall_best("10.1038/nature12373", email="you@example.com")
if oa_location:
    print(f"PDF: {oa_location['pdf_url']}")
    print(f"License: {oa_location['license']}")
    print(f"Version: {oa_location['version']}")
```

---

## 📝 Citation Formatting

### Harvard (Cite Them Right)

**Inline Citations**:
```python
from modules.academic.citations.harvard import cite_text

works = [
    {"title": "Paper A", "authors": ["Smith"], "year": 2023},
    {"title": "Paper B", "authors": ["Doe", "Lee"], "year": 2024}
]

inline = cite_text(works, inline=True)
# Output: "(Smith, 2023; Doe and Lee, 2024)"
```

**Full Bibliography**:
```python
from modules.academic.citations.harvard import render_bibliography, work_to_csl

csl_items = [work_to_csl(work) for work in works]
bib = render_bibliography(csl_items)

for entry in bib:
    print(entry)
# Output: Smith, J. (2023) 'Paper A'. Available at: ...
```

### Customization

The system downloads `harvard-cite-them-right.csl` on first use. To use a different style:

1. Download CSL file from: https://github.com/citation-style-language/styles
2. Save to: `modules/academic/citations/styles/your-style.csl`
3. Use: `render_bibliography(items, style_path=Path("your-style.csl"))`

---

## 🧬 GROBID PDF Processing

GROBID (GeneRation Of BIbliographic Data) extracts structured metadata from PDFs.

### Setup

**Windows**:
```powershell
.\scripts\dev\run_grobid.bat
```

**Manual Docker**:
```bash
docker pull lfoppiano/grobid:0.8.0
docker run --init -p 8070:8070 lfoppiano/grobid:0.8.0
```

### Usage

```python
from modules.academic.grobid_pipe import parse_header, parse_references, enrich_with_doi

# Extract metadata
metadata = parse_header("paper.pdf")
print(metadata["title"])
print(metadata["authors"])
print(metadata["doi"])

# Extract references
refs = parse_references("paper.pdf")
for ref in refs:
    print(f"{ref.get('title')} ({ref.get('year')})")

# Enrich with Crossref/Unpaywall
enriched = enrich_with_doi(metadata, polite_email="you@example.com")
print(enriched["pdf_url"])  # OA PDF if available
```

---

## 🔬 Hybrid Retrieval

Combines sparse (BM25) and dense (embeddings) search with Reciprocal Rank Fusion.

### How It Works

```
Query: "neural networks"
   ↓
┌──────────────┐  ┌──────────────┐
│ BM25 Ranking │  │Dense Ranking │
│ (term match) │  │ (semantic)   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ↓
        ┌───────────────┐
        │  RRF Fusion   │
        │ score = Σ 1   │
        │       k+rank  │
        └───────┬───────┘
                ↓
         Final Ranking
```

### Usage

```python
from modules.academic.retrieval.hybrid import HybridRetriever

retriever = HybridRetriever(
    dense_model="sentence-transformers/all-MiniLM-L6-v2",
    bm25_impl="rank_bm25",
    rrf_k=60
)

# Index documents
retriever.index(documents)

# Query
results = retriever.query_hybrid("machine learning", top_k=12)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"  Dense rank: {result.dense_rank}, Sparse rank: {result.sparse_rank}")
    print(f"  Text: {result.text[:100]}...")
```

### Configuration

```yaml
academic:
  retrieval:
    dense_model: "sentence-transformers/all-MiniLM-L6-v2"
    bm25_impl: "rank_bm25"  # or "bm25s" for speed
    rrf_k: 60
    top_k: 12
```

---

## 🌐 API Endpoints

### GET /academic/search
Search across multiple providers:

```bash
curl "http://localhost:8000/academic/search?q=transformers&providers=openalex,arxiv&polite_email=you@example.com"
```

Response:
```json
{
  "query": "transformers",
  "providers": ["openalex", "arxiv"],
  "count": 25,
  "results": [
    {
      "title": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "year": 2017,
      "doi": "...",
      "pdf_url": "https://arxiv.org/pdf/...",
      "citation_count": 50000,
      "is_highly_cited": true
    }
  ]
}
```

### POST /academic/cite
Generate Harvard citations:

```bash
curl -X POST "http://localhost:8000/academic/cite" \
  -H "Content-Type: application/json" \
  -d '{"dois": ["10.1234/example"], "polite_email": "you@example.com"}'
```

Response:
```json
{
  "inline": "(Smith, 2023)",
  "bibliography": ["Smith, J. (2023) ..."],
  "count": 1
}
```

### POST /academic/export
Export to multiple formats:

```bash
curl -X POST "http://localhost:8000/academic/export" \
  -H "Content-Type: application/json" \
  -d '{"works": [...], "format": "bibtex"}'
```

Formats: `bibtex`, `ris`, `markdown`, `csv`

### GET /academic/resolve_pdf
Find OA PDF for DOI:

```bash
curl "http://localhost:8000/academic/resolve_pdf?doi=10.1234/example&polite_email=you@example.com"
```

Response:
```json
{
  "doi": "10.1234/example",
  "pdf_url": "https://...",
  "oa_status": "gold",
  "license": "CC-BY",
  "version": "publishedVersion"
}
```

### POST /academic/download_arxiv
Download ArXiv PDF with GROBID extraction:

```bash
curl -X POST "http://localhost:8000/academic/download_arxiv" \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "2301.12345"}'
```

---

## 🎨 UI Integration

### Academic Tab

The Academic tab provides a graphical interface for all features:

**Search Section**:
- Multi-line query input
- Provider toggles (OpenAlex, ArXiv, S2, Crossref)
- Advanced options (collapsed): polite email, result limit

**Results List**:
- Title, authors, year, venue
- Badges: 🟢 OA, 📄 DOI, 📋 ArXiv, ⭐ Highly Cited (>100)
- Actions per row:
  - **Preview**: Show abstract in popup
  - **Add to Draft**: Add to bibliography builder
  - **Copy DOI**: Copy to clipboard
  - **Open PDF**: Resolve and open OA PDF (if available)
  - **Harvard Cite**: Generate inline citation

**Draft Builder**:
- Shows selected papers
- Actions:
  - **Copy Inline Cites**: (Author1, Year; Author2, Year)
  - **Copy Bibliography**: Full Harvard references
  - **Export**: Dropdown menu:
    - Bibliography (Harvard Markdown)
    - BibTeX (.bib)
    - RIS (.ris)
    - CSV (.csv)

**Settings Panel** (collapsed):
- Citation style selector (Harvard CTR default)
- Locale (en-GB default)
- RRF k parameter
- Dense model selection

---

## ⚙️ Configuration

### config.yaml

```yaml
academic:
  enabled: true
  
  providers:
    openalex:
      enabled: true
      polite_email: "your.email@domain.com"
    
    crossref:
      enabled: true
      polite_email: "your.email@domain.com"
    
    arxiv:
      enabled: true
    
    semanticscholar:
      enabled: false
      api_key: ""  # Optional: set via S2_API_KEY env var
    
    unpaywall:
      enabled: true
      email: "your.email@domain.com"
  
  citations:
    style: "harvard-cite-them-right"
    locale: "en-GB"
  
  retrieval:
    dense_model: "sentence-transformers/all-MiniLM-L6-v2"
    bm25_impl: "rank_bm25"  # or "bm25s"
    rrf_k: 60
    top_k: 12
  
  grobid:
    url: "http://localhost:8070"
    enabled: true
```

### Environment Variables

```bash
# Semantic Scholar API key (optional, for advanced features)
set S2_API_KEY=your-api-key-here

# Polite emails (recommended for better rate limits)
set OPENALEX_EMAIL=your.email@domain.com
set CROSSREF_EMAIL=your.email@domain.com
set UNPAYWALL_EMAIL=your.email@domain.com
```

---

## 🧪 Testing

```bash
# Run academic module tests
pytest tests/test_academic_flow.py -v

# Test specific provider
pytest tests/test_academic_flow.py::test_openalex_search_smoke -v

# Test citation formatting
pytest tests/test_academic_flow.py::test_harvard_bibliography_formatting -v

# Test hybrid retrieval
pytest tests/test_academic_flow.py::test_rrf_fusion_ordering -v
```

---

## 📊 Performance

### Benchmarks (typical)

| Operation | Time | Notes |
|-----------|------|-------|
| OpenAlex search | 200-500ms | 25 results |
| ArXiv search | 300-800ms | 25 results |
| S2 search | 400-1000ms | 25 results |
| Crossref fetch | 100-300ms | Per DOI |
| Unpaywall resolve | 150-400ms | Per DOI |
| GROBID header | 2-5s | Per PDF |
| GROBID references | 5-15s | Per PDF |
| BibTeX export | <100ms | 100 items |
| RRF fusion | <50ms | 1000 items |

### Optimization Tips

1. **Use polite emails** - 10x faster rate limits
2. **Enable caching** - Avoid redundant API calls
3. **Batch operations** - Group DOI fetches
4. **Use S2 API key** - Higher limits + embeddings
5. **Run GROBID locally** - Faster than API

---

## 🔐 Privacy & Ethics

### Data Collection
- **No tracking**: All API calls go directly to providers
- **No storage**: Results cached only in local vector store
- **No sharing**: Your queries are not shared with RAGGITY

### Polite API Usage
- Uses polite headers (`mailto:`) for better rate limits
- Respects provider rate limits (100-500ms delays)
- Identifies as "RAGGITY/2.0" in User-Agent
- Never scrapes; uses official APIs only

### Open Access
- Prioritizes legal OA sources (Unpaywall)
- Never bypasses paywalls
- Links to publisher pages when OA unavailable
- Respects copyright and licenses

---

## 🐛 Troubleshooting

### "GROBID server not reachable"
```bash
# Check if Docker is running
docker ps

# Start GROBID
.\scripts\dev\run_grobid.bat

# Verify: http://localhost:8070/api/isalive
```

### "OpenAlex rate limit exceeded"
- Add polite email to config
- Wait 1 minute and retry
- Check if your email is in polite pool

### "Semantic Scholar API error"
- Verify API key is correct
- Check rate limits (100/5min without key)
- Ensure network access to api.semanticscholar.org

### "Citation rendering failed"
- Install citeproc-py: `pip install citeproc-py`
- Check CSL file exists in `citations/styles/`
- Try re-downloading style: delete cached .csl and retry

### "Hybrid retrieval slow"
- First query downloads SentenceTransformers model (~100MB)
- Subsequent queries are fast (<50ms)
- Use smaller model for speed: "all-MiniLM-L6-v2" (default)

---

## 📚 Examples

### Research Workflow

```python
# 1. Search for papers
from modules.academic.providers import multi_search

config = {
    "openalex": {"enabled": True, "polite_email": "you@example.com"},
    "arxiv": {"enabled": True}
}

papers = multi_search(
    query="retrieval augmented generation",
    providers=["openalex", "arxiv"],
    config=config
)

# 2. Filter highly-cited papers
highly_cited = [p for p in papers if p.is_highly_cited]

# 3. Download ArXiv PDFs
from modules.academic.arxiv_helper import download_and_index

for paper in papers:
    if paper.arxiv_id:
        result = download_and_index(paper.arxiv_id)
        print(f"Downloaded: {result['pdf_path']}")

# 4. Generate bibliography
from modules.academic.exporters import to_markdown_bibliography

works_dicts = [p.to_dict() for p in papers[:10]]
markdown = to_markdown_bibliography(works_dicts)

with open("bibliography.md", "w") as f:
    f.write(markdown)

# 5. Export to BibTeX
from modules.academic.exporters import to_bibtex

bibtex = to_bibtex(works_dicts)
with open("references.bib", "w") as f:
    f.write(bibtex)
```

---

## 🚀 Advanced Features

### Custom CSL Styles

```python
from pathlib import Path
from modules.academic.citations.harvard import render_bibliography, ensure_style

# Download APA style
style_path = ensure_style("apa")

# Render with custom style
bibliography = render_bibliography(csl_items, style_path=style_path)
```

### Hybrid Retrieval Integration

```python
# Combine local docs + fetched abstracts
from modules.academic.retrieval.hybrid import HybridRetriever

retriever = HybridRetriever(rrf_k=60)

# Index: local documents + paper abstracts
documents = local_docs + [p.abstract for p in papers if p.abstract]
retriever.index(documents)

# Query with fusion
results = retriever.query_hybrid("what is attention mechanism?", top_k=12)

# Results include both local and remote content, ranked by relevance
```

### Batch DOI Resolution

```python
from modules.academic.providers import unpaywall_best

dois = ["10.1234/a", "10.1234/b", "10.1234/c"]
oa_pdfs = []

for doi in dois:
    oa = unpaywall_best(doi, email="you@example.com")
    if oa and oa["pdf_url"]:
        oa_pdfs.append(oa)

print(f"Found {len(oa_pdfs)} OA PDFs from {len(dois)} DOIs")
```

---

## 📖 References

- **OpenAlex**: https://openalex.org
- **Crossref**: https://www.crossref.org
- **ArXiv**: https://arxiv.org
- **Semantic Scholar**: https://www.semanticscholar.org
- **Unpaywall**: https://unpaywall.org
- **GROBID**: https://grobid.readthedocs.io
- **CSL**: https://citationstyles.org

---

## 🤝 Contributing

Academic Mode is under active development. Contributions welcome:

- Additional citation styles (APA, MLA, Chicago, etc.)
- More providers (PubMed, Google Scholar proxies, etc.)
- Enhanced metadata extraction
- UI improvements

---

**Built for researchers, by researchers. Happy citing! 📚✨**

