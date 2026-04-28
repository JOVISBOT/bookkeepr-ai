"""BookKeepr AI - Entry Point"""
import os
import sys

# Load environment variables BEFORE any app imports
from dotenv import load_dotenv
load_dotenv()

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
