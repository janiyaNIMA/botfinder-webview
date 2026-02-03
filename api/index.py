import sys
import os
import json
import threading
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

# Add the project root to sys.path so we can import scraper
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import the custom scraper module
try:
    from scraper import GitHubBotScraper
except ImportError:
    # Fallback if import fails during build/init
    GitHubBotScraper = None

app = Flask(__name__, template_folder=os.path.join(root_dir, 'templates'))
load_dotenv(os.path.join(root_dir, '.env'))

MONGO_URI = os.getenv("mdb")

def get_db_collection():
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.get_database("bot_directory")
        return db.get_collection("bots")
    except:
        return None

@app.route("/")
def index():
    collection = get_db_collection()
    bots = []
    if collection is not None:
        try:
            bots = list(collection.find({}, {'_id': 0}).sort("stars", -1))
        except Exception as e:
            print(f"MongoDB Error: {e}")
            collection = None # Force fallback
    
    if collection is None or not bots:
        # Fallback to local file if DB fails or is empty
        try:
            local_data_path = os.path.join(root_dir, "bots_data.json")
            if os.path.exists(local_data_path):
                with open(local_data_path, "r", encoding="utf-8") as f:
                    bots = json.load(f)
            else:
                bots = []
        except Exception as e:
            print(f"Local file Error: {e}")
            bots = []
    return render_template("index.html", bots=bots)

@app.route("/sync")
def sync():
    """Route to trigger sync manually (Vercel friendly)"""
    if GitHubBotScraper is None:
        return "Scraper module not found", 500

    def run_sync(limit=None):
        scraper = GitHubBotScraper(
            github_token=os.getenv("GITHUB_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            mongo_uri=MONGO_URI
        )
        scraper.run(limit=limit)

    # On Vercel, this route will just run the logic directly (blocking)
    if os.environ.get("VERCEL"):
        # Limit to 3 bots on Vercel to stay within the 10s execution limit
        try:
            run_sync(limit=3)
            return "Sync (limited) Completed on Vercel"
        except Exception as e:
            return f"Sync failed: {str(e)}", 500
    else:
        thread = threading.Thread(target=run_sync)
        thread.start()
        return "Sync Started in Background"

@app.route("/_debug")
def debug():
    return {
        "root_dir": root_dir,
        "current_dir": current_dir,
        "sys_path": sys.path,
        "env_keys": list(os.environ.keys()),
        "has_scraper": GitHubBotScraper is not None,
        "templates_exists": os.path.exists(os.path.join(root_dir, 'templates')),
        "templates_content": os.listdir(os.path.join(root_dir, 'templates')) if os.path.exists(os.path.join(root_dir, 'templates')) else []
    }

# Vercel needs 'app' or 'application' to be available at the module level
application = app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
