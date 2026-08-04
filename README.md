# GenAI Prompt Assistant - Lovable UI + Streamlit Core

A GitHub-ready Streamlit application that combines the functional ML prototype from `GenAI_Prompt_Assistant_Streamlit_GitHub.zip` with the visual system supplied in `lovable-gen-ai-prompt-source.zip`.

**Author:** Yashvi Mehta  
**Mentor:** Dr. Qingyang Xiao

## What was integrated

The original core repository supplied the working Python models, sample data, Colab notebook, session feedback ranker, and Streamlit deployment structure. The Lovable repository supplied the product design language and page architecture.

This integrated version ports the Lovable experience into Streamlit-native components:

- Navy workspace sidebar and GenAI Prompt brand mark
- Gradient welcome hero and quick-action cards
- Prompt editor with example starters
- Target AI, context, audience, tone, length, and output format controls
- Live prompt-quality score with clarity, specificity, context, constraints, and example breakdowns
- Smart prompt-improvement recommendations
- Personalized next-phrase suggestions from local n-gram and TF-IDF models
- Accept/reject feedback ranking
- Before-and-after prompt comparison
- Prompt history
- Saved-prompt library and reusable templates
- Training-data dashboard
- Settings and quick-start pages
- Author and mentor credits in the sidebar and footer

The app remains a single Streamlit deployment. It does not require Node.js, npm, React, or a separate front-end hosting service.

## Repository structure

```text
GenAI_Prompt_Assistant_Lovable_Integrated/
├── app.py                         # Streamlit Cloud entry point
├── requirements.txt              # Python dependencies
├── README.md                      # This guide
├── LICENSE
├── data/
│   └── sample_user_history.csv
├── notebooks/
│   └── GenAI_Prompt_Assistant_Colab.ipynb
├── assets/
│   └── favicon.svg
├── .streamlit/
│   └── config.toml
├── docs/
│   ├── PROJECT_ARCHITECTURE.md
│   └── STREAMLIT_DEPLOYMENT.md
├── tests/
│   └── test_static_checks.py
└── ui_reference/                 # Selected supplied Lovable design source
    ├── README.md
    ├── app-shell.tsx
    ├── brand-logo.tsx
    ├── prompt-engine.ts
    ├── score-ring.tsx
    ├── styles.css
    └── workspace-index.tsx
```

## Streamlit Cloud deployment

### 1. Extract the ZIP

Download and extract the generated repository ZIP. Do not upload only the compressed ZIP as the GitHub repository contents.

### 2. Create a GitHub repository

Create a new empty GitHub repository, for example:

```text
genai-prompt-assistant
```

Upload all extracted files and folders so that `app.py` and `requirements.txt` are visible at the repository root.

### 3. Confirm the root layout

The GitHub repository root must look like:

```text
app.py
requirements.txt
README.md
data/
.streamlit/
```

Do not place all files inside an additional nested directory.

### 4. Deploy on Streamlit Community Cloud

Create a new Streamlit app and select:

```text
Repository: your-account/genai-prompt-assistant
Branch: main
Main file path: app.py
```

No API secrets are required for this local-ML prototype.

## Run locally

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
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

Open the local URL displayed by Streamlit, normally `http://localhost:8501`.

## CSV personalization format

The sidebar accepts a CSV with one required column and one optional column:

```csv
context,user_input
email,"Dear team, thank you for the update."
search,"best beginner Python project ideas"
report,"The project includes preprocessing, prediction, feedback, and a user interface."
```

Required:

- `user_input`

Optional:

- `context`

When `context` is missing, the app assigns `general`.

## Model pipeline

### N-gram continuation model

The app learns common token transitions from approved writing samples and proposes likely next phrases.

### Local TF-IDF personalization

The current prompt is compared with prior samples. A related excerpt can be used as a personalized continuation.

### Context templates

Email, search, note, report, and general templates provide reliable fallback suggestions.

### Prompt-quality analyzer

A lightweight heuristic layer scores:

- Clarity
- Specificity
- Context
- Constraints
- Examples

It then proposes practical fixes that can be applied to the improved prompt.

### Feedback ranker

Accept/reject actions update a small bandit-style score in Streamlit session state. Sources that receive positive feedback rank higher later in the session.

## Privacy behavior

- No external AI API is called.
- No API key is required.
- Uploaded CSV data is used only within the active Streamlit process/session.
- Session history is not written to a production database.
- Users can download their profile data as JSON.

For production use, add authentication, encrypted persistent storage, consent flows, deletion controls, moderation, audit logs, and a formal security/privacy review.

## Important implementation note

The Lovable source is a React/TanStack project. Streamlit Community Cloud launches Python entry points, not a separate Vite front end. Therefore, this repository uses a Streamlit-native port of the Lovable design rather than attempting to run both servers. The selected original design files remain in `ui_reference/` for provenance and future front-end work.

## Testing

Run the static deployment tests with:

```bash
python -m pytest -q
```

A direct syntax check is also available:

```bash
python -m py_compile app.py
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'`

This integrated `app.py` is self-contained and does not import a local Python `src` package. Confirm that Streamlit is deploying the new repository and that the main file path is exactly `app.py`.

### The old interface still appears

In Streamlit Community Cloud, open **Manage app**, reboot the app, and confirm the latest GitHub commit is deployed.

### Sample data cannot be found

Keep this path unchanged in the repository:

```text
data/sample_user_history.csv
```

The app resolves it relative to `app.py`, so it does not depend on the server working directory.

### Uploaded CSV is rejected

Confirm that the header includes exactly:

```text
user_input
```

The optional header is:

```text
context
```

## Portfolio use

This project demonstrates:

- Python application engineering
- Streamlit product development
- Local NLP and recommendation logic
- Prompt-quality analysis
- Feedback-driven ranking
- Responsive UI translation from a React design system
- GitHub packaging and cloud deployment
- Privacy-first prototype planning

## License

See `LICENSE`.
