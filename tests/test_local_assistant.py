from src.assistant.local import answer_career_question


def sample_context():
    return {
        "target_career_family": "Data & Analytics",
        "skills_found": [
            {"skill": "python", "evidence": "built a Python project"},
            {"skill": "sql", "evidence": "used SQL in coursework"},
        ],
        "skills_not_found_in_resume": [
            {"skill": "pandas", "priority": "high"},
            {"skill": "statistics", "priority": "medium"},
        ],
        "ats_suggestions": ["Add measurable project outcomes."],
        "projects": ["Sales dashboard using Python and SQL"],
        "experience": [],
        "opportunities": [{"title": "Junior Data Analyst", "company": "Acme"}],
    }


def test_local_assistant_suggests_next_skill_without_external_service():
    answer = answer_career_question("What should I learn next?", sample_context())

    assert "Data & Analytics" in answer
    assert "pandas" in answer


def test_local_assistant_uses_resume_evidence_for_strengths():
    answer = answer_career_question("What strengths stand out?", sample_context())

    assert "python" in answer
    assert "sql" in answer


def test_local_assistant_can_point_to_opportunities():
    answer = answer_career_question("Any opportunities?", sample_context())

    assert "Junior Data Analyst" in answer


def test_local_assistant_answers_resume_improvement_prompt():
    answer = answer_career_question(
        "How can I improve my resume?",
        sample_context(),
    )

    assert "measurable project outcomes" in answer


def test_local_assistant_requires_a_question():
    try:
        answer_career_question(" ", sample_context())
    except ValueError as error:
        assert "question" in str(error)
    else:
        raise AssertionError("empty question should be rejected")
