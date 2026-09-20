from src.ats.analyzer import (
    calculate_completeness,
    calculate_skill_coverage,
    calculate_category_coverage,
    calculate_evidence_strength,
    calculate_skill_diversity,
    calculate_project_experience_presence,
    calculate_role_information,
    calculate_project_technologies,
    calculate_achievement_quality,
    calculate_education_presence,
    calculate_certification_presence,
    calculate_section_structure,
    calculate_section_organization,
    calculate_action_language,
    calculate_quantifiable_content,
    calculate_overall_ats_score,
    generate_ats_suggestions,
)
from src.resume.extractor import ResumeData


def test_calculate_completeness():
    resume = ResumeData(
        name="Rachit Dhakad",
        email="rachit@example.com",
        phone="9098689136",
        education=["B.Tech CSE"],
        projects=["AI Sales System"],
        certifications=["OCI Data Science"],
        skills=["Python", "SQL"],
        experience=[],
    )

    result = calculate_completeness(resume)

    assert result["score"] == 19
    assert result["max_score"] == 20

    assert result["checks"]["name"] is True
    assert result["checks"]["email"] is True
    assert result["checks"]["phone"] is True
    assert result["checks"]["education"] is True
    assert result["checks"]["skills"] is True
    assert result["checks"]["projects"] is True
    assert result["checks"]["experience"] is False
    assert result["checks"]["certifications"] is True

from src.nlp.skill_extractor import SkillMatch


def test_calculate_skill_coverage():
    matches = [
        SkillMatch(
            skill="python",
            category="programming",
            confidence=1.0,
            evidence="Technical Skills",
        ),
        SkillMatch(
            skill="sql",
            category="databases",
            confidence=1.0,
            evidence="Technical Skills",
        ),
        SkillMatch(
            skill="flask",
            category="web_development",
            confidence=0.9,
            evidence="Project Core Skills",
        ),
    ]

    result = calculate_skill_coverage(matches)

    assert result["score"] == 2.25
    assert result["max_score"] == 15
    assert result["detected_skills"] == 3

def test_calculate_category_coverage():
    grouped_skills = {
        "programming": [],
        "data_science": [],
        "databases": [],
    }

    result = calculate_category_coverage(grouped_skills)

    assert result["score"] == 2.5
    assert result["max_score"] == 5
    assert result["populated_categories"] == 3

def test_calculate_evidence_strength():
    matches = [
        SkillMatch(
            skill="python",
            category="programming",
            confidence=1.0,
            evidence="Technical Skills",
        ),
        SkillMatch(
            skill="flask",
            category="web_development",
            confidence=0.9,
            evidence="Project Core Skills",
        ),
    ]

    result = calculate_evidence_strength(matches)

    assert result["average_confidence"] == 0.95
    assert result["score"] == 4.75
    assert result["max_score"] == 5

def test_calculate_skill_diversity():
    grouped_skills = {
        "programming": ["python", "javascript"],
        "data_science": [
            "python",
            "pandas",
            "numpy",
        ],
        "databases": ["sql", "mysql"],
        "core_cs": ["dsa", "oops"],
        "web_development": ["flask"],
    }

    result = calculate_skill_diversity(grouped_skills)

    assert result["meaningful_categories"] == 4
    assert result["score"] == 4.0
    assert result["max_score"] == 5

def test_calculate_project_experience_presence():
    resume = ResumeData(
        projects=["AI Sales System"],
        experience=[],
    )

    result = calculate_project_experience_presence(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["has_projects"] is True
    assert result["has_experience"] is False

def test_calculate_role_information():
    resume = ResumeData(
        projects=[
            "Autonomous AI Sales & Recovery System",
            "Role: ML & Backend Developer",
        ],
        experience=[],
    )

    result = calculate_role_information(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["role_found"] is True

def test_calculate_project_technologies():
    resume = ResumeData(
        projects=[
            "Autonomous AI Sales & Recovery System",
            "Core Skills: Python, Flask, MySQL, NumPy, Pandas",
        ],
        experience=[],
    )

    result = calculate_project_technologies(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["technology_found"] is True

def test_calculate_achievement_quality():
    resume = ResumeData(
        projects=[
            (
                "Built an AI-driven automation system to analyze "
                "1K+ customer records, improving lead accuracy by ~20%."
            )
        ],
        experience=[],
    )

    result = calculate_achievement_quality(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["has_number"] is True
    assert result["has_action_verb"] is True

def test_calculate_education_presence():
    resume = ResumeData(
        education=[
            "B.Tech CSE, AITR, Indore",
            "HSC - 78.40%",
            "SSC - 95.60%",
        ]
    )

    result = calculate_education_presence(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["education_found"] is True

def test_calculate_certification_presence():
    resume = ResumeData(
        certifications=[
            "ORACLE- OCI Data Science"
        ]
    )

    result = calculate_certification_presence(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["certifications_found"] is True

def test_calculate_section_structure():
    resume = ResumeData(
        education=["B.Tech CSE"],
        skills=["Python"],
        projects=["AI Sales System"],
        experience=[],
        certifications=["Oracle OCI"],
    )

    result = calculate_section_structure(resume)

    assert result["score"] == 4
    assert result["max_score"] == 5
    assert result["present_sections"] == 4

def test_calculate_section_organization():
    resume = ResumeData(
        education=["B.Tech CSE"],
        skills=["Python"],
        projects=["AI Sales System"],
        experience=[],
        certifications=["Oracle OCI"],
    )

    result = calculate_section_organization(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["non_empty_sections"] == 4

def test_calculate_action_language():
    resume = ResumeData(
        projects=[
            "Built an AI system.",
            "Developed automation.",
            "Improved prediction accuracy.",
        ],
        experience=[],
    )

    result = calculate_action_language(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert len(result["matched_verbs"]) == 3

def test_calculate_quantifiable_content():
    resume = ResumeData(
        projects=[
            "Analyzed 1K+ customer records.",
            "Improved accuracy by 20%.",
        ],
        experience=[],
    )

    result = calculate_quantifiable_content(resume)

    assert result["score"] == 5
    assert result["max_score"] == 5
    assert result["quantifiable_items"] == 2

def test_calculate_overall_ats_score():
    resume = ResumeData(
        name="Rachit Dhakad",
        email="rachit@example.com",
        phone="9098689136",
        education=["B.Tech CSE"],
        experience=[],
        projects=[
            "Autonomous AI Sales System",
            "Role: ML & Backend Developer",
            "Core Skills: Python, Flask, MySQL",
            "Built system analyzing 1K+ records and improving accuracy by 20%.",
        ],
        certifications=["Oracle OCI Data Science"],
        skills=["Python", "Machine Learning", "SQL"],
    )

    skill_matches = [
        SkillMatch(
            skill="python",
            category="programming",
            confidence=1.0,
            evidence="Technical Skills",
        ),
        SkillMatch(
            skill="machine learning",
            category="data_science",
            confidence=1.0,
            evidence="Technical Skills",
        ),
        SkillMatch(
            skill="sql",
            category="databases",
            confidence=1.0,
            evidence="Technical Skills",
        ),
    ]

    grouped_skills = {
        "programming": skill_matches[:1],
        "data_science": skill_matches[1:2],
        "databases": skill_matches[2:3],
    }

    result = calculate_overall_ats_score(
        resume,
        skill_matches,
        grouped_skills,
    )

    assert result["max_score"] == 100
    assert result["total_score"] > 0
    assert "resume_completeness" in result["breakdown"]
    assert "skills_keywords" in result["breakdown"]
    assert "projects_experience" in result["breakdown"]
    assert "education_certifications" in result["breakdown"]
    assert "resume_structure" in result["breakdown"]
    assert "content_quality" in result["breakdown"]

def test_generate_ats_suggestions():
    ats_result = {
        "breakdown": {
            "resume_completeness": {
                "score": 15,
                "max_score": 20,
                "checks": {
                    "name": True,
                    "email": True,
                    "phone": False,
                    "education": True,
                    "skills": True,
                    "projects": True,
                    "experience": False,
                    "certifications": False,
                },
            },
            "skills_keywords": {
                "skill_coverage": {
                    "score": 5,
                    "max_score": 15,
                },
                "evidence_strength": {
                    "score": 5,
                    "max_score": 5,
                },
            },
            "projects_experience": {
                "role_information": {
                    "score": 5,
                    "max_score": 5,
                },
                "project_technologies": {
                    "score": 5,
                    "max_score": 5,
                },
            },
            "content_quality": {
                "action_language": {
                    "score": 5,
                    "max_score": 5,
                },
                "quantifiable_content": {
                    "score": 0,
                    "max_score": 5,
                },
            },
            "resume_structure": {
                "section_structure": {
                    "score": 5,
                    "max_score": 5,
                },
            },
        }
    }

    suggestions = generate_ats_suggestions(ats_result)

    assert len(suggestions) > 0
    assert any("missing" in suggestion.lower() for suggestion in suggestions)
    assert any("measurable" in suggestion.lower() for suggestion in suggestions)



