# Smart API Data Analyzer

🚀 **Live Demo:** [smadarr.streamlit.app](https://smadarr.streamlit.app)

A production-ready dual-mode data analyzer built with Python and Streamlit — GitHub profile intelligence + Weather forecast dashboard.

## Features

- Fetch and analyze any GitHub user's public repositories
- Language breakdown (by repo count and byte usage)
- Commit activity trends over the last 52 weeks
- Stars vs Forks scatter analysis
- Activity score ranking
- AI-style insight summary
- TTL caching to respect API rate limits

## Setup

### 1. Clone and install dependencies

```bash
cd smart-api-analyzer
pip install -r requirements.txt
```

### 2. (Optional) Set GitHub token

A token increases your rate limit from 60 to 5,000 requests/hour.

```bash
cp .env.example .env
# Edit .env and add your token
```

You can also paste the token directly in the app's sidebar — no file needed.

### 3. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## API Usage Guide

The app uses the following GitHub REST API endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /users/{username}` | User profile |
| `GET /users/{username}/repos` | Repository list |
| `GET /repos/{owner}/{repo}/languages` | Language byte counts |
| `GET /repos/{owner}/{repo}/stats/commit_activity` | Weekly commit stats |

All requests are cached for 5 minutes in-memory.

## Deployment

### Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the entry point
4. Add `GITHUB_TOKEN` as a secret in the Streamlit Cloud dashboard

### Render

1. Create a new Web Service on [render.com](https://render.com)
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add `GITHUB_TOKEN` as an environment variable

## Project Structure

```
smart-api-analyzer/
├── app.py                  # Streamlit UI entry point
├── requirements.txt
├── .env.example
├── api/
│   └── github_client.py    # GitHub API service layer
├── processing/
│   └── data_processor.py   # Data cleaning + insight generation
├── utils/
│   └── cache.py            # TTL cache decorator
└── visualization/
    └── charts.py           # Plotly chart builders
```
