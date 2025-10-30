@echo off
call .venv\Scripts\activate
python -V
pytest -q
