# Lovable UI reference

This folder preserves the most relevant source files from the supplied `lovable-gen-ai-prompt-source.zip`.

The production Streamlit app does not run the React/TanStack project directly. Instead, its visual language was ported into Streamlit-native HTML/CSS and widgets so that the repository remains deployable on Streamlit Community Cloud with `app.py` as the root entry point.

Ported design elements include:

- Navy fixed-style workspace navigation
- Geometric GenAI Prompt brand treatment
- Gradient hero card and accent rule
- Quick-action cards
- Prompt editor and segmented settings layout
- Prompt-strength score ring and quality breakdown
- History, saved prompts, training, settings, and help views
- Soft card borders, rounded controls, blue/mint accents, and responsive layout

The original TypeScript files are retained here only as design provenance and are not required by Streamlit at runtime.
