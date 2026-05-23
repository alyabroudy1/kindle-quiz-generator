# Kindle Quiz Generator 📚

A professional Python CLI tool that uses AI (NVIDIA Build API with LLaMA 3.1, GLM, etc.) to generate validated, Kindle-optimized flashcard and quiz EPUB files. It handles complex AI JSON schemas, validates the output using Pydantic, and creates beautifully formatted quizzes tailored for e-ink displays.

## Features
- **Dynamic AI Model Selection**: Choose between models like `meta/llama-3.1-8b-instruct`, `ZhipuAI/glm-5.1-9b-instruct`, and others.
- **Multiple Quiz Types**:
  - **Standard Q/A**: Simple Question & Answer flashcards.
  - **Multiple Choice (MCQ)**: Questions with 4 options and dedicated result pages.
  - **True/False**: Statement-based questions with True/False evaluations.
  - **Code Rule**: Displays a coding rule, an incorrect code block to evaluate, and the correct code block with explanations.
- **Batched Generation**: Safely generates large numbers of cards (e.g., 75+) by chunking requests and passing previous context to prevent duplicates.
- **Strict Validation**: Uses Pydantic to ensure all cards have the correct schema, discarding low-confidence or hallucinated results.
- **Auto AZW3 Conversion**: Automatically converts generated `.epub` files into Kindle-native `.azw3` format if Calibre is installed.

## Prerequisites & Installation

1. **Python 3.9+** is required.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Requires: `openai`, `pydantic`, `ebooklib`, `jinja2`)*

3. **NVIDIA API Key (Free)**:
   This tool uses the NVIDIA Build API, which provides free API access to top open-source models.
   - Go to [build.nvidia.com](https://build.nvidia.com/)
   - Create a free developer account and generate an API Key.
   - Set it as an environment variable in your terminal:
     ```bash
     export NVIDIA_API_KEY="nvapi-your-key-here"
     ```

4. **Calibre (Optional, but highly recommended for USB transfers)**:
   If you want the tool to automatically convert the `.epub` files to `.azw3` so you can copy them directly to your Kindle via USB, install Calibre.
   - **On macOS (using Homebrew)**:
     ```bash
     brew install --cask calibre
     ```
   - *If Calibre is not installed, the tool will still successfully generate `.epub` files.*

## Usage

You can run the script interactively or via command-line arguments.

### Interactive Mode
Simply run the script with no arguments. It will prompt you for the topic, the number of cards, the quiz type, and the AI model you want to use.
```bash
python3 main.py
```

### Command-Line Arguments
If you prefer to skip the interactive prompts, you can pass the configuration directly:
```bash
python3 main.py --topic "Software Engineering Principles" --num-cards 20 --quiz-type code_rule --model meta/llama-3.1-8b-instruct
```

## How to Transfer Quizzes to your Kindle

Kindle e-readers (like the Paperwhite 10th Gen) **do not** natively read `.epub` files transferred directly over USB. You have two options:

### Option A: Send to Kindle (Easiest — No Calibre required)
Amazon will automatically convert your `.epub` file and sync it to your Kindle over Wi-Fi.
1. Open the [Amazon Send to Kindle](https://www.amazon.com/sendtokindle) web portal in your browser.
2. Drag and drop the generated `.epub` file (found in the `output/` folder) into the webpage.
3. Turn on your Kindle's Wi-Fi, and the quiz will appear in your library shortly.

### Option B: Direct USB Transfer
If you want to transfer offline via USB, the file **must** be converted to `.azw3` or `.mobi`. 
1. If you installed Calibre (`brew install --cask calibre`), this tool will automatically create an `.azw3` version alongside the `.epub` in the `output/` folder.
2. If you need to convert it manually, run:
   ```bash
   ebook-convert output/Flashcards_topic.epub output/Flashcards_topic.azw3
   ```
3. Connect your Kindle via USB and drag the `.azw3` file directly into the `documents/` folder on the Kindle drive.

## Project Structure
```text
kindle-quiz-generator/
├── main.py                # CLI entry point
├── config.py              # Centralized configuration (Models, validation rules, registries)
├── requirements.txt       # Python dependencies
├── builders/
│   └── epub_builder.py    # Assembles templates into an EPUB using ebooklib
├── models/
│   ├── base.py            # Abstract BaseCard
│   ├── standard_qa.py     # Q/A model
│   ├── multiple_choice.py # MCQ model
│   ├── true_false.py      # T/F model
│   └── code_rule.py       # Code Rule model
├── services/
│   └── ai_provider.py     # Handles batched NVIDIA API calls and strict Pydantic validation
└── templates/             # Jinja2 XHTML templates and CSS
    ├── styles/
    │   └── kindle.css
    ├── index.xhtml.j2
    ├── standard_qa.xhtml.j2
    └── ...
```
