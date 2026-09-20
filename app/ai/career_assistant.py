"""Local guidance provider. Replace through this interface for a hosted LLM."""

from typing import Protocol


class CareerProvider(Protocol):
    def answer(self, prompt: str) -> str: ...


class RuleBasedCareerProvider:
    def answer(self, prompt: str) -> str:
        if "resume" in prompt.lower():
            return "Describe your education, projects, responsibilities and measurable outcomes. Map each claim to evidence in your portfolio, then take the relevant skill assessments."
        if "interview" in prompt.lower():
            return "Review the opportunity requirements, practice explaining your verified projects, and prepare examples demonstrating the required competencies."
        return "Choose an opportunity, review its skill-gap explanation, complete the recommended learning, and reassess. Use an alumni or academic mentor for domain-specific guidance."


provider: CareerProvider = RuleBasedCareerProvider()


def generate_ai_answer(prompt: str) -> str:
    return provider.answer(prompt)
