"""
True/False card model.

Each card has a statement, a boolean truth value, and an explanation.
"""
from pydantic import Field

from models.base import BaseCard


class TrueFalseCard(BaseCard):
    """A true-or-false quiz card with an explanation.

    Attributes:
        statement: A declarative statement to evaluate.
        is_true: Whether the statement is true.
        explanation: Why the statement is true or false.
    """

    statement: str = Field(..., min_length=5, description="Declarative statement")
    is_true: bool = Field(..., description="Whether the statement is true")
    explanation: str = Field(
        ..., min_length=5, description="Explanation of the correct answer"
    )

    def _content_fields(self) -> list[str]:
        return super()._content_fields() + ["statement", "explanation"]
