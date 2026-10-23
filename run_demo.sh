#!/usr/bin/env bash
set -e
uv sync
uv run uvicorn app.api:app --reload &
uv run streamlit run app/ui.py
