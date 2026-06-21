#!/bin/bash
cd "$(dirname "$0")/.."
cd backend
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
