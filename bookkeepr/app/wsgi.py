"""
BookKeepr AI - WSGI entry point for Gunicorn (production / Render)
"""
import os
import sys

# Ensure the app directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables BEFORE any app imports
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from run import app as application

# Gunicorn looks for `application` by default
app = application
