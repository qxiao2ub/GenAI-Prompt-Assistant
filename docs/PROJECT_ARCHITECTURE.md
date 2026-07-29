# Project Architecture

```text
User prompt / uploaded examples
             |
             v
     Text validation and cleaning
             |
             +--------------------+
             |                    |
             v                    v
   N-gram continuation      TF-IDF similarity
             |                    |
             +---------+----------+
                       v
             Context-aware candidates
                       |
                       v
          Accept/reject feedback ranker
                       |
                       v
        Ranked suggestions and insights
```

## Components

- **Input layer:** writing context, current prompt, optional CSV history.
- **Preprocessing layer:** whitespace normalization, tokenization, context validation.
- **Prediction layer:** local n-gram continuation and TF-IDF similarity retrieval.
- **Fallback layer:** context-specific templates for email, search, notes, reports, and general writing.
- **Feedback layer:** bandit-style source ranking using accept/reject interactions in the current Streamlit session.
- **Output layer:** ranked suggestions, behavior insights, downloadable session profile, and downloadable CSV.

## Scope

This is a lightweight educational and portfolio prototype. It does not use an external generative-AI API or persist user content in a database. A production implementation would need authentication, encrypted storage, consent management, retention controls, stronger evaluation, and platform-specific integrations.
