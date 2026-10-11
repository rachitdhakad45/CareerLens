from src.recommendations.career_requirements import CAREER_REQUIREMENTS
from src.nlp.taxonomy import SKILL_TAXONOMY
from src.nlp.skill_extractor import SKILL_ALIASES, normalize_skill


def test_audit_career_requirements():
    known_skills = set()

    for skills in SKILL_TAXONOMY.values():
        known_skills.update(normalize_skill(skill) for skill in skills)

    known_skills.update(
        normalize_skill(alias)
        for alias in SKILL_ALIASES
    )

    required_skills = {
        normalize_skill(skill)
        for groups in CAREER_REQUIREMENTS.values()
        for skills in groups.values()
        for skill in skills
    }

    unsupported = sorted(required_skills - known_skills)

    print("\nCareer families:", len(CAREER_REQUIREMENTS))
    print("Unique required skills:", len(required_skills))
    print("Skills recognized by Phase 4:", len(required_skills & known_skills))
    print("Skills not yet recognized:", len(unsupported))

    for skill in unsupported:
        print(" -", skill)

from src.recommendations.career_requirements import SKILL_PRIORITIES


def test_all_career_families_have_explicit_priorities():
    assert set(SKILL_PRIORITIES) == set(CAREER_REQUIREMENTS)

    for family, groups in CAREER_REQUIREMENTS.items():
        prioritized_skills = SKILL_PRIORITIES[family]

        for skills in groups.values():
            for skill in skills:
                assert skill in prioritized_skills, (
                    f"Missing priority for {family}: {skill}"
                )
                assert prioritized_skills[skill] in {
                    "high",
                    "medium",
                    "low",
                }