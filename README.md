# GenAI Prompt Assistant

**Author:** Yashvi Mehta  
**Mentor:** Dr. Qingyang Xiao

GenAI Prompt Assistant is a privacy-first Streamlit prototype that learns from approved writing examples and proposes next phrases for emails, notes, reports, general writing, and online-search prompts.

The app name, browser-page title, main-page heading, sidebar heading, author, and mentor information have all been updated in this repository.

## Live app capabilities

- Accepts a partial phrase, sentence, paragraph, or search prompt.
- Supports `email`, `search`, `note`, `report`, and `general` writing contexts.
- Generates lightweight local next-phrase suggestions.
- Learns from built-in examples, an uploaded CSV, and optional session text.
- Uses TF-IDF similarity to retrieve relevant prior writing patterns.
- Uses an n-gram predictor to estimate likely continuations.
- Adds context-aware fallback suggestions when training history is limited.
- Accepts positive or negative feedback and ranks suggestion sources using a bandit-style score.
- Displays behavior insights such as example counts, context counts, common terms, and average content length.
- Downloads the session learning profile as JSON and approved session examples as CSV.
- Requires no API key and calls no external AI service.

## Branding

The Streamlit interface displays:

```text
GenAI Prompt Assistant
Author: Yashvi Mehta
Mentor: Dr. Qingyang Xiao
```

The author and mentor appear in both places requested:

1. At the top of the left sidebar.
2. Directly below the app title on the main page.

## Repository structure

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- LICENSE
|-- .gitignore
|-- .streamlit/
|   `-- config.toml
|-- data/
|   `-- sample_user_history.csv
|-- notebooks/
|   `-- GenAI_Prompt_Assistant_Colab.ipynb
|-- docs/
|   |-- PROJECT_ARCHITECTURE.md
|   `-- STREAMLIT_DEPLOYMENT.md
`-- tests/
    `-- test_static_checks.py
```

## Why this version is Streamlit-ready

The entrypoint is the root-level `app.py`. It contains the complete prediction engine and does not import a local `src` package. This prevents the earlier deployment failure:

```text
ModuleNotFoundError: No module named 'src'
```

The sample-data path is resolved relative to `app.py`, instead of depending on the server's current working directory:

```python
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "sample_user_history.csv"
```

## Quick local test

Python 3.11 or newer is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the local address displayed by Streamlit, usually `http://localhost:8501`.

## Upload to GitHub

1. Download and extract the ZIP file.
2. Create a new GitHub repository, such as `genai-prompt-assistant`.
3. Upload the **extracted contents** of the project folder.
4. Confirm that these files are at the repository root:

```text
app.py
requirements.txt
README.md
```

5. Commit the files to the `main` branch.

Do not upload only the ZIP file. GitHub must contain the extracted files and folders so Streamlit can access them.

## Deploy to Streamlit Community Cloud

Use these values when creating the Streamlit app:

```text
Branch: main
Main file path: app.py
```

No secrets or API keys are required.

A more detailed procedure is available in [`docs/STREAMLIT_DEPLOYMENT.md`](docs/STREAMLIT_DEPLOYMENT.md).

## CSV history format

The app works without an upload by using fictional sample data. A custom CSV must contain the following required column:

```text
user_input
```

It may also contain this optional column:

```text
context
```

Suggested context values are:

```text
email
search
note
report
general
```

Example:

```csv
context,user_input
email,"Dear team, thank you for the update. I will review the document and respond by Friday."
search,"beginner guide to deploying a Streamlit app from GitHub"
note,"The user should control which examples the assistant learns from."
```

## Model pipeline

### 1. Text preprocessing

The app normalizes spacing, tokenizes the writing examples, removes common stop words for similarity analysis, and validates the CSV schema.

### 2. N-gram next-phrase prediction

The local n-gram model learns which token commonly follows the preceding tokens in the approved writing history. It uses shorter-context backoff and unigram frequencies when an exact sequence is unavailable.

### 3. TF-IDF personalization

A small TF-IDF implementation converts prior writing examples and the current prompt into weighted term vectors. Cosine similarity identifies the closest prior example, from which the app derives a possible continuation.

### 4. Context-aware fallback generation

When local history is sparse, the app adds templates appropriate for email, search, notes, reports, or general writing.

### 5. Feedback-based ranking

Accept and reject buttons update a simple bandit-style score for each suggestion source. Sources with stronger positive session feedback are ranked higher on later generations.

## Privacy and responsible use

This prototype:

- Does not call an external AI API.
- Does not require an API key.
- Does not use a persistent database.
- Keeps feedback and newly learned text in the active Streamlit session unless the user downloads it.
- Uses fictional sample content.

Before converting this into a production keyboard, browser extension, email assistant, or mobile app, add explicit consent, secure authentication, encrypted storage, configurable retention, data deletion, abuse prevention, and independent privacy/security review.

## Limitations

- The local model is an educational prototype, not a large language model.
- N-gram predictions can repeat frequent tokens and are limited by the available writing history.
- TF-IDF measures lexical similarity rather than deep semantic meaning.
- Feedback is session-based and is not retained after the Streamlit session ends.
- The app does not integrate directly with email clients, browsers, or mobile keyboards.

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'`

This repository does not use `src` imports. Seeing this error means Streamlit is deploying an older commit or the wrong entrypoint. Confirm that the selected main file is the new root-level `app.py`, then reboot or redeploy.

### App still shows the old Yashvi title

Confirm that GitHub's current `app.py` contains:

```python
APP_NAME = "GenAI Prompt Assistant"
```

Then reboot the Streamlit app or clear its cache.

### Sample CSV cannot be found

Keep this file in the repository:

```text
data/sample_user_history.csv
```

The app also has built-in fallback examples, so it remains usable if the demo CSV is unavailable.

### Uploaded CSV is rejected

Check that the file has a column named exactly `user_input`. The optional context column must be named exactly `context`.

## Colab notebook

The repository includes an updated copy of the original notebook:

```text
notebooks/GenAI_Prompt_Assistant_Colab.ipynb
```

It is included for portfolio documentation, experimentation, and Google Colab use. Streamlit deploys only the root `app.py`.

## Portfolio value

This repository demonstrates:

- Product and user-experience design
- Text preprocessing
- Lightweight machine learning
- Personalized information retrieval
- Online feedback ranking
- Streamlit development
- GitHub repository organization
- Deployment documentation
- Privacy-aware prototyping

## License

Released under the MIT License for educational and portfolio use. See [`LICENSE`](LICENSE).
