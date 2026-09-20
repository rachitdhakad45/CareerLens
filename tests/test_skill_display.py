from src.nlp.skill_display import (
    format_category_name,
    format_skill_name,
)


def test_format_category_name():
    assert format_category_name("data_science") == "Data Science"
    assert format_category_name("core_cs") == "Core CS"


def test_format_skill_name():
    assert format_skill_name("python") == "Python"
    assert format_skill_name("github") == "GitHub"
    assert format_skill_name("machine learning") == "Machine Learning"
    assert format_skill_name("ai integration") == "AI Integration"