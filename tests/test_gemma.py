import gemma


class _FakeResponse:
    text = "fake answer"


class _FakeModels:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse()


class _FakeClient:
    models = _FakeModels()


def test_summarize_repo_uses_gemma_4(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(gemma, "_get_client", lambda: fake)
    info = {"name": "owner/repo", "language": "Python", "description": "demo"}

    answer = gemma.summarize_repo(info, "README text", ["app.py"])

    assert answer == "fake answer"
    assert fake.models.kwargs["model"].startswith("gemma-4")


def test_retries_temporary_500_errors(monkeypatch):
    from google.genai import errors

    calls = []

    class FlakyModels:
        def generate_content(self, **kwargs):
            level = kwargs["config"].thinking_config.thinking_level
            calls.append(str(getattr(level, "value", level)).lower())
            if len(calls) < 3:
                raise errors.ServerError(500, {"error": {"code": 500, "message": "Internal error", "status": "INTERNAL"}})
            return _FakeResponse()

    class FlakyClient:
        models = FlakyModels()

    monkeypatch.setattr(gemma, "_get_client", lambda: FlakyClient())
    monkeypatch.setattr(gemma.time, "sleep", lambda seconds: None)
    gemma.configure()

    assert gemma._ask("hi", think=True) == "fake answer"
    assert calls == ["high", "high", "minimal"]  # third try drops thinking to make the request lighter


def test_does_not_retry_bad_key_errors(monkeypatch):
    import pytest
    from google.genai import errors

    calls = []

    class BadKeyModels:
        def generate_content(self, **kwargs):
            calls.append(1)
            raise errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}})

    class BadKeyClient:
        models = BadKeyModels()

    monkeypatch.setattr(gemma, "_get_client", lambda: BadKeyClient())
    gemma.configure()

    with pytest.raises(errors.ClientError):
        gemma._ask("hi")
    assert len(calls) == 1
