"""GitHub API service layer — handles all HTTP communication."""

import requests
from typing import Optional

BASE_URL = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}


def _get(url: str, token: Optional[str] = None, params: dict = None) -> dict | list:
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_user(username: str, token: Optional[str] = None) -> dict:
    return _get(f"{BASE_URL}/users/{username}", token)


def fetch_repos(username: str, token: Optional[str] = None) -> list[dict]:
    results = []
    page = 1
    while True:
        page_data = _get(
            f"{BASE_URL}/users/{username}/repos",
            token,
            params={"per_page": 100, "page": page, "sort": "updated"},
        )
        if not page_data:
            break
        results.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1
    return results


def fetch_commit_activity(owner: str, repo: str, token: Optional[str] = None) -> list[dict]:
    """Returns weekly commit counts for the last 52 weeks."""
    try:
        data = _get(f"{BASE_URL}/repos/{owner}/{repo}/stats/commit_activity", token)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def fetch_languages(owner: str, repo: str, token: Optional[str] = None) -> dict:
    try:
        return _get(f"{BASE_URL}/repos/{owner}/{repo}/languages", token)
    except Exception:
        return {}
