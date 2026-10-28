
"""Fetch published jobs from a Greenhouse job board."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseAPIError(RuntimeError):
    """Raised when the Greenhouse API request fails."""


def fetch_greenhouse_jobs(
    board_token: str,
    timeout: int = 15,
    max_attempts: int = 3,
    retry_backoff_seconds: float = 0.5,
) -> list[dict]:
    """Fetch currently published jobs from one Greenhouse board.

    Returns the raw job records supplied by Greenhouse.
    Does not store listings or claim that a job is eligible for a candidate.
    """
    if not isinstance(board_token, str) or not board_token.strip():
        raise ValueError("board_token must be a non-empty string.")

    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("timeout must be a positive integer.")

    if (
        not isinstance(max_attempts, int)
        or isinstance(max_attempts, bool)
        or max_attempts < 1
    ):
        raise ValueError("max_attempts must be a positive integer.")

    if (
        not isinstance(retry_backoff_seconds, (int, float))
        or isinstance(retry_backoff_seconds, bool)
        or retry_backoff_seconds < 0
    ):
        raise ValueError("retry_backoff_seconds must be non-negative.")

    token = quote(board_token.strip(), safe="")
    url = f"{GREENHOUSE_API}/{token}/jobs?content=true"
    request = Request(
        url,
        headers={"User-Agent": "CareerLens/1.0"},
        method="GET",
    )

    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and attempt < max_attempts:
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))
                continue
            raise GreenhouseAPIError(
                f"Greenhouse returned HTTP {exc.code} for board '{board_token}'."
            ) from exc
        except URLError as exc:
            if attempt < max_attempts:
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))
                continue
            raise GreenhouseAPIError(
                f"Could not connect to Greenhouse: {exc.reason}"
            ) from exc
        except (TimeoutError, OSError) as exc:
            if attempt < max_attempts:
                time.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))
                continue
            raise GreenhouseAPIError(
                f"Greenhouse request failed: {exc}"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GreenhouseAPIError(
                "Greenhouse returned an invalid response."
            ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise GreenhouseAPIError(
            "Greenhouse response did not contain a valid jobs list."
        )

    return payload["jobs"]
