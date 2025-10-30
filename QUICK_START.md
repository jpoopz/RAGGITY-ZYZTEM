# Quick Start Guide - RAG System

## 🚀 3-Step Setup

### Step 1: Install Dependencies (2 minutes)

```powershell
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
pip install -r requirements.txt
```

**Or run:**
```powershell
.\setup.bat
```

### Step 2: Index Your Documents (5-10 minutes)

```powershell
python index_documents.py
```

This scans all files in `Notes/` and creates the searchable index.

### Step 3: Test It!

```powershell
python query_llm.py "What is management?"
```

## 🎯 Next Level: Start API Server

For Obsidian integration:

```powershell
.\start_api.bat
# Or: python rag_api.py
```

API runs on `http://localhost:5000`

## 📚 Using the System

### Basic Query
```powershell
python query_llm.py "Explain organizational behavior"
```

### With Web Fallback
```powershell
python query_llm.py "What is SWOT analysis?" --web
```

### Different Modes
```powershell
# Concise
python query_llm.py "Key management principles" --concise

# Creative Academic
python query_llm.py "Future of management" --creative
```

## 🔄 Re-index When You Add New Notes

```powershell
python index_documents.py
```

Takes a few minutes depending on document count.

## 📖 Full Documentation

See `README.md` for complete documentation and API details.

---

**That's it!** You now have a local NotebookLM-style academic assistant! 🎓




