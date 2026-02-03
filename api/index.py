import sys
import os

# Add the project root to the sys.path
# This ensures that imports from the root directory (like app.py, scraper.py) work
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the Flask app instance from app.py
try:
    from app import app
except ImportError as e:
    # Fallback for diagnostic if import fails
    from flask import Flask
    app = Flask(__name__)
    @app.route("/_debug")
    def debug():
        return {
            "error": str(e),
            "sys_path": sys.path,
            "root_dir": root_dir,
            "contents": os.listdir(root_dir) if os.path.exists(root_dir) else "not found"
        }

# Vercel needs 'app' or 'application' to be available at the module level
application = app
