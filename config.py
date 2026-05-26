"""
Configuration for the Kindle Quiz Generator.

Uses NVIDIA Build API (free tier) which is 100% OpenAI-compatible.
Set NVIDIA_API_KEY as an environment variable before running.
"""
import os

# ──────────────────────────────────────────────
# NVIDIA API Configuration (Free tier)
# ──────────────────────────────────────────────
NVIDIA_API_KEY: str = os.environ.get("NVIDIA_API_KEY", "YOUR_NVIDIA_API_KEY_HERE")
NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

# Available Free NVIDIA Models
AVAILABLE_MODELS: dict[str, str] = {
    # Llama Family
    "llama-3.1-8b (Fast)": "meta/llama-3.1-8b-instruct",
    "llama-3.1-70b (Medium)": "meta/llama-3.1-70b-instruct",
    "llama-3.2-3b (Very Fast)": "meta/llama-3.2-3b-instruct",
    "llama-3.3-70b (Medium)": "meta/llama-3.3-70b-instruct",
    
    # NVIDIA Optimized
    "nemotron-70b (Medium)": "nvidia/llama-3.1-nemotron-70b-instruct",
    "mistral-nemo-12b (Fast)": "nv-mistralai/mistral-nemo-12b-instruct",

    # Google Gemma
    "gemma-2-2b-it (Very Fast)": "google/gemma-2-2b-it",
    "gemma-3-12b-it (Fast)": "google/gemma-3-12b-it",
    "gemma-4-31b-it (Medium)": "google/gemma-4-31b-it",

    # Mistral Family
    "mistral-7b (Fast)": "mistralai/mistral-7b-instruct-v0.3",
    "mistral-large-2 (Medium)": "mistralai/mistral-large-2-instruct",
    "mixtral-8x7b (Medium)": "mistralai/mixtral-8x7b-instruct-v0.1",
    "mixtral-8x22b (Slow)": "mistralai/mixtral-8x22b-v0.1",

    # Microsoft Phi
    "phi-3.5-moe (Fast)": "microsoft/phi-3.5-moe-instruct",
    "phi-4-mini (Very Fast)": "microsoft/phi-4-mini-instruct",

    # IBM Granite
    "granite-3.0-8b (Fast)": "ibm/granite-3.0-8b-instruct",
    "granite-34b-code (Medium)": "ibm/granite-34b-code-instruct",

    # Qwen & DeepSeek
    "qwen3-coder-480b (Slow)": "qwen/qwen3-coder-480b-a35b-instruct",
    
    # Others
    "solar-10.7b (Fast)": "upstage/solar-10.7b-instruct",
    "glm-5.1 (Slow)": "z-ai/glm-5.1",
}

# Recommended default model
DEFAULT_MODEL: str = "meta/llama-3.1-8b-instruct"

# ──────────────────────────────────────────────
# Validation Rules
# ──────────────────────────────────────────────
MIN_CONFIDENCE_SCORE: float = 0.9
DEFAULT_NUM_CARDS: int = 20

# ──────────────────────────────────────────────
# Output
# ──────────────────────────────────────────────
OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# ──────────────────────────────────────────────
# Template ↔ Model Registry
# ──────────────────────────────────────────────
# Maps quiz type string → (Pydantic model import path, Jinja2 template filename)
# New quiz styles only need a new entry here + their model + template files.
QUIZ_TYPE_REGISTRY: dict[str, dict[str, str]] = {
    "standard_qa": {
        "model_module": "models.standard_qa",
        "model_class": "StandardQACard",
        "template": "standard_qa.xhtml.j2",
        "label": "Standard Q/A",
    },
    "multiple_choice": {
        "model_module": "models.multiple_choice",
        "model_class": "MultipleChoiceCard",
        "template": "multiple_choice.xhtml.j2",
        "label": "Multiple Choice",
    },
    "true_false": {
        "model_module": "models.true_false",
        "model_class": "TrueFalseCard",
        "template": "true_false.xhtml.j2",
        "label": "True/False",
    },
    "code_rule": {
        "model_module": "models.code_rule",
        "model_class": "CodeRuleCard",
        "template": "code_rule.xhtml.j2",
        "label": "Code Rule / Comparison",
    },
    "concept_example": {
        "model_module": "models.concept_example",
        "model_class": "ConceptExampleCard",
        "template": "concept_example.xhtml.j2",
        "label": "Concept & Example",
    },
}
