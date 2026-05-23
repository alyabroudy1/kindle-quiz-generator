"""
Multiple Choice card model.

Each card has a question, exactly 4 options, and an index pointing to the correct one.
"""
from pydantic import Field, field_validator

from models.base import BaseCard


class MultipleChoiceCard(BaseCard):
    """A multiple-choice quiz card with exactly four options.

    Attributes:
        question: The question text.
        options: Exactly 4 answer options.
        correct_option_index: Zero-based index (0–3) of the correct option.
    """

    question: str = Field(..., min_length=5, description="The question text")
    options: list[str] = Field(
        ..., min_length=4, max_length=4, description="Exactly 4 answer options"
    )
    correct_option_index: int = Field(
        ..., ge=0, le=3, description="Index of the correct option (0–3)"
    )

    @field_validator("options")
    @classmethod
    def options_must_be_non_empty(cls, v: list[str]) -> list[str]:
        """Ensure every option string is non-empty."""
        for i, opt in enumerate(v):
            if not opt.strip():
                raise ValueError(f"Option at index {i} must not be empty")
        return v

    def _content_fields(self) -> list[str]:
        return super()._content_fields() + ["question"]
