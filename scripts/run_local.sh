#!/usr/bin/env bash
set -e
# load .env if present (requires 'pip install python-dotenv' if you want to use dotenv to load env)
export $(grep -v '^#' .env | xargs) || true
streamlit run app/streamlit_app.py --server.port=${PORT:-8501}
