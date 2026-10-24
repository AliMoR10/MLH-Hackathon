"""
local_gemma.py
Runs Gemma 4 on your own computer with Ollama (https://ollama.com): no API key, works offline.
Setup:  install Ollama, then run  `ollama pull gemma4`
"""
import base64
import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4")  # small default; gemma4:26b needs ~18 GB RAM


class _Reply:
    def __init__(self, text):
        self.text = text


def _to_message(contents):
    """Turn our prompt pieces (text and images) into one Ollama chat message."""
    if not isinstance(contents, list):
        contents = [contents]
    texts, images = [], []
    for part in contents:
        if isinstance(part, str):
            texts.append(part)
            continue
        data = getattr(getattr(part, "inline_data", None), "data", None)
        if data:
            images.append(base64.b64encode(data).decode())
        elif getattr(part, "text", None):
            texts.append(part.text)
    message = {"role": "user", "content": "\n\n".join(texts)}
    if images:
        message["images"] = images
    return message


def _chat(messages):
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"num_ctx": 16384},  # Ollama's default context is too small for repos
            },
            timeout=600,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Can't reach Ollama at {OLLAMA_URL}. Is the Ollama app running on this computer? "
            f"Install it from ollama.com, then run: ollama pull {OLLAMA_MODEL}"
        ) from None
    if r.status_code == 404:
        raise RuntimeError(f"Ollama doesn't have the model '{OLLAMA_MODEL}' yet. Run: ollama pull {OLLAMA_MODEL}")
    r.raise_for_status()
    return r.json()["message"]["content"]


def ask(system, contents):
    return _chat([{"role": "system", "content": system}, _to_message(contents)])


class LocalChat:
    """Same idea as the Gemini SDK chat: remembers the conversation history."""

    def __init__(self, system):
        self.messages = [{"role": "system", "content": system}]

    def send_message(self, question):
        self.messages.append({"role": "user", "content": question})
        answer = _chat(self.messages)
        self.messages.append({"role": "assistant", "content": answer})
        return _Reply(answer)
