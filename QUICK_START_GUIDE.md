# Quick Start Guide - READ THIS FIRST!

## ⚠️ Important: You Must Be in the Right Directory!

The scripts are in:
```
C:\Users\Julian Poopat\Documents\Management Class\RAG_System
```

**You're currently in:** `C:\Users\Julian Poopat` ❌

## ✅ Easy Way (Double-Click)

1. **Navigate to:** `C:\Users\Julian Poopat\Documents\Management Class\RAG_System`
2. **Double-click:** `START_HERE.bat` - Opens a command prompt in the right place
3. **Then run commands** in that window

OR

**Double-click these files directly:**
- `1_INDEX.bat` - To index documents
- `2_START_API.bat` - To start the API server

## ✅ Manual Way (Command Prompt)

**Step 1: Open Command Prompt**

**Step 2: Navigate to the RAG System folder:**
```
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
```

**Step 3: Now run these commands (without the ``` parts!):**

### 1. Index Documents
```
python index_documents.py
```

### 2. Start API Server
```
python rag_api.py
```
*(Keep this window open - the server runs here)*

### 3. Test (Open a NEW Command Prompt)

Open a **NEW** command prompt window (don't close the API server!), then:

```
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
.\test_all_endpoints.ps1
```

OR test a query:
```
python query_helper.py query "What is management?"
```

## 🚫 Common Mistakes

**DON'T:**
- Copy and paste the ` ``` ` markdown formatting ❌
- Run commands from your home directory (`C:\Users\Julian Poopat`) ❌
- Close the API server window while testing ❌

**DO:**
- Use plain commands without markdown formatting ✅
- Navigate to the RAG_System folder first ✅
- Use the .bat files for easy access ✅

## 📝 Exact Commands (Copy These - NO MARKDOWN!)

Open Command Prompt and run:

```
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
python index_documents.py
```

Wait for indexing to finish, then:

```
python rag_api.py
```

Keep that window open! Open a NEW window for testing:

```
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
python query_helper.py query "test"
```

## 🎯 What Each Command Does

| Command | What It Does |
|---------|-------------|
| `python index_documents.py` | Scans your Notes folder and creates searchable index |
| `python rag_api.py` | Starts the API server (must stay running) |
| `python query_helper.py query "question"` | Test a query |
| `.\test_all_endpoints.ps1` | Test all API endpoints |

## 💡 Pro Tip

**Create a shortcut:**
1. Right-click on `START_HERE.bat`
2. "Send to" → "Desktop (create shortcut)"
3. Double-click that shortcut whenever you need the RAG system!

---

**Ready? Start with:** `1_INDEX.bat` (double-click it!)




