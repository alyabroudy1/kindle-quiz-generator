"""
Concept & Example flashcard model.

Designed for explaining concepts in depth, including cheatsheets, tips,
and a dedicated example section.
"""
from pydantic import Field

from models.base import BaseCard


class ConceptExampleCard(BaseCard):
    """A card presenting a concept definition, deep explanation, and an example.

    Attributes:
        concept_name: The title or name of the concept.
        concept_description: A brief summary or definition of the concept and its rules.
        explanation: Detailed tips, cheatsheets, and deep explanations.
        example_content: A concrete, real-life example or code snippet.
    """

    concept_name: str = Field(
        ..., min_length=2, description="The title or name of the concept"
    )
    concept_description: str = Field(
        ..., min_length=5, description="A brief summary or definition of the concept"
    )
    explanation: str = Field(
        ..., min_length=10, description="Detailed tips, cheatsheets, and deep explanations (can be text, sketch, or markup)"
    )
    example_content: str = Field(
        ..., min_length=5, description="A concrete, real-life example or code snippet demonstrating the concept"
    )

    def _content_fields(self) -> list[str]:
        return super()._content_fields() + [
            "concept_name",
            "concept_description",
            "explanation",
            "example_content",
        ]

    # For unique identification in AI batching, we treat concept_name as the "question"
    @property
    def question(self) -> str:
        return self.concept_name
