"""
github_api.py  —  OWNER: Crazygamer212
Fetches everything we need about a repo from the GitHub API.
No AI here, just data.
"""
import os
import re

import requests

API = "https://api.github.com"


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")  # optional, but raises rate limit from 60 to 5000 requests/hour
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def parse_repo_url(url: str):
    """'https://github.com/owner/repo' -> ('owner', 'repo')"""
    m = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", url.strip())
    if not m:
        raise ValueError("That doesn't look like a GitHub repo link.")
    return m.group(1), m.group(2).removesuffix(".git")


def get_repo_info(owner, repo):
    r = requests.get(f"{API}/repos/{owner}/{repo}", headers=_headers(), timeout=15)
    if r.status_code == 404:
        raise ValueError("Repo not found (is it public?).")
    if r.status_code == 403:
        raise RuntimeError("GitHub rate limit hit. Add a GITHUB_TOKEN to your .env file.")
    r.raise_for_status()
    d = r.json()
    return {
        "name": d["full_name"],
        "description": d.get("description") or "",
        "language": d.get("language") or "Unknown",
        "stars": d.get("stargazers_count", 0),
        "default_branch": d.get("default_branch", "main"),
        "url": d["html_url"],
    }


def get_readme(owner, repo, max_chars=8000):
    h = _headers() | {"Accept": "application/vnd.github.raw"}
    r = requests.get(f"{API}/repos/{owner}/{repo}/readme", headers=h, timeout=15)
    if r.status_code != 200:
        return "(No README found)"
    return r.text[:max_chars]


def get_file_tree(owner, repo, branch, max_files=200):
    r = requests.get(
        f"{API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=_headers(), timeout=15,
    )
    if r.status_code != 200:
        return []
    paths = [item["path"] for item in r.json().get("tree", []) if item["type"] == "blob"]
    skip = ("node_modules/", ".git/", "dist/", "build/", "vendor/", ".github/", "venv", ".venv")
    paths = [p for p in paths if not p.startswith(skip)]
    return paths[:max_files]


def get_beginner_issues(owner, repo, limit=10):
    """Open issues labelled 'good first issue', falling back to 'help wanted'."""
    
    r = requests.get(
        f"{API}/repos/{owner}/{repo}/issues",
        headers=_headers(),
        params={"state": "open", "per_page": limit},
        timeout=15,
    )

    issues = [i for i in r.json() if "pull_request" not in i]  # skip PRs
    if issues:
        return [
            {
                "number": i["number"],
                "title": i["title"],
                "body": (i.get("body") or "")[:3000],
                "url": i["html_url"],
                "labels": [lbl["name"] for lbl in i.get("labels", [])],
            }
            for i in issues
        ]
    return []
