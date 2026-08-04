# Project architecture

## Presentation layer

`app.py` contains a Streamlit-native implementation of the supplied Lovable visual system. The application exposes six views through one Streamlit entry point:

1. Workspace
2. History
3. Saved Prompts
4. Training
5. Settings
6. Help

Custom CSS reproduces the navy application shell, gradient hero, rounded cards, prompt-strength score ring, blue/mint accents, and responsive layout.

## Prompt intelligence layer

- Prompt-quality analyzer: clarity, specificity, context, constraints, and examples
- Improved-prompt builder: role, task, audience, tone, length, output format, and model-specific guidance
- N-gram predictor: learns likely token continuations from approved history
- TF-IDF personalization: identifies locally similar writing examples
- Context templates: provide stable fallback continuations
- Bandit-style feedback ranker: reorders suggestion sources from accept/reject feedback

## Data layer

- `data/sample_user_history.csv`: fictional demo history
- Uploaded CSV: active-session personalization
- `st.session_state`: prompt history, saved prompts, feedback, settings, and session examples
- Downloaded JSON: portable session profile

## Deployment layer

Streamlit Community Cloud launches the root `app.py`. `requirements.txt` contains the only runtime Python dependencies. The React/TanStack source is not required at runtime; selected design files are retained in `ui_reference/`.
