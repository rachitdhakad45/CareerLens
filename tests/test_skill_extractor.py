from src.nlp.skill_extractor import (
    normalize_skill,
    get_skill_category,
    extract_skills,
    extract_skill_matches,
    group_skill_matches_by_category,
)


def test_skill_normalization():

    assert normalize_skill("Python") == "python"
    assert normalize_skill("ML") == "machine learning"
    assert normalize_skill("sklearn") == "scikit-learn"
    assert normalize_skill("Github") == "github"


def test_skill_categories():

    assert get_skill_category("Python") == "programming"
    assert get_skill_category("Machine Learning") == "data_science"
    assert get_skill_category("SQL") == "databases"
    assert get_skill_category("GitHub") == "devops"

def test_skill_extraction():

    resume_text = """
    Technical Skills:
    Python, Machine Learning, SQL, Pandas, GitHub
    """

    skills = extract_skills(resume_text)

    assert "python" in skills
    assert "machine learning" in skills
    assert "sql" in skills
    assert "pandas" in skills
    assert "github" in skills

def test_alias_skill_extraction():

    resume_text = """
    Skills:
    Python, ML, sklearn, Github, OOPs
    """

    skills = extract_skills(resume_text)

    assert "python" in skills
    assert "machine learning" in skills
    assert "scikit-learn" in skills
    assert "github" in skills
    assert "oops" in skills

def test_extract_skill_matches():
    text = """
    TECHNICAL SKILLS
    Python DSA OOPs

    PROJECTS
    Core Skills: Python, Flask, MySQL
    """

    matches = extract_skill_matches(text)

    skills = {match.skill for match in matches}

    assert "python" in skills
    assert "oops" in skills
    assert "flask" in skills
    assert "mysql" in skills

    python_match = next(
        match for match in matches
        if match.skill == "python"
    )

    flask_match = next(
        match for match in matches
        if match.skill == "flask"
    )

    assert python_match.confidence == 1.00
    assert python_match.evidence == "Technical Skills"

    assert flask_match.confidence == 0.90
    assert flask_match.evidence == "Project Core Skills"

def test_group_skill_matches_by_category():
    text = """
    TECHNICAL SKILLS
    Python SQL DSA

    PROJECTS
    Core Skills: Flask MySQL
    """

    matches = extract_skill_matches(text)

    grouped = group_skill_matches_by_category(matches)

    assert "programming" in grouped
    assert "databases" in grouped
    assert "core_cs" in grouped
    assert "web_development" in grouped

    programming_skills = {
        match.skill
        for match in grouped["programming"]
    }

    database_skills = {
        match.skill
        for match in grouped["databases"]
    }

    assert "python" in programming_skills
    assert "sql" in database_skills
    assert "mysql" in database_skills

