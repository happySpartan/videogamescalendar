#!/usr/bin/env python
# filepath: c:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar\backend\run.py
"""
Entry point for the Flask application.
"""
import os
import sys

# Add the current directory to the path so we can import app modules correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=False)
