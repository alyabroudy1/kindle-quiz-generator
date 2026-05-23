"""
AI Provider — Strict & Verified Generation via NVIDIA Build API.

Uses the openai Python library pointed at NVIDIA's OpenAI-compatible endpoint.
Since NVIDIA does not enforce JSON schemas like OpenAI's newest features,
Pydantic is our primary safety net for filtering out bad/hallucinated data.
"""
from __future__ import annotations

import json
import importlib
from typing import Type

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    DEFAULT_MODEL,
    MIN_CONFIDENCE_SCORE,
    QUIZ_TYPE_REGISTRY,
)
from models.base import BaseCard


class AIProvider:
    """Handles all interactions with the NVIDIA LLM API.

    Responsibilities:
        1. Construct schema-aware prompts based on the requested quiz type.
        2. Call the NVIDIA API with strict temperature settings.
        3. Parse the raw JSON response.
        4. Validate every card through Pydantic and the confidence gate.
    """

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=NVIDIA_API_KEY,
        )

    # ── Prompt engineering ──────────────────────────────────────────

    @staticmethod
    def _get_system_prompt() -> str:
        """Return the hardcoded, strict system prompt for the AI."""
        return (
            "You are a strict, fact-checking academic tutor.\n"
            "RULES:\n"
            "1. Do NOT guess. If you are not 100% certain of a fact, do not include it.\n"
            "2. Every fact must be widely accepted consensus.\n"
            "3. Provide a \"confidence_score\" of 1.0 if certain. Omit the card if uncertain.\n"
            "4. Provide a brief \"source_hint\" (e.g., 'General Chemistry principles').\n"
            "5. Output STRICTLY valid JSON. No markdown backticks, no extra text.\n"
            "6. Do not guess. Only provide 100% verified facts. Output strictly valid JSON."
        )

    @staticmethod
    def _build_user_prompt(
        topic: str,
        num_cards: int,
        card_model: Type[BaseCard],
        existing_questions: list[str] | None = None,
    ) -> str:
        """Build a detailed user prompt that describes the required JSON schema."""
        # Introspect the Pydantic model to communicate the schema to the LLM
        schema = card_model.model_json_schema()
        properties = schema.get("properties", {})

        field_descriptions = []
        for name, info in properties.items():
            desc = info.get("description", "")
            ftype = info.get("type", "any")
            field_descriptions.append(f'  - "{name}" ({ftype}): {desc}')

        fields_block = "\n".join(field_descriptions)

        avoid_block = ""
        if existing_questions:
            # Show up to 30 existing questions to avoid hitting prompt length limits
            sample_existing = existing_questions[-30:]
            avoid_list = "\n".join(f'  - "{q}"' for q in sample_existing)
            avoid_block = (
                f"\nCRITICAL: Do NOT duplicate, repeat, or cover the exact same facts/questions "
                f"as these cards that have already been generated:\n{avoid_list}\n"
            )

        return (
            f"Generate exactly {num_cards} quiz flashcards about: '{topic}'.\n\n"
            f"Each card MUST be a JSON object with these fields:\n{fields_block}\n\n"
            f"{avoid_block}\n"
            f"Return a JSON object with a single key \"cards\" containing an array of "
            f"{num_cards} card objects.\n"
            f"The \"topic\" field should be \"{topic}\".\n"
            f"Ensure every card has confidence_score of 1.0 and a meaningful source_hint."
        )

    # ── Model resolution ────────────────────────────────────────────

    @staticmethod
    def _resolve_card_model(card_model_type: str) -> Type[BaseCard]:
        """Dynamically import and return the Pydantic model class for the given quiz type."""
        registry_entry = QUIZ_TYPE_REGISTRY.get(card_model_type)
        if registry_entry is None:
            raise ValueError(
                f"Unknown quiz type '{card_model_type}'. "
                f"Available: {list(QUIZ_TYPE_REGISTRY.keys())}"
            )
        module = importlib.import_module(registry_entry["model_module"])
        return getattr(module, registry_entry["model_class"])

    # ── Main generation pipeline ────────────────────────────────────

    def generate_cards(
        self, topic: str, num_cards: int, card_model_type: str, model_name: str = DEFAULT_MODEL
    ) -> list[BaseCard]:
        """Generate, validate, and return quiz cards from the NVIDIA API by batching requests.

        Args:
            topic: The subject matter (e.g. "Quantum Mechanics").
            num_cards: How many cards to request.
            card_model_type: Key into QUIZ_TYPE_REGISTRY (e.g. "standard_qa").

        Returns:
            A list of validated Pydantic card objects. Cards that fail
            validation or have low confidence are silently discarded.
        """
        CardModel = self._resolve_card_model(card_model_type)

        # Code rule cards have complex schemas and generate lots of text, so use a smaller batch
        batch_size = 5 if card_model_type == "code_rule" else 10
        validated_cards: list[BaseCard] = []
        consecutive_failures = 0
        max_failures = 3

        # Track already generated questions to avoid duplicates/repetitions
        existing_questions: list[str] = []

        print(f"\n🧠 Starting batch generation for {num_cards} {card_model_type} cards on '{topic}'...")

        while len(validated_cards) < num_cards and consecutive_failures < max_failures:
            cards_to_request = min(batch_size, num_cards - len(validated_cards))
            batch_num = (len(validated_cards) // batch_size) + 1

            print(
                f"\n📡 Querying NVIDIA AI ({model_name}) for batch {batch_num} "
                f"({cards_to_request} cards, target: {num_cards}, current: {len(validated_cards)})..."
            )

            # Build prompt with exclusion list
            user_prompt = self._build_user_prompt(
                topic, cards_to_request, CardModel, existing_questions
            )

            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=4096,
                    timeout=60.0,
                )

                raw_content = response.choices[0].message.content
                if raw_content is None:
                    print("  ⚠️ AI returned an empty response. Retrying...")
                    consecutive_failures += 1
                    continue

                parsed_data = json.loads(raw_content)

                # Handle the AI wrapping arrays in objects (e.g. {"cards": [...]})
                if isinstance(parsed_data, dict):
                    cards_data: list = next(
                        (v for v in parsed_data.values() if isinstance(v, list)), []
                    )
                elif isinstance(parsed_data, list):
                    cards_data = parsed_data
                else:
                    raise ValueError("Invalid JSON structure returned by AI")

                if not cards_data:
                    print("  ⚠️ No cards found in AI response. Retrying...")
                    consecutive_failures += 1
                    continue

                # ── STRICT VALIDATION GATE ──────────────────────────────
                batch_accepted_count = 0
                batch_rejected_count = 0

                for item in cards_data:
                    try:
                        # Give temp ID
                        item["id"] = len(validated_cards) + batch_accepted_count + 1
                        if "topic" not in item:
                            item["topic"] = topic

                        card = CardModel(**item)

                        # Extract card question/statement to check for uniqueness
                        question_val = ""
                        if hasattr(card, "question"):
                            question_val = card.question.strip()
                        elif hasattr(card, "statement"):
                            question_val = card.statement.strip()

                        # Prevent duplicates
                        is_duplicate = False
                        if question_val:
                            # Simple fuzzy duplicate check (lowercased comparison)
                            normalized_q = question_val.lower().strip("?.! ")
                            for existing_q in existing_questions:
                                if existing_q.lower().strip("?.! ") == normalized_q:
                                    is_duplicate = True
                                    break

                        if is_duplicate:
                            batch_rejected_count += 1
                            continue

                        if (
                            card.confidence_score >= MIN_CONFIDENCE_SCORE
                            and card.source_hint
                            and len(card.source_hint.strip()) >= 5
                        ):
                            validated_cards.append(card)
                            batch_accepted_count += 1
                            if question_val:
                                existing_questions.append(question_val)
                        else:
                            batch_rejected_count += 1
                            print(
                                f"  ⚠️  Card {item.get('id', '?')} rejected: low confidence "
                                f"({card.confidence_score}) or missing/short source_hint"
                            )
                    except ValidationError as e:
                        batch_rejected_count += 1
                        print(f"  ⚠️  Card validation failed: {e.errors()[0]['msg']}")
                    except Exception as e:
                        batch_rejected_count += 1
                        print(f"  ⚠️  Card parsing failed: {e}")

                print(
                    f"  ✅ Batch {batch_num}: Accepted {batch_accepted_count} | "
                    f"Rejected/Unsure/Duplicate: {batch_rejected_count}"
                )

                if batch_accepted_count > 0:
                    consecutive_failures = 0  # Reset failure count since we got new valid cards
                else:
                    consecutive_failures += 1

            except KeyboardInterrupt:
                print("\n🛑 Generation manually interrupted. Saving cards generated so far...")
                break
            except json.JSONDecodeError as e:
                print(f"  ❌ Failed to parse batch AI response as JSON: {e}")
                consecutive_failures += 1
            except Exception as e:
                print(f"  ❌ Error in batch generation: {e}")
                consecutive_failures += 1

        # Re-number IDs sequentially so templates can rely on consecutive IDs
        for idx, card in enumerate(validated_cards, start=1):
            card.id = idx

        print(
            f"\n🎉 Generation complete! Total accepted: {len(validated_cards)}/{num_cards}"
        )
        return validated_cards
