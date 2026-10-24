"""
gemma.py  —  OWNER: Daria
All the Gemma 4 calls live here. Improve the prompts to make answers better!
Docs: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api
"""
import io
import os

from google import genai
from google.genai import types

MODEL = "gemma-4-26b-a4b-it"  # Gemma 4 via the Gemini API (also available: gemma-4-31b-it)

MENTOR = (
    "You are First PR Buddy, a friendly open-source mentor for complete beginners. "
    "Use simple English, short paragraphs and bullet points. Never invent files that "
    "are not in the file list you are given."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Missing GEMINI_API_KEY. Put it in your .env file.")
        _client = genai.Client(api_key=key)
    return _client


def _ask(contents, think=False):
    """think=True turns on Gemma 4's thinking mode: slower, but better reasoning."""
    resp = _get_client().models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=MENTOR,
            thinking_config=types.ThinkingConfig(thinking_level="high" if think else "minimal"),
        ),
    )
    return resp.text


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

Answer with these sections:
## What this project does (2-3 sentences)
## How the code is organised (the important folders/files and what they're for)
## How to run it locally (based on the README)
"""
    return _ask(prompt)


def plan_for_issue(info, files, issue):
    prompt = f"""A beginner wants to fix this issue.

{_repo_context(info, files)}

Issue #{issue['number']}: {issue['title']}
Labels: {', '.join(issue['labels'])}
Description:
{issue['body']}

Answer with these sections:
## Difficulty: Easy / Medium / Hard (one line why)
## What the issue is asking for (plain English)
## Files to look at first
## Step-by-step plan (numbered)
## How to submit the pull request (fork, branch, commit, PR, with example git commands)
"""
    return _ask(prompt, think=True)  # planning benefits from thinking mode


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
        "words what went wrong, and give clear steps to fix it."
    )
    return _ask([_image_part(image_bytes, mime_type), prompt], think=True)


def start_chat(info, readme, files):
    """A multi-turn chat about one repo. The SDK remembers the conversation history."""
    chat = _get_client().chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=MENTOR
            + "\n\nYou are helping with this repository:\n"
            + _repo_context(info, files)
            + "\n\nREADME:\n"
            + readme
        ),
    )
    return chat


def ask_chat(chat, question):
    return chat.send_message(question).text
