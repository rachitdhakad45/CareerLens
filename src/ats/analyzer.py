import re

COMPLETENESS_WEIGHTS = {
    "name": 2,
    "email": 2,
    "phone": 2,
    "education": 4,
    "skills": 4,
    "projects": 3,
    "experience": 1,
    "certifications": 2,
}


def calculate_completeness(resume) -> dict:
    """Calculate resume completeness score out of 20."""

    checks = {
        "name": bool(resume.name),
        "email": bool(resume.email),
        "phone": bool(resume.phone),
        "education": bool(resume.education),
        "skills": bool(resume.skills),
        "projects": bool(resume.projects),
        "experience": bool(resume.experience),
        "certifications": bool(resume.certifications),
    }

    earned_points = sum(
        COMPLETENESS_WEIGHTS[field]
        for field, present in checks.items()
        if present
    )

    return {
        "score": earned_points,
        "max_score": 20,
        "checks": checks,
    }

def calculate_skill_coverage(skill_matches) -> dict:
    """Calculate recognized skill coverage out of 15 points."""

    detected_skills = len(skill_matches)

    max_reference_skills = 20

    score = min(
        detected_skills / max_reference_skills,
        1.0,
    ) * 15

    return {
        "score": round(score, 2),
        "max_score": 15,
        "detected_skills": detected_skills,
        "reference_skills": max_reference_skills,
    }

def calculate_category_coverage(grouped_skills: dict) -> dict:
    """Calculate skill category coverage out of 5 points."""

    populated_categories = len(grouped_skills)

    max_reference_categories = 6

    score = min(
        populated_categories / max_reference_categories,
        1.0,
    ) * 5

    return {
        "score": round(score, 2),
        "max_score": 5,
        "populated_categories": populated_categories,
        "reference_categories": max_reference_categories,
    }

def calculate_evidence_strength(skill_matches) -> dict:
    """Calculate skill evidence strength out of 5 points."""

    if not skill_matches:
        return {
            "score": 0.0,
            "max_score": 5,
            "average_confidence": 0.0,
        }

    average_confidence = sum(
        match.confidence
        for match in skill_matches
    ) / len(skill_matches)

    score = average_confidence * 5

    return {
        "score": round(score, 2),
        "max_score": 5,
        "average_confidence": round(average_confidence, 2),
    }

def calculate_skill_diversity(grouped_skills: dict) -> dict:
    """Calculate skill diversity out of 5 points."""

    meaningful_categories = sum(
        1
        for skills in grouped_skills.values()
        if len(skills) >= 2
    )

    max_reference_categories = 5

    score = min(
        meaningful_categories / max_reference_categories,
        1.0,
    ) * 5

    return {
        "score": round(score, 2),
        "max_score": 5,
        "meaningful_categories": meaningful_categories,
        "reference_categories": max_reference_categories,
    }

def calculate_project_experience_presence(resume) -> dict:
    """Calculate project/experience presence out of 5 points."""

    has_projects = bool(resume.projects)
    has_experience = bool(resume.experience)

    if has_projects or has_experience:
        score = 5
    else:
        score = 0

    return {
        "score": score,
        "max_score": 5,
        "has_projects": has_projects,
        "has_experience": has_experience,
    }

def calculate_role_information(resume) -> dict:
    """Calculate role/title information out of 5 points."""

    entries = resume.projects + resume.experience

    role_indicators = (
        "role:",
        "developer",
        "engineer",
        "intern",
        "analyst",
        "manager",
        "lead",
        "consultant",
    )

    role_found = any(
        any(indicator in entry.lower() for indicator in role_indicators)
        for entry in entries
    )

    score = 5 if role_found else 0

    return {
        "score": score,
        "max_score": 5,
        "role_found": role_found,
    }

def calculate_project_technologies(resume) -> dict:
    """Calculate technology/core-skill evidence out of 5 points."""

    entries = resume.projects + resume.experience

    technology_indicators = (
        "core skills:",
        "technologies:",
        "tech stack:",
        "tools:",
        "skills:",
    )

    technology_found = any(
        any(indicator in entry.lower() for indicator in technology_indicators)
        for entry in entries
    )

    score = 5 if technology_found else 0

    return {
        "score": score,
        "max_score": 5,
        "technology_found": technology_found,
    }

def calculate_achievement_quality(resume) -> dict:
    """Calculate quantifiable/action-oriented achievement evidence out of 5 points."""

    entries = resume.projects + resume.experience

    text = " ".join(entries).lower()

    action_verbs = (
        "built",
        "developed",
        "implemented",
        "designed",
        "created",
        "improved",
        "analyzed",
        "automated",
        "optimized",
        "deployed",
    )

    has_number = bool(re.search(r"\b\d+(?:\.\d+)?%?\b|\b\d+[kKmM]\+?\b", text))

    has_action_verb = any(verb in text for verb in action_verbs)

    if has_number and has_action_verb:
        score = 5
    elif has_number or has_action_verb:
        score = 3
    else:
        score = 0

    return {
        "score": score,
        "max_score": 5,
        "has_number": has_number,
        "has_action_verb": has_action_verb,
    }

def calculate_education_presence(resume) -> dict:
    """Calculate education presence out of 5 points."""

    education_found = bool(resume.education)

    score = 5 if education_found else 0

    return {
        "score": score,
        "max_score": 5,
        "education_found": education_found,
    }

def calculate_certification_presence(resume) -> dict:
    """Calculate certification presence out of 5 points."""

    certifications_found = bool(resume.certifications)

    score = 5 if certifications_found else 0

    return {
        "score": score,
        "max_score": 5,
        "certifications_found": certifications_found,
    }

def calculate_section_structure(resume) -> dict:
    """Calculate standard resume section presence out of 5 points."""

    sections = {
        "education": bool(resume.education),
        "skills": bool(resume.skills),
        "projects": bool(resume.projects),
        "experience": bool(resume.experience),
        "certifications": bool(resume.certifications),
    }

    present_sections = sum(sections.values())

    # 5 standard sections -> full points
    score = min(present_sections / 5, 1.0) * 5

    return {
        "score": round(score, 2),
        "max_score": 5,
        "present_sections": present_sections,
        "total_sections": 5,
        "sections": sections,
    }

def calculate_section_organization(resume) -> dict:
    """Calculate basic section organization out of 5 points."""

    sections = [
        resume.education,
        resume.skills,
        resume.projects,
        resume.experience,
        resume.certifications,
    ]

    non_empty_sections = sum(bool(section) for section in sections)

    if non_empty_sections >= 4:
        score = 5
    elif non_empty_sections >= 2:
        score = 3
    elif non_empty_sections >= 1:
        score = 1
    else:
        score = 0

    return {
        "score": score,
        "max_score": 5,
        "non_empty_sections": non_empty_sections,
    }

def calculate_action_language(resume) -> dict:
    """Calculate action-oriented language out of 5 points."""

    entries = resume.projects + resume.experience
    text = " ".join(entries).lower()

    action_verbs = (
        "built",
        "developed",
        "implemented",
        "designed",
        "created",
        "improved",
        "analyzed",
        "automated",
        "optimized",
        "deployed",
    )

    matched_verbs = [
        verb for verb in action_verbs
        if verb in text
    ]

    if len(matched_verbs) >= 3:
        score = 5
    elif len(matched_verbs) >= 1:
        score = 3
    else:
        score = 0

    return {
        "score": score,
        "max_score": 5,
        "matched_verbs": matched_verbs,
    }

def calculate_quantifiable_content(resume) -> dict:
    """Calculate quantifiable content out of 5 points."""

    entries = resume.projects + resume.experience
    text = " ".join(entries)

    numbers = re.findall(
        r"\b\d+(?:\.\d+)?%?\b|\b\d+[kKmM]\+?\b",
        text,
    )

    if len(numbers) >= 2:
        score = 5
    elif len(numbers) == 1:
        score = 3
    else:
        score = 0

    return {
        "score": score,
        "max_score": 5,
        "quantifiable_items": len(numbers),
    }

def calculate_overall_ats_score(resume, skill_matches, grouped_skills) -> dict:
    """Calculate the complete ATS score out of 100."""

    completeness = calculate_completeness(resume)

    skill_coverage = calculate_skill_coverage(skill_matches)
    category_coverage = calculate_category_coverage(grouped_skills)
    evidence_strength = calculate_evidence_strength(skill_matches)
    skill_diversity = calculate_skill_diversity(grouped_skills)

    skills_score = (
        skill_coverage["score"]
        + category_coverage["score"]
        + evidence_strength["score"]
        + skill_diversity["score"]
    )

    project_presence = calculate_project_experience_presence(resume)
    role_information = calculate_role_information(resume)
    project_technologies = calculate_project_technologies(resume)
    achievement_quality = calculate_achievement_quality(resume)

    project_score = (
        project_presence["score"]
        + role_information["score"]
        + project_technologies["score"]
        + achievement_quality["score"]
    )

    education = calculate_education_presence(resume)
    certification = calculate_certification_presence(resume)

    education_score = (
        education["score"]
        + certification["score"]
    )

    structure = calculate_section_structure(resume)
    organization = calculate_section_organization(resume)

    structure_score = (
        structure["score"]
        + organization["score"]
    )

    action_language = calculate_action_language(resume)
    quantifiable_content = calculate_quantifiable_content(resume)

    content_score = (
        action_language["score"]
        + quantifiable_content["score"]
    )

    total_score = (
        completeness["score"]
        + skills_score
        + project_score
        + education_score
        + structure_score
        + content_score
    )

    return {
        "total_score": round(total_score, 2),
        "max_score": 100,
        "breakdown": {
            "resume_completeness": completeness,
            "skills_keywords": {
                "score": round(skills_score, 2),
                "max_score": 30,
                "skill_coverage": skill_coverage,
                "category_coverage": category_coverage,
                "evidence_strength": evidence_strength,
                "skill_diversity": skill_diversity,
            },
            "projects_experience": {
                "score": project_score,
                "max_score": 20,
                "project_presence": project_presence,
                "role_information": role_information,
                "project_technologies": project_technologies,
                "achievement_quality": achievement_quality,
            },
            "education_certifications": {
                "score": education_score,
                "max_score": 10,
                "education": education,
                "certification": certification,
            },
            "resume_structure": {
                "score": structure_score,
                "max_score": 10,
                "section_structure": structure,
                "section_organization": organization,
            },
            "content_quality": {
                "score": content_score,
                "max_score": 10,
                "action_language": action_language,
                "quantifiable_content": quantifiable_content,
            },
        },
    }

def generate_ats_suggestions(ats_result: dict) -> list[str]:
    """Generate score-aware and student-friendly ATS suggestions."""

    suggestions = []
    breakdown = ats_result["breakdown"]

    # -------------------------------------------------
    # Resume Completeness
    # -------------------------------------------------
    completeness = breakdown["resume_completeness"]

    missing_fields = [
        field.replace("_", " ").title()
        for field, present in completeness["checks"].items()
        if not present
    ]

    if missing_fields:
        # Experience is optional for students/freshers.
        non_optional_missing = [
            field for field in missing_fields
            if field != "Experience"
        ]

        if non_optional_missing:
            suggestions.append(
                f"Add missing resume information: "
                f"{', '.join(non_optional_missing)}."
            )

        if "Experience" in missing_fields:
            suggestions.append(
                "Experience section is optional for students. "
                "If you have internships, freelance work, "
                "or relevant practical experience, consider adding them."
            )

    # -------------------------------------------------
    # Skills & Keywords
    # -------------------------------------------------
    skills = breakdown["skills_keywords"]

    skill_coverage = skills["skill_coverage"]

    if skill_coverage["score"] < 0.60 * skill_coverage["max_score"]:
        suggestions.append(
            "Add more relevant technical skills that match "
            "your target career domain."
        )

    evidence_strength = skills["evidence_strength"]

    if evidence_strength["score"] < 0.60 * evidence_strength["max_score"]:
        suggestions.append(
            "Mention important skills in stronger evidence-based "
            "sections such as Technical Skills or Project Core Skills."
        )

    # -------------------------------------------------
    # Projects & Experience
    # -------------------------------------------------
    projects = breakdown["projects_experience"]

    if (
        projects["role_information"]["score"]
        < projects["role_information"]["max_score"]
    ):
        suggestions.append(
            "Clearly mention your role or responsibility "
            "for each project or experience."
        )

    if (
        projects["project_technologies"]["score"]
        < projects["project_technologies"]["max_score"]
    ):
        suggestions.append(
            "Add the technologies, tools, and frameworks "
            "used in your projects."
        )

    # -------------------------------------------------
    # Resume Structure
    # -------------------------------------------------
    structure = breakdown["resume_structure"]

    if (
        structure["section_structure"]["score"]
        < structure["section_structure"]["max_score"]
    ):
        suggestions.append(
            "Consider adding relevant standard resume sections "
            "such as Education, Skills, Projects, Experience, "
            "and Certifications."
        )

    # -------------------------------------------------
    # Content Quality
    # -------------------------------------------------
    content = breakdown["content_quality"]

    if (
        content["action_language"]["score"]
        < 0.60 * content["action_language"]["max_score"]
    ):
        suggestions.append(
            "Use stronger action verbs such as built, developed, "
            "implemented, analyzed, and optimized."
        )

    if (
        content["quantifiable_content"]["score"]
        < 0.60 * content["quantifiable_content"]["max_score"]
    ):
        suggestions.append(
            "Add measurable results such as percentages, "
            "user counts, dataset sizes, or performance improvements."
        )

    return suggestions





