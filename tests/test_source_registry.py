
import csv

import pytest

from src.recommendations.source_registry import (
    get_enabled_sources,
    load_opportunity_sources,
)


COLUMNS = [
    "source_id",
    "company",
    "platform",
    "board_identifier",
    "enabled",
    "last_synced_at",
]


def write_registry(path, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_source(source_id="GH-001", enabled="true", platform="greenhouse"):
    return {
        "source_id": source_id,
        "company": "Example Company",
        "platform": platform,
        "board_identifier": "example-board",
        "enabled": enabled,
        "last_synced_at": "",
    }


def test_empty_registry_returns_empty_list(tmp_path):
    path = write_registry(tmp_path / "sources.csv", [])
    assert load_opportunity_sources(path) == []


def test_enabled_sources_are_normalized(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [make_source(enabled="TRUE")],
    )

    sources = get_enabled_sources(path)

    assert len(sources) == 1
    assert sources[0]["enabled"] is True
    assert sources[0]["platform"] == "greenhouse"


def test_disabled_source_is_not_returned(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [make_source(enabled="false")],
    )

    assert get_enabled_sources(path) == []


def test_platform_filter(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [
            make_source("GH-001", platform="greenhouse"),
            make_source("LV-001", platform="lever"),
        ],
    )

    sources = get_enabled_sources(path, platform="lever")

    assert len(sources) == 1
    assert sources[0]["source_id"] == "LV-001"


def test_duplicate_source_ids_are_rejected(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [
            make_source("GH-001"),
            make_source("GH-001"),
        ],
    )

    with pytest.raises(ValueError, match="Duplicate source_id"):
        load_opportunity_sources(path)


def test_invalid_enabled_value_is_rejected(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [make_source(enabled="sometimes")],
    )

    with pytest.raises(ValueError, match="Invalid enabled value"):
        load_opportunity_sources(path)


def test_unsupported_platform_is_rejected(tmp_path):
    path = write_registry(
        tmp_path / "sources.csv",
        [make_source(platform="unknown-platform")],
    )

    with pytest.raises(ValueError, match="Unsupported platform"):
        load_opportunity_sources(path)


def test_enabled_source_requires_board_identifier(tmp_path):
    source = make_source()
    source["board_identifier"] = ""

    path = write_registry(tmp_path / "sources.csv", [source])

    with pytest.raises(ValueError, match="board_identifier"):
        load_opportunity_sources(path)


def test_missing_registry_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_opportunity_sources(tmp_path / "missing.csv")
