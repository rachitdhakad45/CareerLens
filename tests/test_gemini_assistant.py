import pytest
import requests

from src.assistant.gemini import (
    CareerAssistantError,
    ask_career_assistant,
)


class FakeResponse:
    status_code = 200

    def json(self):
        return {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Build a small SQL project."}],
                },
            }],
        }


def test_gemini_response_is_returned_and_context_is_server_side(monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("src.assistant.gemini.requests.post", fake_post)

    answer = ask_career_assistant(
        "What should I learn next?",
        {"skills_not_found_in_resume": ["sql"]},
        api_key="test-key",
    )

    assert answer == "Build a small SQL project."
    assert "test-key" not in seen["url"]
    assert seen["headers"]["x-goog-api-key"] == "test-key"
    assert seen["timeout"] == 30
    assert seen["json"]["generationConfig"]["maxOutputTokens"] == 600
    assert seen["json"]["generationConfig"]["thinkingConfig"] == {
        "thinkingLevel": "minimal",
    }
    prompt = seen["json"]["contents"][-1]["parts"][0]["text"]
    assert "sql" in prompt
    assert "untrusted data" in prompt


def test_missing_key_is_rejected_without_request(monkeypatch):
    def unexpected_request(*args, **kwargs):
        raise AssertionError("request should not be made")

    monkeypatch.setattr(
        "src.assistant.gemini.requests.post", unexpected_request
    )

    with pytest.raises(CareerAssistantError, match="not configured"):
        ask_career_assistant("Question", {}, api_key="")


def test_http_failure_returns_safe_error(monkeypatch):
    class ErrorResponse:
        status_code = 403

    monkeypatch.setattr(
        "src.assistant.gemini.requests.post",
        lambda *args, **kwargs: ErrorResponse(),
    )

    with pytest.raises(CareerAssistantError, match="API key"):
        ask_career_assistant("Question", {}, api_key="test-key")


def test_timeout_is_translated_to_user_friendly_error(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout("secret request details")

    monkeypatch.setattr("src.assistant.gemini.requests.post", timeout)

    with pytest.raises(CareerAssistantError, match="timed out"):
        ask_career_assistant("Question", {}, api_key="test-key")


@pytest.mark.parametrize("question", ["", " " ])
def test_empty_question_is_rejected(question):
    with pytest.raises(ValueError, match="question"):
        ask_career_assistant(question, {}, api_key="test-key")


def test_oversized_context_is_rejected():
    with pytest.raises(ValueError, match="career context"):
        ask_career_assistant(
            "Question",
            {"evidence": "x" * 13_000},
            api_key="test-key",
        )
