@echo off
set PYTHONUTF8=1
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
uvicorn rag_api:app --host 0.0.0.0 --port 8000 --reload
