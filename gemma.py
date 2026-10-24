"""
gemma.py  —  OWNER: Daria
All the Gemma 4 calls live here. Improve the prompts to make answers better!
Docs: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api
"""
import io
import os
import re
import threading
import time

import requests
from google import genai
from google.genai import errors, types

import local_gemma

MODEL = "gemma-4-26b-a4b-it"  # Gemma 4 via the Gemini API (also available: gemma-4-31b-it)

MENTOR = (
    "You are First PR Buddy, a friendly open-source mentor for complete beginners. "
    "Use simple English, short paragraphs and bullet points. Never invent files that "
    "are not in the file list you are given."
)

_clients = {}  # one Gemini client per API key
_settings = threading.local()  # per-visitor settings, so visitors never share keys


def configure(api_key=None, backend="gemini"):
    """Called by app.py on every page run. backend: "gemini" (cloud) or "ollama" (this computer)."""
    _settings.api_key = api_key
    _settings.backend = backend


def _backend():
    return getattr(_settings, "backend", None) or os.getenv("GEMMA_BACKEND", "gemini")


def _get_client():
    key = getattr(_settings, "api_key", None) or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Missing GEMINI_API_KEY. Add it in the sidebar or in your .env file.")
    if key not in _clients:
        _clients[key] = genai.Client(api_key=key)
    return _clients[key]


RETRY_CODES = {500, 502, 503, 504}  # temporary errors on Google's side
RETRY_WAITS = [2, 5, 10]  # seconds to wait before each retry


def _with_retries(call):
    """Run call(attempt). If Google returns a temporary 5xx error, wait and try again."""
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            return call(attempt)
        except errors.APIError as e:
            if e.code not in RETRY_CODES or attempt == len(RETRY_WAITS):
                raise
            time.sleep(RETRY_WAITS[attempt])


def _ask(contents, think=False):
    """think=True turns on Gemma 4's thinking mode: slower, but better reasoning."""
    if _backend() == "ollama":
        return local_gemma.ask(MENTOR, contents)

    def call(attempt):
        # If the first tries fail, switch thinking off: a smaller, faster request fails less often.
        level = "high" if think and attempt < 2 else "minimal"
        resp = _get_client().models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=MENTOR,
                thinking_config=types.ThinkingConfig(thinking_level=level),
            ),
        )
        return resp.text

    return _with_retries(call)


def _repo_context(info, files):
    return (
        f"Repo: {info['name']}  |  Main language: {info['language']}\n"
        f"Description: {info['description']}\n\n"
        "Files (partial list):\n" + "\n".join(files)
    )


def summarize_repo(info, readme, files):
    prompt = f"""Explain this project to a beginner who wants to make their first contribution.

{_repo_context(info, files)}

README:
{readme}

<constraints>
- You MUST review every single root folder and top-level file provided in the file list.
- DO NOT summarize, skip, or gloss over any root folder.
- Provide a short sentence explanation for EVERY root folder present in the file list.
</constraints>

Answer with these exact sections:
## What this project does (2-3 sentences)
## How the code is organised (the important folders/files and what they're for)
## How to run it locally (based on the README)
"""
    return _ask(prompt, think=True)

def _extract_image_urls(text: str) -> list[str]:
    """Extracts markdown and HTML image URLs from issue text."""
    if not text:
        return []
    markdown_pattern = r'!\[.*?\]\((https?://[^\s)]+)\)'
    html_pattern = r'<img[^>]+src=["\'](https?://[^"\']+)["\']'
    markdown_images = re.findall(markdown_pattern, text)
    html_images = re.findall(html_pattern, text)
    return list(dict.fromkeys(markdown_images + html_images))


def _download_github_image(url: str) -> tuple[bytes | None, str]:
    """Downloads an image using GitHub token if private, returning bytes and mime type."""
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"} if token else {}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            mime_type = response.headers.get("Content-Type", "image/jpeg")
            return response.content, mime_type
    except Exception as e:
        print(f"Failed to download issue image {url}: {e}")
    return None, "image/jpeg"

def plan_for_issue(info, files, issue):
    body = issue.get('body', '') or ''
    image_urls = _extract_image_urls(body)

    # Base text prompt
    prompt = f"""A beginner wants to fix this issue.

{_repo_context(info, files)}

Issue #{issue['number']}: {issue['title']}
Labels: {', '.join(issue['labels'])}
Description:
{body}

RULES for answering the sections:
 * DO NOT include in the response, anything inside of brackets, inclusive. The text in brackets is only to help you understand the instructions of your task
Sections to answer:
## Difficulty: Easy / Medium / Hard (one line why)
## What the issue is asking for (plain English)
## Files to look at first
## Step-by-step plan (numbered)
## How to submit the pull request (fork, branch, commit, PR, with example git commands)
"""

    contents = [prompt]

    # FREE TIER OPTIMIZATION: Only grab the first image to prevent 429 token limit exhaustion
    if image_urls:
        img_bytes, mime_type = _download_github_image(image_urls[0])
        if img_bytes:
            contents.append(_image_part(img_bytes, mime_type))

    return _ask(contents, think=True)


def _image_part(image_bytes, mime_type):
    """Send the image inline; if that fails, upload it (the method shown in the official docs)."""
    try:
        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    except Exception:
        return _get_client().files.upload(
            file=io.BytesIO(image_bytes), config=types.UploadFileConfig(mime_type=mime_type)
        )


def explain_screenshot(image_bytes, mime_type, info=None):
    context = f" while working on {info['name']}" if info else ""
    prompt = (
        f"A beginner got this error{context}. Read the screenshot, explain in simple "
        "words what went wrong, and give clear steps to fix it, and an explanation at the end, explaining how you fixed it."
    )
    return _ask([_image_part(image_bytes, mime_type), prompt], think=True)


def start_chat(info, readme, files):
    """A multi-turn chat about one repo. The SDK remembers the conversation history."""
    system = MENTOR + "\n\nYou are helping with this repository:\n" + _repo_context(info, files) + "\n\nREADME:\n" + readme
    if _backend() == "ollama":
        return local_gemma.LocalChat(system)
    return _get_client().chats.create(model=MODEL, config=types.GenerateContentConfig(system_instruction=system))


def ask_chat(chat, question):
    return _with_retries(lambda attempt: chat.send_message(question).text)
