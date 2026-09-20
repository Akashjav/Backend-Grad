import re


def extract_skills(text, skills):
    found = []
    for skill in skills:
        for alias in [skill.name, *skill.aliases]:
            match = re.search(
                r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, flags=re.IGNORECASE
            )
            if match:
                found.append(
                    {
                        "skill_id": skill.id,
                        "name": skill.name,
                        "matched_term": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "domain_id": skill.domain_id,
                    }
                )
                break
    return {
        "skills": found,
        "provider": "taxonomy-alias-extractor",
        "version": "1.0",
        "verified": False,
    }
