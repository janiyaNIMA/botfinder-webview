import os
import threading
import json
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

# Import our custom module
from scraper import GitHubBotScraper

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
load_dotenv()

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
    
    if collection is None:
        # Fallback to local file if DB fails
        try:
            local_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bots_data.json")
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
    def run_sync(limit=None):
        scraper = GitHubBotScraper(
            github_token=os.getenv("GITHUB_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            mongo_uri=MONGO_URI
        )
        scraper.run(limit=limit)

    # If running locally, we can do it in a thread. 
    # On Vercel, this route will just run the logic directly (blocking) or be used by a Cron.
    if os.environ.get("VERCEL"):
        # Limit to 3 bots on Vercel to stay within the 10s execution limit
        run_sync(limit=3)
        return "Sync (limited) Completed on Vercel"
    else:
        thread = threading.Thread(target=run_sync)
        thread.start()
        return "Sync Started in Background"

if __name__ == "__main__":
    # Local background sync on startup
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        scraper = GitHubBotScraper(
            github_token=os.getenv("GITHUB_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            mongo_uri=MONGO_URI
        )
        threading.Thread(target=scraper.run, daemon=True).start()
    
    app.run(debug=True, port=5000)
