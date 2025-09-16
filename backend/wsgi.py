#!/usr/bin/env python
# filepath: c:\Users\jonathan.peil\Downloads\ProgProjects\videogamecalendar\backend\wsgi.py
"""
WSGI entry point for the Flask application.
This file is used for deployment environments like Gunicorn.
"""
import os
import sys

# Add the current directory to the path so we can import app modules correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
