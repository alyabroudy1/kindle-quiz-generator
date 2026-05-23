"""
Standard Question/Answer card model.

Each card has a single question and a single answer.
"""
from pydantic import Field

from models.base import BaseCard


class StandardQACard(BaseCard):
    """A straightforward question → answer flashcard.

    Attributes:
        question: The question text shown to the reader.
        answer: The correct answer revealed on tap.
    """

    question: str = Field(..., min_length=5, description="The question text")
    answer: str = Field(..., min_length=2, description="The correct answer")

    def _content_fields(self) -> list[str]:
        return super()._content_fields() + ["question", "answer"]
