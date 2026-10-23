@echo off
uv sync
start cmd /k "uv run uvicorn app.api:app --reload"
uv run streamlit run app/ui.py
