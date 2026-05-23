"""
Base card model — the enforcement layer.

All quiz card types inherit from BaseCard which guarantees:
  • Every card has a numeric id, topic, source_hint, and confidence_score.
  • confidence_score must be between 0.0 and 1.0 (filtering at >= 0.9 happens in the AI service).
  • source_hint must be at least 5 characters to prove provenance.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Self


class BaseCard(BaseModel):
    """Abstract base for every quiz card.

    Attributes:
        id: Sequential identifier for the card (≥ 1).
        topic: The subject area the card belongs to.
        source_hint: Provenance note (e.g. 'General Chemistry principles').
        confidence_score: AI self-assessed certainty, 0.0–1.0.
    """

    id: int = Field(..., ge=1, description="Sequential card identifier")
    topic: str = Field(..., min_length=2, description="Subject area")
    source_hint: str = Field(
        ...,
        min_length=5,
        description="Where this fact comes from, e.g. 'Standard Biology Textbook'",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence — must be >= 0.9 to pass the validation gate",
    )

    # ── Content-level validation ────────────────────────────────────
    @model_validator(mode="after")
    def validate_content(self) -> Self:
        """Ensure no critical field is empty or whitespace-only.

        Subclasses add their own fields to _content_fields() so this
        validator automatically covers them too.
        """
        for field_name in self._content_fields():
            value = getattr(self, field_name, None)
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"Field '{field_name}' must not be empty or whitespace")
        return self

    def _content_fields(self) -> list[str]:
        """Return field names that must be non-empty strings.

        Override in subclasses to add quiz-specific fields.
        """
        return ["topic", "source_hint"]
