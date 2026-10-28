
import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from src.recommendations.source_connectors.greenhouse import (
    GreenhouseAPIError,
    fetch_greenhouse_jobs,
)


def mock_response(payload):
    return BytesIO(json.dumps(payload).encode("utf-8"))


def test_fetch_greenhouse_jobs_returns_jobs():
    payload = {
        "jobs": [
            {"id": 123, "title": "Software Engineer Intern"},
            {"id": 456, "title": "Data Analyst Intern"},
        ]
    }

    with patch(
        "src.recommendations.source_connectors.greenhouse.urlopen",
        return_value=mock_response(payload),
    ):
        jobs = fetch_greenhouse_jobs("example-board")

    assert len(jobs) == 2
    assert jobs[0]["id"] == 123
    assert jobs[1]["title"] == "Data Analyst Intern"


def test_empty_board_token_is_rejected():
    with pytest.raises(ValueError, match="board_token"):
        fetch_greenhouse_jobs("  ")


def test_invalid_timeout_is_rejected():
    with pytest.raises(ValueError, match="timeout"):
        fetch_greenhouse_jobs("example-board", timeout=0)


def test_http_error_is_reported():
    error = HTTPError(
        url="https://example.com",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None,
    )

    with patch(
        "src.recommendations.source_connectors.greenhouse.urlopen",
        side_effect=error,
    ):
        with pytest.raises(GreenhouseAPIError, match="HTTP 404"):
            fetch_greenhouse_jobs("missing-board")


def test_network_error_is_reported():
    with patch(
        "src.recommendations.source_connectors.greenhouse.urlopen",
        side_effect=URLError("connection failed"),
    ):
        with pytest.raises(GreenhouseAPIError, match="Could not connect"):
            fetch_greenhouse_jobs("example-board")


def test_temporary_server_error_is_retried(monkeypatch):
    error = HTTPError(
        url="https://example.com",
        code=503,
        msg="Service Unavailable",
        hdrs=None,
        fp=None,
    )
    response = mock_response({"jobs": [{"id": 789}]})
    calls = []

    def request(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise error
        return response

    monkeypatch.setattr(
        "src.recommendations.source_connectors.greenhouse.urlopen", request
    )
    monkeypatch.setattr(
        "src.recommendations.source_connectors.greenhouse.time.sleep",
        lambda delay: None,
    )

    assert fetch_greenhouse_jobs("example-board") == [{"id": 789}]
    assert len(calls) == 2


def test_not_found_error_is_not_retried(monkeypatch):
    error = HTTPError(
        url="https://example.com",
        code=404,
        msg="Not Found",
        hdrs=None,
        fp=None,
    )
    calls = []

    def request(*args, **kwargs):
        calls.append(1)
        raise error

    monkeypatch.setattr(
        "src.recommendations.source_connectors.greenhouse.urlopen", request
    )
    monkeypatch.setattr(
        "src.recommendations.source_connectors.greenhouse.time.sleep",
        lambda delay: None,
    )

    with pytest.raises(GreenhouseAPIError, match="HTTP 404"):
        fetch_greenhouse_jobs("example-board")

    assert len(calls) == 1


def test_invalid_retry_configuration_is_rejected():
    with pytest.raises(ValueError, match="max_attempts"):
        fetch_greenhouse_jobs("example-board", max_attempts=0)


def test_invalid_response_is_rejected():
    with patch(
        "src.recommendations.source_connectors.greenhouse.urlopen",
        return_value=mock_response({"unexpected": []}),
    ):
        with pytest.raises(GreenhouseAPIError, match="valid jobs list"):
            fetch_greenhouse_jobs("example-board")
