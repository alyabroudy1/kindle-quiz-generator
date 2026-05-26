#!/usr/bin/env python3
"""
Kindle Quiz Generator — CLI Entry Point.

A professional tool that uses AI (NVIDIA Build API) to generate
validated flashcard/quiz EPUB files optimized for Kindle e-readers.

Usage::

    python main.py

Or with command-line arguments::

    python main.py --topic "Quantum Mechanics" --num-cards 10 --quiz-type standard_qa
"""
from __future__ import annotations

import argparse
import sys

from config import QUIZ_TYPE_REGISTRY, DEFAULT_NUM_CARDS, NVIDIA_API_KEY, AVAILABLE_MODELS, DEFAULT_MODEL
from services.ai_provider import AIProvider
from builders.epub_builder import EpubBuilder


def _print_banner() -> None:
    """Print the application banner."""
    print(
        "\n"
        "╔══════════════════════════════════════════════╗\n"
        "║     📚  Kindle Quiz Generator (Pro)  📚     ║\n"
        "║     Powered by NVIDIA Build API + LLaMA     ║\n"
        "╚══════════════════════════════════════════════╝"
    )


import subprocess

def _interactive_menu() -> tuple[str, int, str, str]:
    """Prompt the user interactively for topic, num_cards, and quiz_type.

    Returns:
    Returns:
        (topic, num_cards, quiz_type_key, model_name)
    """
    # Topic
    topic = input("\n📖 Enter the topic (e.g., 'Quantum Mechanics'): ").strip()
    if not topic:
        print("❌ Topic cannot be empty.")
        sys.exit(1)

    # Number of cards
    num_input = input(
        f"🔢 Number of cards to generate [{DEFAULT_NUM_CARDS}]: "
    ).strip()
    if num_input:
        try:
            num_cards = int(num_input)
            if num_cards < 1:
                raise ValueError
        except ValueError:
            print("❌ Please enter a positive integer.")
            sys.exit(1)
    else:
        num_cards = DEFAULT_NUM_CARDS

    # Quiz type
    print("\n📝 Select quiz type:")
    type_keys = list(QUIZ_TYPE_REGISTRY.keys())
    for i, key in enumerate(type_keys, start=1):
        label = QUIZ_TYPE_REGISTRY[key]["label"]
        print(f"   {i}. {label}")

    choice = input(f"\nEnter choice [1-{len(type_keys)}]: ").strip()
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(type_keys):
            raise ValueError
        quiz_type = type_keys[choice_idx]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        sys.exit(1)

    # Model selection
    print("\n🤖 Select AI Model:")
    model_keys = list(AVAILABLE_MODELS.keys())
    for i, key in enumerate(model_keys, start=1):
        is_default = " (Default)" if AVAILABLE_MODELS[key] == DEFAULT_MODEL else ""
        print(f"   {i}. {key}{is_default}")
    
    choice = input(f"\nEnter choice [1-{len(model_keys)}, or press Enter for Default]: ").strip()
    if choice:
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(model_keys):
                raise ValueError
            model_key = model_keys[choice_idx]
            model_name = AVAILABLE_MODELS[model_key]
        except (ValueError, IndexError):
            print("❌ Invalid choice.")
            sys.exit(1)
    else:
        model_name = DEFAULT_MODEL

    return topic, num_cards, quiz_type, model_name


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Kindle-optimized quiz/flashcard EPUB files using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --topic 'Biology' --num-cards 15 --quiz-type multiple_choice\n"
            "  python main.py -t 'World History' -n 10 -q true_false\n"
        ),
    )
    parser.add_argument(
        "-t", "--topic",
        type=str,
        default=None,
        help="Subject for the flashcards (e.g., 'Quantum Mechanics').",
    )
    parser.add_argument(
        "-n", "--num-cards",
        type=int,
        default=None,
        help=f"Number of cards to generate (default: {DEFAULT_NUM_CARDS}).",
    )
    parser.add_argument(
        "-q", "--quiz-type",
        type=str,
        default=None,
        choices=list(QUIZ_TYPE_REGISTRY.keys()),
        help="Quiz format: standard_qa, multiple_choice, true_false, code_rule, or concept_example.",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Model string to use (e.g. meta/llama-3.1-8b-instruct or ZhipuAI/glm-5.1-9b-instruct).",
    )
    return parser.parse_args()


def _convert_to_azw3(epub_path: str) -> str | None:
    """Attempt to automatically convert EPUB to AZW3 using calibre's ebook-convert."""
    azw3_path = epub_path.rsplit(".", 1)[0] + ".azw3"
    
    # Common locations for calibre's CLI tool on different OSes
    calibre_paths = [
        "ebook-convert", # If in PATH (Linux, Windows, or Mac Homebrew)
        "/Applications/calibre.app/Contents/MacOS/ebook-convert", # Mac default
        "/Applications/Calibre.app/Contents/MacOS/ebook-convert",
        "C:\\Program Files\\Calibre2\\ebook-convert.exe", # Windows default
    ]
    
    for cmd in calibre_paths:
        try:
            # We use run and hide stdout to prevent spamming the console
            result = subprocess.run([cmd, epub_path, azw3_path], capture_output=True, text=True)
            if result.returncode == 0:
                return azw3_path
        except FileNotFoundError:
            continue
    
    return None


def main() -> None:
    """Main entry point — orchestrates the full pipeline."""
    _print_banner()

    # ── Check API key ───────────────────────────────────────────────
    if NVIDIA_API_KEY == "YOUR_NVIDIA_API_KEY_HERE":
        print(
            "\n⚠️  No NVIDIA API key found!\n"
            "   Set it via: export NVIDIA_API_KEY='your-key-here'\n"
            "   Get a free key at: https://build.nvidia.com/\n"
        )
        sys.exit(1)

    # ── Resolve inputs (CLI args or interactive) ────────────────────
    args = _parse_args()

    if args.topic and args.quiz_type:
        topic = args.topic
        num_cards = args.num_cards or DEFAULT_NUM_CARDS
        quiz_type = args.quiz_type
        model_name = args.model or DEFAULT_MODEL
    else:
        topic, num_cards, quiz_type, model_name = _interactive_menu()

    quiz_label = QUIZ_TYPE_REGISTRY[quiz_type]["label"]
    print(f"\n🎯 Topic:      {topic}")
    print(f"   Cards:      {num_cards}")
    print(f"   Quiz type:  {quiz_label}")
    print(f"   Model:      {model_name}")

    # ── Phase 1: AI Generation + Validation ─────────────────────────
    provider = AIProvider()
    cards = provider.generate_cards(
        topic=topic,
        num_cards=num_cards,
        card_model_type=quiz_type,
        model_name=model_name,
    )

    if not cards:
        print(
            "\n❌ No valid cards were generated. "
            "Try a different topic or increase the card count."
        )
        sys.exit(1)

    # ── Phase 2: EPUB Compilation ───────────────────────────────────
    print("\n📖 Building EPUB...")
    builder = EpubBuilder(topic=topic, quiz_type=quiz_type)
    output_path = builder.build(cards)

    # ── Phase 3: Optional Auto-Conversion ───────────────────────────
    print("\n🔄 Attempting auto-conversion to AZW3 for Kindle USB transfer...")
    azw3_path = _convert_to_azw3(output_path)

    # ── Done ────────────────────────────────────────────────────────
    print(
        f"\n{'═' * 50}"
        f"\n✅ Generation completed successfully!"
        f"\n   📁 EPUB: {output_path}"
    )
    if azw3_path:
        print(f"   📁 AZW3: {azw3_path}")
    
    print(
        f"\n"
        f"\n📱 How to transfer to your Kindle:"
        f"\n   Option A (Easiest — Automatic Conversion):"
        f"\n     1. Upload the .epub file using 'Send to Kindle' in your browser:"
        f"\n        👉 https://www.amazon.com/sendtokindle"
        f"\n     2. Or email the .epub to your Send-to-Kindle email address."
        f"\n"
    )
    if azw3_path:
        print(
            f"   Option B (Direct USB Copy):"
            f"\n     Since the file was auto-converted to .azw3, you can simply"
            f"\n     connect your Kindle via USB and drag & drop the .azw3 file"
            f"\n     into the 'documents' folder."
        )
    else:
        print(
            f"   Option B (Direct USB Copy — Requires Manual Conversion first):"
            f"\n     Kindles do not natively read .epub files copied directly via USB."
            f"\n     To copy via USB, install Calibre and convert the file to .azw3 or .mobi first:"
            f"\n       calibre: ebook-convert {output_path} output.azw3"
            f"\n     Then drag and drop the converted .azw3 into your Kindle's 'documents' folder."
        )
    print(f"{'═' * 50}\n")


if __name__ == "__main__":
    main()
