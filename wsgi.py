#!/usr/bin/env python3
"""
WSGI entry point for the Instagram DM Bot
"""

import os
import sys

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

# Import the Flask app
from run import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
