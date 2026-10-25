
"""Fetch published jobs from a Greenhouse job board."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseAPIError(RuntimeError):
    """Raised when the Greenhouse API request fails."""


def fetch_greenhouse_jobs(board_token: str, timeout: int = 15) -> list[dict]:
    """Fetch currently published jobs from one Greenhouse board.

    Returns the raw job records supplied by Greenhouse.
    Does not store listings or claim that a job is eligible for a candidate.
    """
    if not isinstance(board_token, str) or not board_token.strip():
        raise ValueError("board_token must be a non-empty string.")

    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ValueError("timeout must be a positive integer.")

    token = quote(board_token.strip(), safe="")
    url = f"{GREENHOUSE_API}/{token}/jobs?content=true"
    request = Request(
        url,
        headers={"User-Agent": "CareerLens/1.0"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise GreenhouseAPIError(
            f"Greenhouse returned HTTP {exc.code} for board '{board_token}'."
        ) from exc
    except URLError as exc:
        raise GreenhouseAPIError(
            f"Could not connect to Greenhouse: {exc.reason}"
        ) from exc
    except (TimeoutError, OSError) as exc:
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
