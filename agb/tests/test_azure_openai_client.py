from ab.core.azure_openai_client import AzureOpenAIClient


def test_chat_uses_fresh_bearer_token_without_logging_it(monkeypatch, caplog):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "answer"}}]}

    def post(url, **kwargs):
        captured.update(kwargs)
        return Response()

    client = AzureOpenAIClient(
        endpoint="https://resource.openai.azure.com",
        deployment="deployment",
    )
    monkeypatch.setattr(client, "_token", lambda: "fixture-bearer-value")
    monkeypatch.setattr("requests.post", post)

    assert client.generate("question") == "answer"
    assert captured["headers"]["Authorization"] == "Bearer fixture-bearer-value"
    assert "fixture-bearer-value" not in caplog.text
