#!/usr/bin/env bash
# รันบน macOS/Linux
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q -r requirements.txt
python -m uvicorn api.main:app --port 8000
gh codespace ports visibility 8000:public -c $CODESPACE_NAME

