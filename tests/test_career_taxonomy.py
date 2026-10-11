from src.ml.career_taxonomy import load_career_taxonomy


def test_load_career_taxonomy():
    taxonomy = load_career_taxonomy()

    assert len(taxonomy) > 0

    assert {
        "domain",
        "career_family",
        "career",
    }.issubset(taxonomy[0].keys())

    assert all(row["domain"] for row in taxonomy)
    assert all(row["career_family"] for row in taxonomy)
    assert all(row["career"] for row in taxonomy)


def test_career_taxonomy_contains_multiple_domains():
    taxonomy = load_career_taxonomy()

    domains = {
        row["domain"]
        for row in taxonomy
    }

    assert len(domains) >= 10


def test_career_taxonomy_contains_multiple_career_families():
    taxonomy = load_career_taxonomy()

    career_families = {
        row["career_family"]
        for row in taxonomy
    }

    assert len(career_families) >= 15