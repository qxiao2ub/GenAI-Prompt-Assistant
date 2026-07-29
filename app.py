from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st

APP_NAME = "GenAI Prompt Assistant"
AUTHOR_NAME = "Yashvi Mehta"
MENTOR_NAME = "Dr. Qingyang Xiao"
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "sample_user_history.csv"

DEFAULT_EXAMPLES = [
    {
        "context": "email",
        "user_input": "Hi Professor, I hope you are doing well. I wanted to ask about the assignment deadline and whether there is any flexibility this week.",
    },
    {
        "context": "email",
        "user_input": "Dear team, thank you for the updates. I reviewed the draft and added a few comments about the timeline and deliverables.",
    },
    {
        "context": "email",
        "user_input": "Could we schedule a short meeting next week to discuss the project plan and the remaining action items?",
    },
    {
        "context": "search",
        "user_input": "best way to build a Streamlit app from a Python notebook and deploy it for a portfolio project",
    },
    {
        "context": "search",
        "user_input": "privacy friendly design patterns for apps that learn from user typing behavior",
    },
    {
        "context": "note",
        "user_input": "The assistant should learn from previous writing patterns and suggest the next phrase without interrupting the user.",
    },
    {
        "context": "note",
        "user_input": "The app should allow users to accept, reject, or edit suggestions so the model can improve over time.",
    },
    {
        "context": "report",
        "user_input": "Machine learning is used to identify writing habits, repeated phrases, topic preferences, and context-specific behavior.",
    },
    {
        "context": "report",
        "user_input": "The final deliverable includes a Colab notebook, a Streamlit app, documentation, and a GitHub-ready project structure.",
    },
]

TEMPLATES: Dict[str, List[str]] = {
    "email": [
        "I hope you are doing well. I wanted to follow up on",
        "Thank you for your time and feedback. The next step is",
        "Please let me know if there is anything else I should prepare.",
    ],
    "search": [
        "with examples, code, and best practices",
        "comparison of beginner-friendly tools and deployment options",
        "privacy and safety considerations for implementation",
    ],
    "note": [
        "This will make the product more trustworthy and easier to explain.",
        "The user should stay in control of storage, suggestions, and feedback.",
        "A simple prototype can demonstrate the idea before a full product is built.",
    ],
    "report": [
        "This section will be included in the final README and project presentation.",
        "The system architecture includes preprocessing, prediction, feedback, and user interface layers.",
        "The model can improve when users accept, reject, or edit suggestions.",
    ],
    "general": [
        "Here is a clear next step to continue the thought.",
        "This can be improved by adding a specific example and action item.",
        "The main idea is to keep the user in control while saving time.",
    ],
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "he", "in", "is", "it", "its", "of", "on", "or", "that", "the", "this",
    "to", "was", "were", "will", "with", "you", "your", "i", "we", "our",
}


def normalize_text(text: str) -> str:
    """Trim text and collapse repeated whitespace."""
    return re.sub(r"\s+", " ", str(text or "").strip())


def tokens(text: str) -> List[str]:
    """Simple tokenizer used by the local ML models."""
    return re.findall(r"[A-Za-z0-9']+|[.,!?;]", normalize_text(text).lower())


def content_tokens(text: str) -> List[str]:
    """Tokens used for similarity and insights."""
    return [t for t in tokens(text) if t not in STOP_WORDS and re.search(r"[A-Za-z0-9]", t)]


def detokenize(token_list: Sequence[str]) -> str:
    """Convert tokens back into readable text."""
    text = " ".join(token_list)
    text = re.sub(r"\s+([.,!?;])", r"\1", text)
    return text.strip()


def default_history_df() -> pd.DataFrame:
    """Return built-in sample history data for the demo."""
    return pd.DataFrame(DEFAULT_EXAMPLES)


def clean_history_df(history_df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean a user history dataframe.

    Required CSV column:
    - user_input

    Optional CSV column:
    - context, such as email, search, note, report, or general
    """
    if history_df is None or history_df.empty:
        return default_history_df()

    df = history_df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if "user_input" not in df.columns:
        raise ValueError("The CSV must include a column named 'user_input'.")
    if "context" not in df.columns:
        df["context"] = "general"

    df = df[["context", "user_input"]].copy()
    df["context"] = df["context"].fillna("general").astype(str).str.lower().str.strip()
    df["user_input"] = df["user_input"].fillna("").astype(str).map(normalize_text)
    df = df[df["user_input"].str.len() > 0].reset_index(drop=True)
    return df if not df.empty else default_history_df()


class NGramPredictor:
    """A small n-gram next-token predictor.

    This model learns which words often follow the recent words in the user's
    approved writing history. It is intentionally small so the Streamlit demo
    runs without external APIs, API keys, or large model downloads.
    """

    def __init__(self, n: int = 3):
        if n < 2:
            raise ValueError("n must be at least 2")
        self.n = n
        self.table: defaultdict[Tuple[str, ...], Counter] = defaultdict(Counter)
        self.backoff: defaultdict[Tuple[str, ...], Counter] = defaultdict(Counter)
        self.unigram: Counter = Counter()

    def fit(self, corpus: Iterable[str]) -> "NGramPredictor":
        for doc in corpus:
            t = tokens(doc)
            self.unigram.update(t)
            for i in range(len(t) - self.n + 1):
                key = tuple(t[i : i + self.n - 1])
                nxt = t[i + self.n - 1]
                self.table[key][nxt] += 1
            for i in range(len(t) - 1):
                self.backoff[(t[i],)][t[i + 1]] += 1
        return self

    def predict_continuation(self, prefix: str, max_words: int = 10) -> str:
        prefix_tokens = tokens(prefix)
        output: List[str] = []
        working = prefix_tokens[:]

        for _ in range(max_words):
            key = tuple(working[-(self.n - 1) :]) if len(working) >= self.n - 1 else tuple(working)
            candidates = self.table.get(key)
            if not candidates and working:
                candidates = self.backoff.get((working[-1],))
            if not candidates:
                candidates = self.unigram
            if not candidates:
                break

            nxt = candidates.most_common(1)[0][0]
            if nxt in [".", "!", "?"] and not output:
                break
            output.append(nxt)
            working.append(nxt)
            if nxt in [".", "!", "?"]:
                break

        return detokenize(output)


class TfidfSimilarity:
    """Tiny TF-IDF similarity model implemented with the Python standard library."""

    def __init__(self, documents: Sequence[str]):
        self.documents = [normalize_text(d) for d in documents]
        self.doc_tokens = [content_tokens(d) for d in self.documents]
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self._fit()

    def _fit(self) -> None:
        n_docs = max(len(self.doc_tokens), 1)
        df_counter = Counter()
        for doc in self.doc_tokens:
            df_counter.update(set(doc))
        self.idf = {term: math.log((1 + n_docs) / (1 + df)) + 1.0 for term, df in df_counter.items()}
        self.doc_vectors = [self._vector_from_tokens(doc) for doc in self.doc_tokens]

    def _vector_from_tokens(self, toks: Sequence[str]) -> Dict[str, float]:
        counts = Counter(toks)
        if not counts:
            return {}
        total = float(sum(counts.values()))
        return {term: (count / total) * self.idf.get(term, 1.0) for term, count in counts.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a).intersection(b)
        dot = sum(a[t] * b[t] for t in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def most_similar(self, prompt: str) -> Tuple[Optional[int], float]:
        q_vec = self._vector_from_tokens(content_tokens(prompt))
        if not q_vec or not self.doc_vectors:
            return None, 0.0
        scores = [self._cosine(q_vec, vec) for vec in self.doc_vectors]
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        return best_idx, float(scores[best_idx])


@dataclass(frozen=True)
class Suggestion:
    source: str
    text: str
    reason: str

    def as_dict(self) -> Dict[str, str]:
        return {"source": self.source, "text": self.text, "reason": self.reason}


class SuggestionEngine:
    """Combines n-gram prediction, TF-IDF personalization, and templates."""

    def __init__(self, history_df: pd.DataFrame):
        self.df = clean_history_df(history_df)
        self.corpus = self.df["user_input"].tolist()
        self.ngram = NGramPredictor(n=3).fit(self.corpus)
        self.similarity = TfidfSimilarity(self.corpus)

    def similar_text(self, prompt: str, context: str) -> Optional[str]:
        if not normalize_text(prompt):
            return None
        idx, score = self.similarity.most_similar(prompt)
        if idx is None:
            return None
        context_bonus = 0.05 if str(self.df.loc[idx, "context"]).lower() == context.lower() else 0.0
        if score + context_bonus <= 0.02:
            return None
        return self.corpus[idx]

    @staticmethod
    def continuation_from_similar(prompt: str, similar: str) -> str:
        """Return a useful continuation or excerpt from a similar prior example."""
        prompt_words = content_tokens(prompt)
        similar_words = normalize_text(similar).split()
        if not prompt_words:
            return " ".join(similar_words[:18])

        lower_words = [re.sub(r"[^A-Za-z0-9']+", "", w).lower() for w in similar_words]
        last = prompt_words[-1]
        if last in lower_words:
            pos = lower_words.index(last)
            return " ".join(similar_words[pos + 1 : pos + 16]).strip(" ,") or " ".join(similar_words[:18])
        return " ".join(similar_words[:18])

    def suggestions(self, prompt: str, context: str = "general", top_k: int = 5) -> List[Dict[str, str]]:
        prompt = normalize_text(prompt)
        context = (context or "general").lower()
        candidates: List[Suggestion] = []

        continuation = self.ngram.predict_continuation(prompt, max_words=10)
        if continuation:
            candidates.append(
                Suggestion(
                    source="ml_ngram",
                    text=continuation,
                    reason="learned from repeated phrase patterns in the writing history",
                )
            )

        similar = self.similar_text(prompt, context)
        if similar:
            candidates.append(
                Suggestion(
                    source="tfidf_personalization",
                    text=self.continuation_from_similar(prompt, similar),
                    reason="matched a similar prior writing example using local TF-IDF similarity",
                )
            )

        for template in TEMPLATES.get(context, TEMPLATES["general"]):
            candidates.append(
                Suggestion(
                    source="context_template",
                    text=template,
                    reason=f"fallback suggestion for the {context} context",
                )
            )

        if prompt:
            candidates.append(
                Suggestion(
                    source="clarity_rewrite",
                    text="Consider adding a specific next action, owner, or deadline to make this more useful.",
                    reason="general writing improvement heuristic",
                )
            )

        seen = set()
        unique: List[Dict[str, str]] = []
        for item in candidates:
            text = normalize_text(item.text)
            if not text or text.lower() in seen:
                continue
            seen.add(text.lower())
            unique.append(Suggestion(item.source, text, item.reason).as_dict())
            if len(unique) >= top_k:
                break
        return unique

    def behavior_insights(self) -> Dict[str, object]:
        context_counts = self.df["context"].value_counts().to_dict()
        all_terms = Counter()
        for doc in self.corpus:
            all_terms.update(content_tokens(doc))
        common_terms = all_terms.most_common(10)
        avg_words = sum(len(content_tokens(doc)) for doc in self.corpus) / max(len(self.corpus), 1)
        return {
            "num_examples": int(len(self.df)),
            "contexts": context_counts,
            "common_terms": common_terms,
            "avg_content_words": round(float(avg_words), 1),
        }


class BanditRanker:
    """Simple accept/reject ranker stored in Streamlit session state."""

    def __init__(self):
        if "bandit" not in st.session_state:
            st.session_state["bandit"] = {}

    def score(self, source: str) -> float:
        record = st.session_state["bandit"].get(source, {"accepted": 0, "shown": 0})
        accepted = record.get("accepted", 0)
        shown = record.get("shown", 0)
        return (accepted + 1.0) / (shown + 2.0)

    def update(self, source: str, accepted: bool) -> None:
        record = st.session_state["bandit"].setdefault(source, {"accepted": 0, "shown": 0})
        record["shown"] += 1
        if accepted:
            record["accepted"] += 1

    def rank(self, suggestions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return sorted(suggestions, key=lambda item: self.score(item["source"]), reverse=True)


@st.cache_data(show_spinner=False)
def load_default_history() -> pd.DataFrame:
    if DATA_PATH.exists():
        return clean_history_df(pd.read_csv(DATA_PATH))
    return default_history_df()


def read_uploaded_history(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return load_default_history()
    try:
        return clean_history_df(pd.read_csv(uploaded_file))
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        return load_default_history()


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_session() -> None:
    st.session_state.setdefault("session_history", [])
    st.session_state.setdefault("last_suggestions", [])
    st.session_state.setdefault("last_prompt", "")
    st.session_state.setdefault("last_context", "email")


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="✨", layout="wide")
    initialize_session()

    st.title(APP_NAME)
    st.markdown(
        f"**Author:** {AUTHOR_NAME} &nbsp;&nbsp; | &nbsp;&nbsp; **Mentor:** {MENTOR_NAME}"
    )
    st.caption(
        "A GitHub-ready Streamlit prototype that learns from approved writing examples "
        "and suggests next phrases for email, notes, reports, and searches."
    )

    with st.sidebar:
        st.header(APP_NAME)
        st.markdown(f"**Author:** {AUTHOR_NAME}")
        st.markdown(f"**Mentor:** {MENTOR_NAME}")
        st.divider()
        st.header("Project controls")
        uploaded = st.file_uploader("Optional: upload writing history CSV", type=["csv"])
        st.markdown(
            "CSV format: one required column named `user_input`; optional column named `context`. "
            "The app runs without uploading any file by using sample demo data."
        )
        st.divider()
        st.subheader("Privacy-first demo")
        st.write(
            "This prototype uses local code only. It does not call external AI APIs, does not require "
            "an API key, and does not store user text in a database. Session history exists only for "
            "the active Streamlit session unless you download it."
        )
        st.divider()
        st.subheader("Model pieces")
        st.markdown(
            "- N-gram next phrase predictor\n"
            "- Local TF-IDF similarity personalization\n"
            "- Context-aware fallback suggestions\n"
            "- Bandit-style accept/reject feedback ranking"
        )

    history = read_uploaded_history(uploaded)
    if st.session_state.session_history:
        history = pd.concat([history, pd.DataFrame(st.session_state.session_history)], ignore_index=True)
        history = clean_history_df(history)

    engine = SuggestionEngine(history)
    ranker = BanditRanker()

    main_col, insight_col = st.columns([2.1, 1])

    with main_col:
        st.subheader("Write with AI suggestions")
        contexts = ["email", "search", "note", "report", "general"]
        default_index = contexts.index(st.session_state.last_context) if st.session_state.last_context in contexts else 0
        context = st.selectbox("Writing context", contexts, index=default_index)
        prompt = st.text_area(
            "Start typing",
            value=st.session_state.last_prompt,
            height=170,
            placeholder="Example: Dear team, thank you for...",
        )

        controls = st.columns([1, 1, 1])
        with controls[0]:
            top_k = st.slider("Number of suggestions", min_value=3, max_value=8, value=5)
        with controls[1]:
            add_to_history = st.checkbox("Learn from this session text", value=True)
        with controls[2]:
            st.write("")
            st.write("")
            generate = st.button("Generate suggestions", type="primary", use_container_width=True)

        if generate:
            st.session_state.last_prompt = prompt
            st.session_state.last_context = context
            if add_to_history and prompt.strip():
                example = {"context": context, "user_input": prompt.strip(), "created_at": current_utc_iso()}
                st.session_state.session_history.append(example)
                history = pd.concat([history, pd.DataFrame([example])], ignore_index=True)
                engine = SuggestionEngine(history)
            suggestions = engine.suggestions(prompt, context, top_k=top_k)
            st.session_state.last_suggestions = ranker.rank(suggestions)

        suggestions = st.session_state.get("last_suggestions", [])
        if suggestions:
            st.markdown("### Suggested continuations")
            for i, item in enumerate(suggestions, start=1):
                with st.container(border=True):
                    st.markdown(f"**Suggestion {i}:** {item['text']}")
                    st.caption(
                        f"Source: {item['source']} | Why: {item['reason']} | "
                        f"Current score: {ranker.score(item['source']):.2f}"
                    )
                    st.code(item["text"], language="text")
                    feedback_left, feedback_right = st.columns(2)
                    with feedback_left:
                        if st.button(f"Accept suggestion {i}", key=f"accept_{i}", use_container_width=True):
                            ranker.update(item["source"], accepted=True)
                            st.success("Feedback saved. This source will rank higher next time.")
                    with feedback_right:
                        if st.button(f"Reject suggestion {i}", key=f"reject_{i}", use_container_width=True):
                            ranker.update(item["source"], accepted=False)
                            st.info("Feedback saved. This source will rank lower next time.")
        else:
            st.info("Type a prompt and click Generate suggestions to see the assistant in action.")

    with insight_col:
        st.subheader("Behavior insights")
        insights = engine.behavior_insights()
        st.metric("Training examples", insights["num_examples"])
        st.metric("Average content words", insights["avg_content_words"])
        st.write("Contexts learned")
        st.json(insights["contexts"])
        common_terms = [word for word, _ in insights["common_terms"]]
        st.write("Common terms")
        st.write(", ".join(common_terms) if common_terms else "No common terms yet.")

        st.divider()
        st.subheader("Feedback ranker")
        st.json(st.session_state.get("bandit", {}))

        st.divider()
        st.subheader("Download session")
        profile = {
            "created_at": current_utc_iso(),
            "session_history": st.session_state.get("session_history", []),
            "bandit": st.session_state.get("bandit", {}),
        }
        st.download_button(
            "Download profile JSON",
            data=json.dumps(profile, indent=2),
            file_name="genai_prompt_assistant_profile.json",
            mime="application/json",
            use_container_width=True,
        )

        session_df = pd.DataFrame(st.session_state.get("session_history", []))
        csv_buffer = StringIO()
        session_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download session CSV",
            data=csv_buffer.getvalue(),
            file_name="session_user_history.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=session_df.empty,
        )

    st.divider()
    with st.expander("Prototype notes and limitations"):
        st.markdown(
            "This app is a working web prototype based on the project Colab notebook. "
            "It demonstrates the product idea with lightweight ML so it can run on Streamlit hosting. "
            "A production typing assistant, browser extension, or iOS keyboard would require native app development, "
            "stronger privacy controls, security review, user consent flows, and larger training/evaluation data."
        )


if __name__ == "__main__":
    main()
