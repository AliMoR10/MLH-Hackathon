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
    monkeypatch.setattr(gemma, "_client", fake)
    info = {"name": "owner/repo", "language": "Python", "description": "demo"}

    answer = gemma.summarize_repo(info, "README text", ["app.py"])

    assert answer == "fake answer"
    assert fake.models.kwargs["model"].startswith("gemma-4")
