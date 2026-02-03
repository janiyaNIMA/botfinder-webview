from flask import Flask, render_template, jsonify
import json
import os
import threading
from pymongo import MongoClient
from dotenv import load_dotenv

# Load main logic
from main import GitHubBotScraper

# Initialize Flask
app = Flask(__name__)

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("mdb")

DATA_FILE = "bots_data.json"

def sync_data():
    """Background task to sync GitHub data with MongoDB."""
    print("[*] Starting background data sync...")
    try:
        scraper = GitHubBotScraper(
            github_token=os.getenv("GITHUB_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            mongo_uri=MONGO_URI
        )
        # Search and update top bots
        scraper.run()
        print("[+] Background sync completed successfully.")
    except Exception as e:
        print(f"[!] Background sync failed: {e}")

def get_data():
    # Try fetching from MongoDB first
    if MONGO_URI:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client.get_database("bot_directory")
            collection = db.get_collection("bots")
            bots = list(collection.find({}, {'_id': 0}).sort("stars", -1))
            if bots:
                print(f"[+] Retrieved {len(bots)} bots from MongoDB.")
                return bots
        except Exception as e:
            print(f"[!] MongoDB Error in app: {e}. Falling back to local file.")

    # Fallback to local JSON file
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

@app.route("/")
def index():
    bots = get_data()
    return render_template("index.html", bots=bots)

if __name__ == "__main__":
    # Start the sync in a background thread so it doesn't block the web app
    # Only start if not in the reloader thread to avoid double-syncing in debug mode
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        sync_thread = threading.Thread(target=sync_data, daemon=True)
        sync_thread.start()
    
    # Run Flask
    print("[*] Starting Flask server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
