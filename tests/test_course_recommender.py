
import csv

import pytest

from src.recommendations.course_recommender import (
    load_course_catalog,
    recommend_courses,
)


COLUMNS = [
    "course_id",
    "title",
    "provider",
    "url",
    "skills",
    "career_families",
    "level",
    "price",
    "duration",
    "description",
]


def create_test_catalog(path):
    courses = [
        {
            "course_id": "PY-001",
            "title": "Python Basics",
            "provider": "Test Provider",
            "url": "https://example.com/python",
            "skills": "python",
            "career_families": "Data & Analytics",
            "level": "Beginner",
            "price": "Free",
            "duration": "",
            "description": "Learn Python.",
        },
        {
            "course_id": "SQL-001",
            "title": "SQL Fundamentals",
            "provider": "Test Provider",
            "url": "https://example.com/sql",
            "skills": "sql",
            "career_families": "Data & Analytics",
            "level": "Beginner",
            "price": "Free",
            "duration": "",
            "description": "Learn SQL.",
        },
        {
            "course_id": "VIS-001",
            "title": "Data Visualization",
            "provider": "Test Provider",
            "url": "https://example.com/visualization",
            "skills": "data visualization",
            "career_families": "Data & Analytics",
            "level": "Beginner",
            "price": "Free",
            "duration": "",
            "description": "Learn visualization.",
        },
        {
            "course_id": "DES-001",
            "title": "Design Basics",
            "provider": "Test Provider",
            "url": "https://example.com/design",
            "skills": "figma",
            "career_families": "UI/UX & Product Design",
            "level": "Beginner",
            "price": "Free",
            "duration": "",
            "description": "Learn Figma.",
        },
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(courses)

    return path


def test_load_course_catalog(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "courses.csv"
    )

    courses = load_course_catalog(catalog_path)

    assert len(courses) == 4
    assert courses[0]["title"] == "Python Basics"


def test_missing_catalog_file_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_course_catalog(tmp_path / "missing.csv")


def test_courses_are_ranked_by_missing_skill_priority(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "courses.csv"
    )

    result = recommend_courses(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
    )

    titles = [course["title"] for course in result]

    assert "SQL Fundamentals" in titles
    assert "Data Visualization" in titles
    assert titles.index("SQL Fundamentals") < titles.index(
        "Data Visualization"
    )


def test_irrelevant_courses_are_excluded(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "courses.csv"
    )

    result = recommend_courses(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
    )

    titles = [course["title"] for course in result]

    assert "Python Basics" not in titles
    assert "Design Basics" not in titles


def test_top_n_limits_recommendations(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "courses.csv"
    )

    result = recommend_courses(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        top_n=1,
        catalog_path=catalog_path,
    )

    assert len(result) == 1


def test_invalid_top_n_is_rejected():
    with pytest.raises(ValueError, match="top_n"):
        recommend_courses(
            resume_text="Python",
            career_family="Data & Analytics",
            top_n=0,
        )


def test_no_recommendations_when_all_required_skills_are_detected(
    tmp_path,
):
    catalog_path = create_test_catalog(
        tmp_path / "courses.csv"
    )

    resume = """
    Technical Skills
    Python, SQL, Pandas, NumPy, EDA, Statistics,
    Tableau, Power BI, Data Visualization, MySQL, PostgreSQL
    """

    result = recommend_courses(
        resume_text=resume,
        career_family="Data & Analytics",
        catalog_path=catalog_path,
    )

    assert result == []


def test_duplicate_course_ids_are_returned_only_once(tmp_path):
    catalog_path = tmp_path / "courses.csv"
    create_test_catalog(catalog_path)

    with catalog_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writerow({
            "course_id": "SQL-001",
            "title": "SQL Fundamentals Duplicate",
            "provider": "Test Provider",
            "url": "https://example.com/sql-duplicate",
            "skills": "sql",
            "career_families": "Data & Analytics",
            "level": "Beginner",
            "price": "Free",
            "duration": "",
            "description": "Duplicate test course.",
        })

    result = recommend_courses(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
    )

    course_ids = [course["course_id"] for course in result]

    assert len(course_ids) == len(set(course_ids))
