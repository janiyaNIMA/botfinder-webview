import sys
import os
from flask import Flask, render_template, request
from pymongo import MongoClient
from dotenv import load_dotenv

# Add the root directory to sys.path so we can import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import GitHubBotScraper

# Initialize Flask with absolute path for templates
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

load_dotenv()
MONGO_URI = os.getenv("mdb")

def get_data():
    if MONGO_URI:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client.get_database("bot_directory")
            collection = db.get_collection("bots")
            bots = list(collection.find({}, {'_id': 0}).sort("stars", -1))
            return bots
        except Exception as e:
            print(f"DB Error: {e}")
    return []

@app.route("/")
def index():
    bots = get_data()
    return render_template("index.html", bots=bots)

@app.route("/sync")
def trigger_sync():
    """Endpoint to trigger the scraper (e.g. via CRON or manual request)"""
    try:
        scraper = GitHubBotScraper(
            github_token=os.getenv("GITHUB_TOKEN"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            mongo_uri=MONGO_URI
        )
        scraper.run()
        return "Sync completed successfully"
    except Exception as e:
        return f"Sync failed: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
