# GitHub Telegram Bot Summary

A web application that discovers and summarizes Telegram bots from GitHub repositories. It uses AI to analyze bot descriptions and README files to provide clear summaries of what each bot does and how to use it.

## Features

- **Automated Discovery**: Searches GitHub for Telegram bot repositories
- **AI-Powered Summaries**: Uses Google Gemini AI to generate concise summaries and usage instructions
- **Web Interface**: Clean, modern web UI to browse discovered bots
- **Data Storage**: Supports both MongoDB and local JSON file storage
- **Background Sync**: Automatically updates bot data in the background

## Technologies Used

- **Backend**: Python Flask
- **AI**: Google Generative AI (Gemini)
- **Database**: MongoDB (optional, falls back to JSON)
- **Frontend**: HTML/CSS/JavaScript
- **APIs**: GitHub API

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/janiyaNIMA/botfinder-webview.git
   cd botfinder-webview
   ```

2. Create a virtual environment:
   ```bash
   python -m venv _venv
   _venv\Scripts\activate  # On Windows
   # or
   source _venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   GITHUB_TOKEN=your_github_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   MDB=mongodb://localhost:27017  # Optional, for MongoDB storage
   ```

## Configuration

### Required Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token for API access (recommended for higher rate limits)
- `GEMINI_API_KEY`: Google AI API key for generating summaries

### Optional Environment Variables

- `MDB`: MongoDB connection URI. If not provided, the app will use local JSON file storage.

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:5000`

3. The app will automatically start syncing bot data in the background. The web interface will display the discovered bots with their summaries.

## How It Works

1. **Search**: Queries GitHub API for repositories containing "telegram bot"
2. **Analyze**: Fetches README and description for each repository
3. **Summarize**: Uses Gemini AI to generate structured summaries including:
   - What the bot does
   - How to use it
   - Repository type (Library/Module or Application/Bot)
4. **Store**: Saves data to MongoDB or local JSON file
5. **Display**: Web interface shows sorted list of bots by stars

## Project Structure

```
├── app.py              # Flask web application
├── main.py             # Core bot scraping and AI logic
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web interface template
├── bots_data.json      # Local data storage (fallback)
├── bots_data.csv       # CSV export (optional)
└── _venv/              # Virtual environment (ignored)
```

## API Keys Setup

### GitHub Token
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` scope
3. Add to `.env` as `GITHUB_TOKEN`

### Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` as `GEMINI_API_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check individual repository licenses for any included code.