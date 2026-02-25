"""
WSGI application entry point for production deployment.
Used by Gunicorn, Heroku, and other production servers.

Usage:
    gunicorn wsgi:app
    gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from web.app import create_app

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # This is for local development only
    # Use Gunicorn for production
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('APP_PORT', 5000)),
        debug=os.getenv('DEBUG', 'False') == 'True'
    )
