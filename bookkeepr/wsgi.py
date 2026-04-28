"""
BookKeepr AI - WSGI entry point for Gunicorn (production / Render)
"""
import os
import sys

# Add the app directory to path (where run.py is located)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

# Load environment variables BEFORE any app imports
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Import from the app directory
from run import app as application

# Gunicorn looks for `application` by default
app = application
