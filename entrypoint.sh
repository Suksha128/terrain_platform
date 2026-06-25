#!/bin/bash

# Start the FastAPI backend in the background
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd ..

# Wait a few seconds for backend to initialize
sleep 3

# Start the Streamlit frontend in the foreground
streamlit run streamlit_app.py --server.port=7860 --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
