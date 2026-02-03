import urllib.request
import urllib.parse
import urllib.error
import json
import os
import time
import base64
import re
import csv
from typing import List, Dict, Any
from pymongo import MongoClient

import google.generativeai as genai

class GitHubBotScraper:
    def __init__(self, github_token: str = None, gemini_api_key: str = None, mongo_uri: str = None):
        self.github_base_url = "https://api.github.com"
        
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

        self.github_headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Bot-Summary-App-v3"
        }
        if github_token:
            self.github_headers["Authorization"] = f"token {github_token}"
            
        self.gemini_api_key = gemini_api_key
        
        # MongoDB Initialization
        self.mongo_client = None
        self.db = None
        self.collection = None
        if mongo_uri:
            try:
                self.mongo_client = MongoClient(mongo_uri)
                # Using 'bot_directory' as DB name and 'bots' as collection
                self.db = self.mongo_client.get_database("bot_directory")
                self.collection = self.db.get_collection("bots")
                print("[+] Connected to MongoDB successfully.")
            except Exception as e:
                print(f"[!] MongoDB connection error: {e}")

    def _make_github_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Helper to make GET requests to GitHub using urllib."""
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url, headers=self.github_headers)
        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            if not str(e).endswith("404: Not Found"):
                print(f"[!] GitHub API error for {url}: {e}")
        return {}

    def get_gemini_summary(self, readme: str, description: str) -> Dict[str, str]:
        """Use Gemini API to get a summary and usage instructions."""
        if not self.model:
            return {"what_it_does": description, "how_to_use": "API Key missing.", "repo_type": "Unknown"}

        prompt = (
            "Analyze this GitHub repository and provide a summary in STRICT JSON format.\n"
            "Required keys: 'what_it_does', 'how_to_use', 'repo_type'.\n"
            "'repo_type' must be exactly either 'Library/Module' or 'Application/Bot'.\n"
            "Keep the values concise but informative.\n\n"
            f"Description: {description}\n\n"
            f"README Snippet:\n{readme[:5000]}"
        )

        try:
            # Sleep to avoid rate limits
            time.sleep(2.0) 
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r'^```(?:json)?\n', '', raw_text)
                raw_text = re.sub(r'\n```$', '', raw_text)
            
            # Attempt to find JSON object if there's surrounding text
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                # Basic cleanup for common AI JSON mistakes
                json_str = json_str.replace("'", '"')
                return json.loads(json_str)
                
        except Exception as e:
            print(f"    [!] Gemini AI Error: {e}")
            
        return {
            "what_it_does": description or "No description available", 
            "how_to_use": "Refer to the GitHub repository for installation and usage instructions.", 
            "repo_type": "Application/Bot"
        }

    def search_telegram_bots(self, query: str = "telegram bot", per_page: int = 10) -> List[Dict[str, Any]]:
        """Search for repositories matching the query."""
        url = f"{self.github_base_url}/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page}
        data = self._make_github_request(url, params)
        return data.get("items", [])

    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch content of a file from a repository."""
        url = f"{self.github_base_url}/repos/{owner}/{repo}/contents/{path}"
        data = self._make_github_request(url)
        if data and "content" in data:
            content_b64 = data["content"].replace("\n", "")
            try:
                return base64.b64decode(content_b64).decode("utf-8", errors="ignore")
            except:
                pass
        return ""

    def get_repo_type_heuristic(self, readme: str, name: str, description: str, language: str) -> str:
        """Fallback heuristic to identify repo type if AI fails."""
        text = f"{name} {description} {readme}".lower()
        
        lib_keywords = ["wrapper", "library", "api-client", "sdk", "framework", "for developers", "binding", "client for", "toolkit"]
        app_keywords = ["bot for", "ready to use", "run with", "deployment", "docker-compose", "self-hosted", "personal bot"]
        
        if any(k in text for k in lib_keywords): return "Library/Module"
        if any(k in text for k in app_keywords): return "Application/Bot"
            
        if language == "Python":
            if "setup.py" in readme or "pyproject.toml" in readme:
                return "Library/Module"
        
        return "Application/Bot"

    def process_bot(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single repository to extract and summarize info."""
        owner = repo["owner"]["login"]
        name = repo["name"]
        
        print(f"[*] Processing {owner}/{name}...")
        
        readme = self.get_file_content(owner, name, "README.md")
        if not readme:
            readme = self.get_file_content(owner, name, "readme.md")
            
        ai_summary = self.get_gemini_summary(readme, repo.get("description") or "")
        
        repo_type = ai_summary.get("repo_type")
        if not repo_type or repo_type == "Unknown":
            repo_type = self.get_repo_type_heuristic(readme, name, repo.get("description") or "", repo.get("language") or "")

        return {
            "name": name,
            "author": owner,
            "full_name": f"{owner}/{name}",
            "description": repo.get("description"),
            "link": repo.get("html_url"),
            "category": ", ".join(repo.get("topics", [])),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "forks": repo.get("forks_count"),
            "open_issues": repo.get("open_issues_count"),
            "last_updated": repo.get("updated_at"),
            "license": repo.get("license", {}).get("name") if repo.get("license") else "None",
            "repo_type": repo_type,
            "what_it_does": ai_summary.get("what_it_does") or repo.get("description"),
            "how_to_use": ai_summary.get("how_to_use") or "Refer to GitHub for setup instructions."
        }

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        if not data: return
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def save_to_mongodb(self, data: List[Dict[str, Any]]):
        if self.collection is None:
            return
        try:
            # We use name and author as a unique identifier to avoid duplicates
            for bot in data:
                self.collection.update_one(
                    {"full_name": bot["full_name"]},
                    {"$set": bot},
                    upsert=True
                )
            print("[+] Data synced to MongoDB.")
        except Exception as e:
            print(f"[!] Error saving to MongoDB: {e}")

    def run(self, output_base: str = "bots_data"):
        print("=== GitHub Bot Summary (AI & MongoDB Enhanced) ===")
        bots = self.search_telegram_bots()
        
        results = []
        for bot in bots:
            data = self.process_bot(bot)
            results.append(data)
            
            # Save progress locally (wrapped for read-only systems like Vercel)
            try:
                with open(f"{output_base}.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                self.save_to_csv(results, f"{output_base}.csv")
            except Exception as e:
                print(f"[*] Local file saving skipped (read-only filesystem): {e}")
            
            # Save to MongoDB
            self.save_to_mongodb(results)
            
            time.sleep(5.0) 
        
        print(f"\n[OK] Final results synced to MongoDB.")

def load_env():
    """Simple helper to load .env file manually."""
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

if __name__ == "__main__":
    env = load_env()
    scraper = GitHubBotScraper(
        github_token=env.get("GITHUB_TOKEN"),
        gemini_api_key=env.get("GEMINI_API_KEY"),
        mongo_uri=env.get("mdb") # Using the 'mdb' key from .env
    )
    scraper.run()