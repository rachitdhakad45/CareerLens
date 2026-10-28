"""Small, private career guidance that works without an external API key."""

import re


def answer_career_question(question: str, context: dict) -> str:
    """Return a short response grounded only in the supplied resume context."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string.")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary.")

    normalized = question.casefold()
    target = str(context.get("target_career_family") or "your target role")
    found = context.get("skills_found", [])
    missing = context.get("skills_not_found_in_resume", [])
    suggestions = context.get("ats_suggestions", [])
    current_opportunities = context.get("opportunities", [])

    found_names = [
        str(item.get("skill", "")).strip()
        for item in found
        if isinstance(item, dict) and item.get("skill")
    ]
    missing_names = [
        str(item.get("skill", "")).strip()
        for item in missing
        if isinstance(item, dict) and item.get("skill")
    ]

    if any(word in normalized for word in ("apply", "eligible", "suitable")):
        role_match = re.search(
            r"\b(?:role|position)\s+(?:of\s+)?(.+?)"
            r"(?:\s+with\s+(?:this|my)\s+resume|[?.!]|$)",
            question,
            flags=re.IGNORECASE,
        )
        role_title = (
            role_match.group(1).strip(" .?!")
            if role_match
            else target
        )
        evidence = ", ".join(found_names[:5]) or "no clear skill evidence"
        gaps = ", ".join(missing_names[:4]) or "no major listed skill gaps"
        role_guidance = (
            "For product management, highlight real examples of prioritizing "
            "work, understanding users, and measuring outcomes."
            if "product manager" in role_title.casefold()
            else "Highlight real examples that match the role's core duties."
        )
        return (
            f"You can apply if you meet the role's stated requirements; a "
            f"resume alone can't confirm eligibility. For {role_title}, your "
            f"resume shows {evidence}. It doesn't show {gaps}. Compare the "
            f"job description with your actual experience. {role_guidance} "
            "Apply if you can support the role's key requirements with "
            "examples."
        )

    if any(word in normalized for word in ("gap", "learn", "next", "missing", "build")):
        if not missing_names:
            return (
                f"CareerLens did not find a clear skill gap for {target}. "
                "Your next step is to add stronger evidence for your skills "
                "and check the Opportunities tab for roles to explore."
            )
        items = "; ".join(missing_names[:5])
        return (
            f"For {target}, the top skills not found in your resume are "
            f"{items}. Start with one high-priority skill, build a small "
            "project using it, then add the project and your specific "
            "contribution to your resume."
        )

    if any(word in normalized for word in ("strength", "good at", "skills", "strong")):
        if not found_names:
            return (
                "I couldn't find skills from CareerLens' current vocabulary "
                "in the uploaded resume. Add a clear Skills section and "
                "describe how you used each skill in a project or experience."
            )
        items = "; ".join(found_names[:6])
        return (
            f"Your resume currently shows {items}. For {target}, strengthen "
            "the best examples with the project, your contribution, and a "
            "measurable result where possible."
        )

    if any(word in normalized for word in ("ats", "resume", "score", "format", "improve")):
        if suggestions:
            return "A few ways to strengthen the resume: " + "; ".join(
                str(item) for item in suggestions[:3]
            )
        return (
            "Open the Resume and ATS tab to review the score breakdown and "
            "evidence. Keep bullets specific: action, tool or skill, and "
            "result. The score is advisory, not a hiring prediction."
        )

    if any(word in normalized for word in ("job", "jobs", "opportunit", "opening")):
        if current_opportunities:
            titles = "; ".join(
                str(item.get("title", ""))
                for item in current_opportunities[:3]
                if isinstance(item, dict) and item.get("title")
            )
            if titles:
                return (
                    f"The Opportunities tab currently shows {titles}. "
                    "Open each listing to check location, eligibility, and "
                    "whether the role is still accepting applications."
                )
        return (
            "I don't have a matched listing in this session yet. Open the "
            "Opportunities tab, refresh the source, or try a neighboring "
            "career path."
        )

    if any(word in normalized for word in ("project", "experience", "evidence")):
        projects = context.get("projects", [])
        experience = context.get("experience", [])
        examples = [str(item) for item in (projects + experience)[:2] if item]
        if examples:
            return (
                "Use one of these resume examples to show a skill in context: "
                + "; ".join(examples)
                + ". Clarify your contribution and the outcome."
            )
        return (
            "No project or experience details were detected. Add one project "
            "with the problem, tools you used, your contribution, and the "
            "result so employers can see the skill in action."
        )

    if any(word in normalized for word in ("career", "role", "fit", "which")):
        evidence = "; ".join(found_names[:4]) or "no clear skill evidence yet"
        return (
            f"Your selected direction is {target}. The resume currently "
            f"shows {evidence}. Treat the model suggestion as a starting "
            "point, then compare it with your interests and project evidence."
        )

    return (
        f"I can help with your skills, gaps, resume improvements, or the "
        f"{target} career path. Try asking: ‘What should I learn next?’ or "
        "‘Which strengths are visible in my resume?’"
    )
