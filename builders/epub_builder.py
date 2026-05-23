"""
EPUB Builder — The Assembler.

Takes validated Pydantic card objects, renders them through Jinja2 templates,
and compiles everything into a valid EPUB file using ebooklib.

The builder dynamically selects the correct template based on the Pydantic
model type, so adding a new quiz style requires zero changes here.
"""
from __future__ import annotations

import os
import re
from typing import Sequence

from ebooklib import epub
from jinja2 import Environment, FileSystemLoader

from config import OUTPUT_DIR, QUIZ_TYPE_REGISTRY
from models.base import BaseCard
from models.standard_qa import StandardQACard
from models.multiple_choice import MultipleChoiceCard
from models.true_false import TrueFalseCard
from models.code_rule import CodeRuleCard


# ── Template directory (sibling to this file's package) ─────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_DIR = os.path.join(_PROJECT_ROOT, "templates")
_STYLES_DIR = os.path.join(_TEMPLATE_DIR, "styles")


class EpubBuilder:
    """Assembles an EPUB book from validated quiz cards.

    Usage::

        builder = EpubBuilder(topic="Quantum Mechanics", quiz_type="standard_qa")
        output_path = builder.build(cards)
    """

    def __init__(self, topic: str, quiz_type: str) -> None:
        """
        Args:
            topic: The subject (used for the book title and filename).
            quiz_type: Key into QUIZ_TYPE_REGISTRY.
        """
        self.topic = topic
        self.quiz_type = quiz_type
        self.quiz_label = QUIZ_TYPE_REGISTRY[quiz_type]["label"]

        # Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR),
            autoescape=False,  # XHTML is hand-controlled
        )

    # ── Public API ──────────────────────────────────────────────────

    def build(self, cards: Sequence[BaseCard]) -> str:
        """Build and save an EPUB file from the given cards.

        Args:
            cards: Validated Pydantic card objects (all of the same type).

        Returns:
            Absolute path to the generated .epub file.
        """
        if not cards:
            raise ValueError("Cannot build an EPUB with zero cards.")

        book = epub.EpubBook()

        # ── Metadata ────────────────────────────────────────────────
        safe_topic = re.sub(r"[^a-zA-Z0-9]+", "_", self.topic).strip("_")
        
        # Truncate topic to avoid OS filename length limits (macOS limits to 255 bytes)
        # We limit to 100 chars to leave plenty of room for 'Flashcards_' and '.epub'
        if len(safe_topic) > 100:
            safe_topic = safe_topic[:100].strip("_")
            
        book.set_identifier(f"kindle-quiz-{safe_topic}")
        book.set_title(f"Flashcards: {self.topic[:100]}...")
        book.set_language("en")
        book.add_author("Kindle Quiz Generator")

        # ── CSS ─────────────────────────────────────────────────────
        css_path = os.path.join(_STYLES_DIR, "kindle.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        style = epub.EpubItem(
            uid="kindle_css",
            file_name="styles/kindle.css",
            media_type="text/css",
            content=css_content.encode("utf-8"),
        )
        book.add_item(style)

        # ── Index / Table of Contents page ──────────────────────────
        index_template = self.env.get_template("index.xhtml.j2")
        index_html = index_template.render(
            title=f"Flashcards: {self.topic}",
            num_cards=len(cards),
            quiz_type_label=self.quiz_label,
            cards=cards,
        )
        index_page = epub.EpubHtml(
            title="Table of Contents",
            file_name="index.xhtml",
            lang="en",
            content=index_html.encode("utf-8"),
        )
        index_page.add_item(style)
        book.add_item(index_page)

        # ── Card pages ──────────────────────────────────────────────
        spine: list = ["nav", index_page]
        toc: list = [epub.Link("index.xhtml", "Table of Contents", "toc")]

        total = len(cards)

        for card in cards:
            pages = self._render_card_pages(card, total, style)
            for page in pages:
                book.add_item(page)
                spine.append(page)

            # Only the question page goes into the TOC
            toc.append(
                epub.Link(
                    f"q{card.id}.xhtml",
                    f"Card {card.id}",
                    f"card_{card.id}",
                )
            )

        # ── Assemble ────────────────────────────────────────────────
        book.toc = toc
        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # ── Write ───────────────────────────────────────────────────
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f"Flashcards_{safe_topic}.epub"
        output_path = os.path.join(OUTPUT_DIR, filename)
        epub.write_epub(output_path, book, {})

        return output_path

    # ── Private helpers ─────────────────────────────────────────────

    def _render_card_pages(
        self, card: BaseCard, total: int, style: epub.EpubItem
    ) -> list[epub.EpubHtml]:
        """Render all EPUB pages for a single card (question + answer/result pages).

        Dynamically dispatches to the correct template set based on card type.
        """
        if isinstance(card, StandardQACard):
            return self._render_standard_qa(card, total, style)
        elif isinstance(card, MultipleChoiceCard):
            return self._render_multiple_choice(card, total, style)
        elif isinstance(card, TrueFalseCard):
            return self._render_true_false(card, total, style)
        elif isinstance(card, CodeRuleCard):
            return self._render_code_rule(card, total, style)
        else:
            raise TypeError(f"Unknown card type: {type(card).__name__}")

    def _render_standard_qa(
        self, card: StandardQACard, total: int, style: epub.EpubItem
    ) -> list[epub.EpubHtml]:
        """Render question page + answer page for a Standard Q/A card."""
        pages: list[epub.EpubHtml] = []
        ctx = {"card": card, "total": total}

        # Question page
        q_template = self.env.get_template("standard_qa.xhtml.j2")
        q_html = q_template.render(**ctx)
        q_page = epub.EpubHtml(
            title=f"Q{card.id}",
            file_name=f"q{card.id}.xhtml",
            lang="en",
            content=q_html.encode("utf-8"),
        )
        q_page.add_item(style)
        pages.append(q_page)

        # Answer page
        a_template = self.env.get_template("standard_qa_answer.xhtml.j2")
        a_html = a_template.render(**ctx)
        a_page = epub.EpubHtml(
            title=f"A{card.id}",
            file_name=f"a{card.id}.xhtml",
            lang="en",
            content=a_html.encode("utf-8"),
        )
        a_page.add_item(style)
        pages.append(a_page)

        return pages

    def _render_multiple_choice(
        self, card: MultipleChoiceCard, total: int, style: epub.EpubItem
    ) -> list[epub.EpubHtml]:
        """Render question page + 4 result pages for a Multiple Choice card."""
        pages: list[epub.EpubHtml] = []
        ctx = {"card": card, "total": total}

        # Question page
        q_template = self.env.get_template("multiple_choice.xhtml.j2")
        q_html = q_template.render(**ctx)
        q_page = epub.EpubHtml(
            title=f"Q{card.id}",
            file_name=f"q{card.id}.xhtml",
            lang="en",
            content=q_html.encode("utf-8"),
        )
        q_page.add_item(style)
        pages.append(q_page)

        # One result page per option
        r_template = self.env.get_template("multiple_choice_result.xhtml.j2")
        for opt_idx in range(4):
            r_html = r_template.render(**ctx, selected_index=opt_idx)
            r_page = epub.EpubHtml(
                title=f"Q{card.id} Result {opt_idx}",
                file_name=f"mcq_result_{card.id}_{opt_idx}.xhtml",
                lang="en",
                content=r_html.encode("utf-8"),
            )
            r_page.add_item(style)
            pages.append(r_page)

        return pages

    def _render_true_false(
        self, card: TrueFalseCard, total: int, style: epub.EpubItem
    ) -> list[epub.EpubHtml]:
        """Render question page + 2 result pages (true/false) for a T/F card."""
        pages: list[epub.EpubHtml] = []
        ctx = {"card": card, "total": total}

        # Question page
        q_template = self.env.get_template("true_false.xhtml.j2")
        q_html = q_template.render(**ctx)
        q_page = epub.EpubHtml(
            title=f"Q{card.id}",
            file_name=f"q{card.id}.xhtml",
            lang="en",
            content=q_html.encode("utf-8"),
        )
        q_page.add_item(style)
        pages.append(q_page)

        # Result page for "True" answer
        r_template = self.env.get_template("true_false_result.xhtml.j2")
        for user_answer, label in [(True, "true"), (False, "false")]:
            r_html = r_template.render(**ctx, user_answer=user_answer)
            r_page = epub.EpubHtml(
                title=f"Q{card.id} — {label}",
                file_name=f"tf_result_{card.id}_{label}.xhtml",
                lang="en",
                content=r_html.encode("utf-8"),
            )
            r_page.add_item(style)
            pages.append(r_page)

        return pages

    def _render_code_rule(
        self, card: CodeRuleCard, total: int, style: epub.EpubItem
    ) -> list[epub.EpubHtml]:
        """Render question page + answer page for a Code Rule card."""
        pages: list[epub.EpubHtml] = []
        ctx = {"card": card, "total": total}

        # Question page
        q_template = self.env.get_template("code_rule.xhtml.j2")
        q_html = q_template.render(**ctx)
        q_page = epub.EpubHtml(
            title=f"Rule {card.id}",
            file_name=f"q{card.id}.xhtml",
            lang="en",
            content=q_html.encode("utf-8"),
        )
        q_page.add_item(style)
        pages.append(q_page)

        # Answer page
        a_template = self.env.get_template("code_rule_answer.xhtml.j2")
        a_html = a_template.render(**ctx)
        a_page = epub.EpubHtml(
            title=f"Rule Answer {card.id}",
            file_name=f"a{card.id}.xhtml",
            lang="en",
            content=a_html.encode("utf-8"),
        )
        a_page.add_item(style)
        pages.append(a_page)

        return pages
