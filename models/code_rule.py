"""
Code Rule comparison card model.

Each card presents a rule, an incorrect implementation, and a correct implementation.
"""
from pydantic import Field

from models.base import BaseCard


class CodeRuleCard(BaseCard):
    """A card showing a coding rule, a wrong example, and a correct example.

    Attributes:
        rule_description: A description of the rule/principle.
        incorrect_code: An example of the incorrect way to write the code.
        incorrect_explanation: Why the incorrect code is wrong.
        correct_code: An example of the correct way to write the code.
        correct_explanation: Why the correct code is right or how it fixes the issue.
    """

    rule_description: str = Field(
        ..., min_length=5, description="A description of the coding rule or principle"
    )
    incorrect_code: str = Field(
        ..., min_length=2, description="An example of incorrect or anti-pattern code"
    )
    incorrect_explanation: str = Field(
        ..., min_length=5, description="Explanation of why the incorrect code is wrong"
    )
    correct_code: str = Field(
        ..., min_length=2, description="An example of the correct, optimized code"
    )
    correct_explanation: str = Field(
        ..., min_length=5, description="Explanation of why the correct code is better"
    )

    def _content_fields(self) -> list[str]:
        return super()._content_fields() + [
            "rule_description",
            "incorrect_code",
            "incorrect_explanation",
            "correct_code",
            "correct_explanation",
        ]

    # For unique identification in AI batching, we treat rule_description as the "question"
    @property
    def question(self) -> str:
        return self.rule_description
