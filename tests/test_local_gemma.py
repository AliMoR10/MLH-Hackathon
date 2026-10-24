import base64

from google.genai import types

import gemma
import local_gemma


class _FakeHTTP:
    status_code = 200

    def __init__(self, answer):
        self._answer = answer

    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": self._answer}}


def test_ollama_backend_sends_text_and_images(monkeypatch):
    sent = {}

    def fake_post(url, json, timeout):
        sent.update(url=url, body=json)
        return _FakeHTTP("local answer")

    monkeypatch.setattr(local_gemma.requests, "post", fake_post)
    gemma.configure(backend="ollama")
    image = types.Part.from_bytes(data=b"png-bytes", mime_type="image/png")

    answer = gemma._ask(["Explain this error", image])

    assert answer == "local answer"
    assert sent["url"].endswith("/api/chat")
    user_msg = sent["body"]["messages"][-1]
    assert user_msg["content"] == "Explain this error"
    assert user_msg["images"] == [base64.b64encode(b"png-bytes").decode()]
    gemma.configure()


def test_local_chat_remembers_history(monkeypatch):
    monkeypatch.setattr(local_gemma.requests, "post", lambda url, json, timeout: _FakeHTTP(f"seen {len(json['messages'])}"))
    chat = local_gemma.LocalChat("system")
    chat.send_message("hi")
    assert chat.send_message("again").text == "seen 4"


def test_visitor_key_is_used(monkeypatch):
    made = []
    monkeypatch.setattr(gemma.genai, "Client", lambda api_key: made.append(api_key) or object())
    gemma.configure(api_key="visitor-key")
    gemma._get_client()
    assert made == ["visitor-key"]
    gemma.configure()
