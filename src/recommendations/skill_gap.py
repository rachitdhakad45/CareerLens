
from src.nlp.skill_extractor import (
    extract_skill_matches,
    normalize_skill,
)
from src.recommendations.career_requirements import (
    CAREER_REQUIREMENTS,
    SKILL_PRIORITIES,
)


def analyze_skill_gap(
    resume_text: str,
    career_family: str,
) -> dict:
    """
    Compare detected resume skills with career requirements.

    The coverage score measures the percentage of required skills
    detected in the resume, including skills mentioned without
    strong supporting evidence. It does not measure actual
    proficiency.
    """

    # Validate the resume text.
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    # Validate the selected career family.
    if career_family not in CAREER_REQUIREMENTS:
        raise ValueError(
            f"Unsupported career family: {career_family}"
        )

    # Flatten career requirements while retaining categories.
    required_skills = {}

    for category, skills in CAREER_REQUIREMENTS[career_family].items():
        for skill in skills:
            canonical_skill = normalize_skill(skill)
            required_skills[canonical_skill] = category

    # Extract skills detected in the resume.
    extracted_matches = extract_skill_matches(resume_text)

    detected_skills = {
        normalize_skill(match.skill): match
        for match in extracted_matches
    }

    # Prepare result categories.
    covered_skills = []
    mention_only_skills = []
    missing_skills = []

    # Compare detected skills against career requirements.
    career_priorities = SKILL_PRIORITIES.get(career_family, {})

    for skill, category in required_skills.items():
        match = detected_skills.get(skill)

        if match is None:
            priority = career_priorities.get(skill, "medium")

            missing_skills.append({
                "skill": skill,
                "category": category,
                "priority": priority,
            })

        elif match.confidence >= 0.90:
            covered_skills.append({
                "skill": skill,
                "category": category,
                "evidence": match.evidence,
                "confidence": match.confidence,
            })

        else:
            mention_only_skills.append({
                "skill": skill,
                "category": category,
                "evidence": match.evidence,
                "confidence": match.confidence,
            })

    # Sort missing skills: high, medium, then low priority.
    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    missing_skills.sort(
        key=lambda item: (
            priority_order.get(item["priority"], 1),
            item["skill"],
        )
    )

    # Calculate detected skill coverage.
    total_required = len(required_skills)

    detected_count = (
        len(covered_skills)
        + len(mention_only_skills)
    )

    coverage_score = (
        round(detected_count / total_required * 100, 2)
        if total_required
        else 0.0
    )

    # Return the complete skill-gap analysis.
    return {
        "career_family": career_family,
        "total_required": total_required,
        "covered_count": len(covered_skills),
        "mention_only_count": len(mention_only_skills),
        "missing_count": len(missing_skills),
        "coverage_score": coverage_score,
        "covered_skills": covered_skills,
        "mention_only_skills": mention_only_skills,
        "missing_skills": missing_skills,
    }