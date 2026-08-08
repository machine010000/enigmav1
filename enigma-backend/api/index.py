"""
Vercel entry point for the FastAPI backend.
"""
import sys
import os

# Add the backend to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel will use this as the entry point
handler = app
