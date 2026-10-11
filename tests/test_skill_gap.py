import pytest

from src.recommendations.skill_gap import analyze_skill_gap


def test_data_analytics_gap_analysis():
    resume = """
    Technical Skills
    Python, SQL, Pandas, NumPy, Statistics
    """

    result = analyze_skill_gap(
        resume,
        "Data & Analytics",
    )

    assert result["career_family"] == "Data & Analytics"
    assert result["total_required"] > 0
    assert result["coverage_score"] > 0
    assert result["missing_count"] > 0


def test_empty_resume_is_rejected():
    with pytest.raises(ValueError, match="Resume text cannot be empty"):
        analyze_skill_gap("", "Data & Analytics")


def test_unknown_career_family_is_rejected():
    with pytest.raises(ValueError, match="Unsupported career family"):
        analyze_skill_gap("Python SQL", "Unknown Career")


def test_coverage_score_is_bounded():
    result = analyze_skill_gap(
        "Python SQL Pandas NumPy Statistics Tableau Power BI",
        "Data & Analytics",
    )

    assert 0 <= result["coverage_score"] <= 100

def test_all_required_skills_produce_full_coverage():
    resume = """
    Technical Skills
    Python, SQL, Pandas, NumPy, EDA, Statistics,
    Tableau, Power BI, Data Visualization, MySQL, PostgreSQL
    """

    result = analyze_skill_gap(
        resume,
        "Data & Analytics",
    )

    assert result["coverage_score"] == 100.0
    assert result["missing_count"] == 0


def test_no_detected_skills_produce_zero_coverage():
    resume = """
    I enjoy learning, teamwork, reading, and helping others.
    """

    result = analyze_skill_gap(
        resume,
        "Data & Analytics",
    )

    assert result["coverage_score"] == 0.0
    assert result["covered_count"] == 0
    assert result["mention_only_count"] == 0
    assert result["missing_count"] == result["total_required"]

def test_skill_counts_are_consistent():
    resume = """
    Technical Skills
    Python, SQL, Pandas
    """

    result = analyze_skill_gap(
        resume,
        "Data & Analytics",
    )

    classified_count = (
        result["covered_count"]
        + result["mention_only_count"]
        + result["missing_count"]
    )

    assert classified_count == result["total_required"]


def test_missing_skills_include_priority():
    result = analyze_skill_gap(
        "Python SQL",
        "Data & Analytics",
    )

    missing = result["missing_skills"]

    assert missing

    for skill in missing:
        assert skill["priority"] in {
            "high",
            "medium",
            "low",
        }


def test_missing_skills_are_sorted_by_priority():
    result = analyze_skill_gap(
        "I enjoy learning new things.",
        "Data & Analytics",
    )

    missing = result["missing_skills"]

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    actual_order = [
        priority_order[skill["priority"]]
        for skill in missing
    ]

    assert actual_order == sorted(actual_order)