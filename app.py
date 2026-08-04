from __future__ import annotations

import html
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



# -----------------------------------------------------------------------------
# Lovable-inspired prompt analysis layer
# -----------------------------------------------------------------------------

MODEL_HINTS = {
    "ChatGPT": "Use an explicit role, task, constraints, and step framing.",
    "Claude": "Provide rich context and clearly labelled sections.",
    "Gemini": "State concrete goals and structured output rules.",
    "Perplexity": "Include sourcing and recency requirements.",
    "Copilot": "Name the language, files, constraints, and desired code quality.",
}

PROMPT_CONTEXTS = ["Email", "Research", "Coding", "Meeting Notes", "School", "Business", "Marketing", "General"]
PROMPT_LENGTHS = ["Short", "Medium", "Long"]
PROMPT_TONES = ["Professional", "Friendly", "Academic", "Persuasive", "Creative"]
PROMPT_AUDIENCES = ["Beginner", "Intermediate", "Expert"]
PROMPT_FORMATS = ["Paragraph", "Bullets", "Table", "JSON", "Checklist"]
PROMPT_MODELS = list(MODEL_HINTS)

EXAMPLE_PROMPTS = {
    "Write an email": "Write a polite email asking my professor for a two-day extension on a project because I was sick.",
    "Research a topic": "Research the benefits and risks of AI tutoring for middle-school students.",
    "Summarize notes": "Summarize these meeting notes and identify decisions, owners, and deadlines.",
    "Create a presentation": "Create a 10-slide presentation that explains renewable energy to high-school students.",
    "Build code": "Build a beginner-friendly Python program that tracks homework assignments in a CSV file.",
    "Analyze data": "Analyze a student progress dataset and explain the most important trends in plain language.",
}

PROMPT_LIBRARY = {
    "Business": "Act as a business analyst. Create a concise proposal for [initiative]. Include the objective, audience, benefits, risks, timeline, budget assumptions, and next steps. Return the answer as a structured memo.",
    "Education": "Act as an experienced teacher. Create a lesson plan about [topic] for [grade level]. Include learning objectives, materials, a warm-up, guided practice, independent practice, assessment, and accommodations.",
    "Coding": "Act as a senior software engineer and patient coding tutor. Build [feature] in [language]. Explain the approach, provide production-ready code, include error handling, and add small tests. Assume the learner is [level].",
    "Writing": "Act as an expert editor. Rewrite the following draft for [audience] using a [tone] tone. Improve clarity, flow, structure, and concision while preserving the original meaning: [paste draft].",
    "Marketing": "Act as a marketing strategist. Create a campaign for [product] aimed at [audience]. Include positioning, key messages, channels, sample copy, success metrics, and a 30-day launch plan.",
    "Resume": "Act as a resume editor. Rewrite these accomplishments for a [role] application using quantified impact, strong action verbs, and concise bullet points. Do not invent facts: [paste accomplishments].",
    "Interviews": "Act as an interview coach. Prepare me for a [role] interview. Generate likely questions, strong answer frameworks, a mock interview, and a scoring rubric based on this job description: [paste description].",
    "Research": "Act as a research assistant. Develop a structured research plan for [topic]. Include research questions, search terms, inclusion criteria, evidence table fields, limitations, and a synthesis outline.",
}

WEAK_PROMPT_WORDS = ["help", "do", "make", "stuff", "things", "some", "nice", "good"]


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def analyze_prompt_quality(prompt: str, audience: str, length: str, tone: str, output_format: str) -> Dict[str, object]:
    text = normalize_text(prompt)
    words = len(text.split()) if text else 0
    lower = f" {text.lower()} "

    clarity = clamp_score(30 + min(words, 60) * 0.9 + (12 if re.search(r"[.?!]", text) else 0))
    specificity = clamp_score(
        20 + min(words, 80) * 0.7 + (15 if re.search(r"\d", text) else 0)
        - sum(8 for word in WEAK_PROMPT_WORDS if f" {word} " in lower)
    )
    context = clamp_score(18 + (35 if words > 25 else words) + (25 if re.search(r"audience|for |context|because", lower) else 0))
    constraints = clamp_score(
        10 + (55 if re.search(r"within|limit|no more|avoid|must|only|word|tone", lower) else 0)
        + min(words, 40) * 0.6
    )
    examples = clamp_score((80 if re.search(r"example|e\.g\.|for instance|sample", lower) else 15) + words * 0.2)
    breakdown = {
        "Clarity": clarity,
        "Specificity": specificity,
        "Context": context,
        "Constraints": constraints,
        "Examples": examples,
    }
    score = clamp_score(sum(breakdown.values()) / len(breakdown)) if text else 0

    suggestions = []
    if context < 70:
        suggestions.append(("Clarify your audience", "Naming who the answer is for makes the response more relevant.", f"Write this for a {audience.lower()} audience."))
    if constraints < 70:
        suggestions.append(("Specify constraints", "Length, tone, and boundaries keep the model on target.", f"Keep it {length.lower()} and use a {tone.lower()} tone."))
    if not re.search(r"bullet|table|json|checklist|paragraph|format", lower):
        suggestions.append(("Add an output format", "Tell the model how to structure the answer.", f"Return the answer as {output_format.lower()}."))
    if examples < 60:
        suggestions.append(("Include an example", "One example can sharply improve response quality.", "Include one short example of the ideal answer."))
    if 0 < words < 12:
        suggestions.append(("Make the goal more specific", "Add the subject, outcome, and key details you expect.", "Add the specific goal and the outcome you want to achieve."))

    return {"score": score, "breakdown": breakdown, "suggestions": suggestions}


def build_improved_prompt(
    prompt: str,
    context: str,
    model: str,
    length: str,
    tone: str,
    audience: str,
    output_format: str,
    applied_guidance: Sequence[str],
) -> str:
    text = normalize_text(prompt)
    if not text:
        return ""
    length_guide = {"Short": "under 150 words", "Medium": "around 350 words", "Long": "800 or more words"}[length]
    lines = [
        f"You are an expert {context.lower()} specialist.",
        "",
        f"Task: {text}",
        "",
        "Requirements:",
        f"- Audience: {audience.lower()} readers",
        f"- Tone: {tone.lower()}",
        f"- Length: {length_guide}",
        f"- Output format: {output_format.lower()}",
        f"- Model guidance: {MODEL_HINTS[model]}",
        "- Ask for missing details before making important assumptions.",
    ]
    if applied_guidance:
        lines.extend(["", "Additional guidance:"])
        lines.extend(f"- {item}" for item in applied_guidance)
    return "\n".join(lines)


def score_label(score: int) -> str:
    if score == 0:
        return "Awaiting prompt"
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Professional"
    if score >= 50:
        return "Solid start"
    return "Needs improvement"


def safe_uploaded_history(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return load_default_history()
    try:
        uploaded_file.seek(0)
        return clean_history_df(pd.read_csv(uploaded_file))
    except Exception as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        return load_default_history()


def extend_session_defaults() -> None:
    initialize_session()
    defaults = {
        "navigation": "Workspace",
        "prompt_text": "",
        "prompt_context": "General",
        "target_model": "ChatGPT",
        "response_length": "Medium",
        "target_audience": "Intermediate",
        "prompt_tone": "Professional",
        "output_format": "Bullets",
        "applied_guidance": [],
        "generation_log": [],
        "saved_prompts": [],
        "learn_from_session": True,
        "top_k": 5,
        "live_analysis": True,
        "high_contrast": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def inject_lovable_styles() -> None:
    high_contrast = bool(st.session_state.get("high_contrast", False))
    bg = "#eef2f7" if high_contrast else "#f6f8fb"
    text = "#07182d" if high_contrast else "#10233f"
    st.markdown(
        f"""
        <style>
        :root {{
          --navy:#07182d;
          --navy-2:#0b1f3a;
          --blue:#2563eb;
          --blue-soft:#e8f0ff;
          --mint:#3dd6b4;
          --surface:#ffffff;
          --surface-2:#f2f5f9;
          --border:#dfe6ef;
          --text:{text};
          --muted:#6f7f93;
          --success:#15946f;
          --shadow:0 18px 50px -34px rgba(7,24,45,.45);
        }}
        html, body, [class*="css"] {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
        .stApp {{ background: {bg}; color: var(--text); }}
        [data-testid="stHeader"] {{ background: rgba(246,248,251,.80); border-bottom:1px solid rgba(223,230,239,.75); backdrop-filter: blur(16px); }}
        [data-testid="stMainBlockContainer"] {{ max-width: 1500px; padding-top: 1.6rem; padding-bottom: 4rem; }}
        [data-testid="stSidebar"] {{ background: var(--navy); border-right:0; }}
        [data-testid="stSidebar"] * {{ color: rgba(255,255,255,.84); }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: rgba(255,255,255,.72); }}
        [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.10); }}
        [data-testid="stSidebar"] [data-baseweb="radio"] > div {{ gap:.35rem; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
          border-radius:12px; padding:.58rem .7rem; margin:.08rem 0; transition:.18s ease; width:100%;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:rgba(255,255,255,.07); }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:rgba(255,255,255,.10); box-shadow:inset 3px 0 0 var(--blue); }}
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{ background:rgba(255,255,255,.06); border-color:rgba(255,255,255,.16); }}
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{ color:var(--navy)!important; background:white!important; }}
        h1,h2,h3 {{ color:var(--text); letter-spacing:-.025em; }}
        .lovable-topbar {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:18px; color:var(--muted); font-size:13px; }}
        .lovable-status {{ display:flex; align-items:center; gap:9px; }}
        .lovable-status-dot {{ width:7px; height:7px; border-radius:999px; background:var(--blue); box-shadow:0 0 0 5px rgba(37,99,235,.08); }}
        .hero-card {{
          position:relative; overflow:hidden; border:1px solid var(--border); border-radius:24px; padding:40px;
          background:linear-gradient(135deg,#ffffff 0%,#f8fbff 58%,#edf4ff 100%); box-shadow:var(--shadow); margin-bottom:22px;
        }}
        .hero-card:before {{ content:""; position:absolute; width:330px; height:330px; right:-110px; top:-160px; border-radius:50%; background:rgba(37,99,235,.12); filter:blur(30px); }}
        .hero-card:after {{ content:""; position:absolute; width:120px; height:120px; right:90px; bottom:-45px; border:1px solid rgba(11,31,58,.10); border-radius:50%; }}
        .hero-inner {{ position:relative; max-width:820px; }}
        .accent-rule {{ width:54px; height:4px; border-radius:99px; background:linear-gradient(90deg,var(--blue),var(--mint)); margin-bottom:16px; }}
        .hero-eyebrow {{ color:var(--blue); font-weight:650; font-size:14px; }}
        .hero-title {{ color:var(--navy-2); font-size:clamp(35px,4vw,54px); line-height:1.04; letter-spacing:-.045em; font-weight:750; margin:7px 0 12px; }}
        .hero-copy {{ color:var(--muted); font-size:16px; line-height:1.65; max-width:720px; }}
        .support-row {{ display:flex; flex-wrap:wrap; gap:12px 19px; margin-top:20px; color:var(--muted); font-size:13px; }}
        .support-row b {{ color:var(--text); }}
        .support-item:before {{ content:"✓"; color:var(--success); font-weight:800; margin-right:6px; }}
        .quick-card {{ min-height:120px; border:1px solid var(--border); border-radius:16px; background:white; padding:18px; box-shadow:0 12px 32px -30px rgba(7,24,45,.55); }}
        .quick-icon {{ width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:11px; border:1px solid var(--border); background:var(--blue-soft); color:var(--navy); font-size:18px; }}
        .quick-title {{ color:var(--text); font-weight:700; font-size:14px; margin-top:13px; }}
        .quick-detail {{ color:var(--muted); font-size:12.5px; margin-top:4px; line-height:1.45; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{ background:var(--surface); border:1px solid var(--border)!important; border-radius:18px!important; box-shadow:0 12px 36px -32px rgba(7,24,45,.55); }}
        [data-testid="stMetric"] {{ background:var(--surface-2); border:1px solid var(--border); border-radius:14px; padding:14px 16px; }}
        .section-kicker {{ text-transform:uppercase; letter-spacing:.14em; color:var(--muted); font-weight:750; font-size:10.5px; margin-bottom:8px; }}
        .score-card {{ background:linear-gradient(150deg,#fff,#f7faff); border:1px solid var(--border); border-radius:18px; padding:22px; box-shadow:var(--shadow); }}
        .score-ring {{ width:140px; height:140px; margin:12px auto; border-radius:50%; display:grid; place-items:center; background:conic-gradient(var(--blue) calc(var(--score)*1%), #dfe7f2 0); position:relative; }}
        .score-ring:after {{ content:""; position:absolute; width:112px; height:112px; background:white; border-radius:50%; box-shadow:inset 0 0 0 1px var(--border); }}
        .score-number {{ position:relative; z-index:1; text-align:center; color:var(--navy); font-size:34px; font-weight:760; line-height:1; }}
        .score-number small {{ display:block; font-size:10.5px; color:var(--muted); font-weight:500; margin-top:5px; letter-spacing:.04em; }}
        .score-label {{ display:table; margin:10px auto 18px; border:1px solid var(--border); border-radius:99px; padding:5px 11px; font-size:12px; font-weight:700; color:var(--navy); background:white; }}
        .credit-card {{ border:1px solid rgba(255,255,255,.11); background:rgba(255,255,255,.055); border-radius:16px; padding:14px; margin-top:16px; }}
        .credit-row {{ display:flex; align-items:center; gap:11px; }}
        .avatar {{ width:38px; height:38px; border-radius:50%; display:grid; place-items:center; background:rgba(37,99,235,.30); border:1px solid rgba(255,255,255,.16); color:white; font-size:12px; font-weight:800; }}
        .credit-name {{ color:white; font-weight:700; font-size:13px; }}
        .credit-role {{ color:rgba(255,255,255,.50); font-size:10.5px; margin-top:2px; }}
        .brand-wrap {{ display:flex; align-items:center; gap:11px; margin:4px 0 19px; }}
        .brand-mark {{ width:42px; height:42px; border-radius:14px; border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.09); display:grid; place-items:center; color:white; font-size:21px; font-weight:800; }}
        .brand-name {{ color:white; font-size:15px; font-weight:800; line-height:1.2; }}
        .brand-sub {{ color:rgba(255,255,255,.52); font-size:10.5px; margin-top:3px; letter-spacing:.04em; }}
        .original-box,.improved-box {{ min-height:190px; border-radius:15px; padding:18px; border:1px solid var(--border); white-space:pre-wrap; line-height:1.55; font-size:13.5px; }}
        .original-box {{ background:#fff; color:var(--muted); }}
        .improved-box {{ background:linear-gradient(145deg,#eef5ff,#f7fbff); color:var(--text); }}
        .chip {{ display:inline-block; border:1px solid var(--border); background:white; color:var(--muted); border-radius:99px; padding:5px 10px; margin:3px 5px 3px 0; font-size:11.5px; }}
        .history-card {{ background:white; border:1px solid var(--border); border-radius:15px; padding:16px 18px; margin-bottom:10px; }}
        .history-score {{ float:right; background:rgba(21,148,111,.12); color:var(--success); font-weight:750; padding:4px 9px; border-radius:99px; font-size:11px; }}
        .footer-note {{ color:var(--muted); text-align:center; font-size:11px; padding-top:26px; }}
        .stButton > button, .stDownloadButton > button {{ border-radius:11px!important; min-height:2.55rem; font-weight:650!important; transition:.18s ease!important; }}
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{ background:var(--blue)!important; border-color:var(--blue)!important; }}
        .stButton > button:hover, .stDownloadButton > button:hover {{ transform:translateY(-1px); box-shadow:0 12px 24px -18px rgba(7,24,45,.65); }}
        [data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea {{ border-radius:12px!important; border-color:var(--border)!important; }}
        textarea {{ min-height:175px; }}
        [data-testid="stTabs"] button {{ font-weight:650; }}
        @media (max-width: 800px) {{ .hero-card {{ padding:28px 22px; }} .hero-title {{ font-size:36px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_sidebar() -> None:
    st.markdown(
        """
        <div class="brand-wrap">
          <div class="brand-mark">G+</div>
          <div><div class="brand-name">GenAI Prompt</div><div class="brand-sub">INTELLIGENT PROMPT ASSISTANT</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    st.markdown(
        """
        <div class="lovable-topbar">
          <div class="lovable-status"><span class="lovable-status-dot"></span>Better prompts, better answers - every time.</div>
          <div><span class="chip">Privacy-first prototype</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(analysis: Dict[str, object]) -> None:
    score = int(analysis["score"])
    st.markdown(
        f"""
        <div class="score-card">
          <div class="section-kicker">Prompt strength</div>
          <div class="score-ring" style="--score:{score}"><div class="score-number">{score}<small>OUT OF 100</small></div></div>
          <div class="score-label">{score_label(score)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for label, value in analysis["breakdown"].items():
        left, right = st.columns([4, 1])
        left.caption(label)
        right.caption(str(value))
        st.progress(int(value) / 100)


def render_sidebar() -> object:
    with st.sidebar:
        render_brand_sidebar()
        st.caption("WORKSPACE")
        page = st.radio(
            "Navigation",
            ["Workspace", "History", "Saved Prompts", "Training", "Settings", "Help"],
            label_visibility="collapsed",
            key="navigation",
        )
        st.divider()
        uploaded = st.file_uploader("Teach the assistant with a CSV", type=["csv"], help="Required column: user_input. Optional column: context.")
        st.caption("Your upload remains inside the active Streamlit session.")
        st.markdown(
            f"""
            <div class="credit-card">
              <div class="credit-row"><div class="avatar">YM</div><div><div class="credit-name">{AUTHOR_NAME}</div><div class="credit-role">AUTHOR</div></div></div>
              <div style="height:1px;background:rgba(255,255,255,.09);margin:12px 0"></div>
              <div class="credit-name" style="font-size:12px">{MENTOR_NAME}</div><div class="credit-role">MENTOR</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Local ML demo - no external AI API required")
        return uploaded


def render_hero() -> None:
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    st.markdown(
        f"""
        <section class="hero-card">
          <div class="hero-inner">
            <div class="accent-rule"></div>
            <div class="hero-eyebrow">{greeting}, Yashvi</div>
            <div class="hero-title">Ready to build better prompts?</div>
            <div class="hero-copy">GenAI Prompt Assistant turns ordinary requests into expert-level instructions, scores their quality, and learns from approved writing examples.</div>
            <div class="support-row"><b>Supports</b><span class="support-item">ChatGPT</span><span class="support-item">Claude</span><span class="support-item">Gemini</span><span class="support-item">Perplexity</span><span class="support-item">Copilot</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def set_prompt_text(value: str) -> None:
    """Callback-safe helper for loading examples and templates."""
    st.session_state["prompt_text"] = value


def render_quick_actions() -> None:
    cards = [
        ("✎", "Start writing", "Draft a prompt from a blank canvas."),
        ("✦", "Improve existing", "Paste a prompt and refine it."),
        ("▤", "Email example", "Load a polished email request."),
        ("⌁", "Coding example", "Load a structured coding task."),
    ]
    columns = st.columns(4)
    for col, (icon, title, detail) in zip(columns, cards):
        with col:
            st.markdown(f'<div class="quick-card"><div class="quick-icon">{icon}</div><div class="quick-title">{title}</div><div class="quick-detail">{detail}</div></div>', unsafe_allow_html=True)
    buttons = st.columns(4)
    buttons[0].button("Open blank canvas", use_container_width=True, on_click=set_prompt_text, args=("",))
    buttons[1].button("Keep current draft", use_container_width=True)
    buttons[2].button("Load email", use_container_width=True, on_click=set_prompt_text, args=(EXAMPLE_PROMPTS["Write an email"],))
    buttons[3].button("Load coding", use_container_width=True, on_click=set_prompt_text, args=(EXAMPLE_PROMPTS["Build code"],))


def build_history(uploaded) -> pd.DataFrame:
    history = safe_uploaded_history(uploaded)
    session_rows = st.session_state.get("session_history", [])
    if session_rows:
        additions = [{"context": item.get("context", "general"), "user_input": item.get("user_input", "")} for item in session_rows]
        history = pd.concat([history, pd.DataFrame(additions)], ignore_index=True)
    return clean_history_df(history)


def render_workspace(uploaded) -> None:
    render_hero()
    render_quick_actions()
    st.write("")

    history = build_history(uploaded)
    engine = SuggestionEngine(history)
    ranker = BanditRanker()

    prompt = st.session_state.get("prompt_text", "")
    analysis = analyze_prompt_quality(
        prompt,
        st.session_state.target_audience,
        st.session_state.response_length,
        st.session_state.prompt_tone,
        st.session_state.output_format,
    )

    left, right = st.columns([2.15, 1], gap="large")
    with left:
        with st.container(border=True):
            header_a, header_b = st.columns([4, 1])
            header_a.markdown('<div class="section-kicker">✦ Prompt editor</div>', unsafe_allow_html=True)
            header_b.caption(f"{len(normalize_text(prompt).split()) if normalize_text(prompt) else 0} words")
            st.text_area(
                "Prompt editor",
                key="prompt_text",
                label_visibility="collapsed",
                placeholder="What would you like AI to help you with today?",
                height=190,
            )
            st.caption("Examples")
            example_cols = st.columns(3)
            for idx, (label, example) in enumerate(EXAMPLE_PROMPTS.items()):
                example_cols[idx % 3].button(
                    label,
                    key=f"example_{idx}",
                    use_container_width=True,
                    on_click=set_prompt_text,
                    args=(example,),
                )

        with st.container(border=True):
            st.markdown('<div class="section-kicker">Prompt details</div>', unsafe_allow_html=True)
            row1 = st.columns(3)
            row1[0].selectbox("Context", PROMPT_CONTEXTS, key="prompt_context")
            row1[1].selectbox("Target AI", PROMPT_MODELS, key="target_model")
            row1[2].selectbox("Response length", PROMPT_LENGTHS, key="response_length")
            row2 = st.columns(3)
            row2[0].selectbox("Audience", PROMPT_AUDIENCES, key="target_audience")
            row2[1].selectbox("Tone", PROMPT_TONES, key="prompt_tone")
            row2[2].selectbox("Output format", PROMPT_FORMATS, key="output_format")
            row3 = st.columns([1, 1, 1.3])
            row3[0].slider("Next-phrase suggestions", 3, 8, key="top_k")
            row3[1].checkbox("Learn from this session", key="learn_from_session")
            generate = row3[2].button("Improve and generate suggestions", type="primary", use_container_width=True)

        prompt = st.session_state.get("prompt_text", "")
        analysis = analyze_prompt_quality(
            prompt,
            st.session_state.target_audience,
            st.session_state.response_length,
            st.session_state.prompt_tone,
            st.session_state.output_format,
        )
        improved = build_improved_prompt(
            prompt,
            st.session_state.prompt_context,
            st.session_state.target_model,
            st.session_state.response_length,
            st.session_state.prompt_tone,
            st.session_state.target_audience,
            st.session_state.output_format,
            st.session_state.applied_guidance,
        )

        if generate:
            if st.session_state.learn_from_session and normalize_text(prompt):
                example = {
                    "context": st.session_state.prompt_context.lower(),
                    "user_input": normalize_text(prompt),
                    "created_at": current_utc_iso(),
                }
                st.session_state.session_history.append(example)
                history = pd.concat([history, pd.DataFrame([example])], ignore_index=True)
                engine = SuggestionEngine(history)
            suggestions = engine.suggestions(prompt, st.session_state.prompt_context.lower(), top_k=st.session_state.top_k)
            st.session_state.last_suggestions = ranker.rank(suggestions)
            st.session_state.generation_log.insert(
                0,
                {
                    "created_at": current_utc_iso(),
                    "title": normalize_text(prompt)[:70] or "Untitled prompt",
                    "context": st.session_state.prompt_context,
                    "score": analysis["score"],
                    "prompt": prompt,
                    "improved": improved,
                },
            )

        quality_suggestions = analysis["suggestions"] if normalize_text(prompt) else []
        if quality_suggestions:
            st.markdown("### Smart improvements")
            suggestion_cols = st.columns(2)
            for idx, (title, detail, fix) in enumerate(quality_suggestions):
                with suggestion_cols[idx % 2].container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(detail)
                    c1, c2 = st.columns(2)
                    if c1.button("Apply", key=f"apply_quality_{idx}", use_container_width=True):
                        if fix not in st.session_state.applied_guidance:
                            st.session_state.applied_guidance.append(fix)
                        st.rerun()
                    if c2.button("Dismiss", key=f"dismiss_quality_{idx}", use_container_width=True):
                        st.info("Suggestion dismissed for this view.")

        suggestions = st.session_state.get("last_suggestions", [])
        if suggestions:
            st.markdown("### Personalized next-phrase suggestions")
            for idx, item in enumerate(suggestions, start=1):
                with st.container(border=True):
                    st.markdown(f"**{idx}. {item['text']}**")
                    st.caption(f"{item['reason']} · feedback score {ranker.score(item['source']):.2f}")
                    f1, f2, f3 = st.columns([1, 1, 2])
                    if f1.button("Accept", key=f"accept_{idx}", use_container_width=True):
                        ranker.update(item["source"], accepted=True)
                        st.success("Accepted. This source will rank higher.")
                    if f2.button("Reject", key=f"reject_{idx}", use_container_width=True):
                        ranker.update(item["source"], accepted=False)
                        st.info("Rejected. This source will rank lower.")
                    f3.code(item["text"], language="text")

        st.markdown("### Before and after")
        original_col, improved_col = st.columns(2)
        original_escaped = html.escape(prompt or "Start typing to see your prompt here.")
        original_col.markdown(f'<div class="section-kicker">Original prompt</div><div class="original-box">{original_escaped}</div>', unsafe_allow_html=True)
        improved_escaped = html.escape(improved or "Your expert-level rewrite will appear here.")
        improved_col.markdown(f'<div class="section-kicker">Improved prompt</div><div class="improved-box">{improved_escaped}</div>', unsafe_allow_html=True)
        action_cols = st.columns([1, 1, 1])
        action_cols[0].download_button("Export TXT", improved, file_name="improved_prompt.txt", mime="text/plain", disabled=not bool(improved), use_container_width=True)
        if action_cols[1].button("Save prompt", disabled=not bool(improved), use_container_width=True):
            st.session_state.saved_prompts.insert(0, {"title": normalize_text(prompt)[:60], "prompt": prompt, "improved": improved, "score": analysis["score"]})
            st.success("Saved to your prompt library.")
        if action_cols[2].button("Clear guidance", use_container_width=True):
            st.session_state.applied_guidance = []
            st.rerun()

    with right:
        render_score_card(analysis)
        st.write("")
        insights = engine.behavior_insights()
        with st.container(border=True):
            st.markdown('<div class="section-kicker">Today\'s activity</div>', unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.metric("Prompts improved", len(st.session_state.generation_log))
            average_score = round(sum(item["score"] for item in st.session_state.generation_log) / len(st.session_state.generation_log)) if st.session_state.generation_log else 0
            m2.metric("Average score", average_score)
            m3, m4 = st.columns(2)
            m3.metric("Training examples", insights["num_examples"])
            m4.metric("Saved prompts", len(st.session_state.saved_prompts))
        with st.container(border=True):
            st.markdown('<div class="section-kicker">Behavior insights</div>', unsafe_allow_html=True)
            st.write(f"**Average content words:** {insights['avg_content_words']}")
            st.write("**Common terms**")
            terms = "".join(f'<span class="chip">{html.escape(str(word))}</span>' for word, _ in insights["common_terms"])
            st.markdown(terms or '<span class="chip">No terms yet</span>', unsafe_allow_html=True)
            st.write("**Contexts learned**")
            st.bar_chart(pd.Series(insights["contexts"], name="Examples"), height=190)
        with st.container(border=True):
            st.markdown('<div class="section-kicker">Session profile</div>', unsafe_allow_html=True)
            profile = {
                "created_at": current_utc_iso(),
                "session_history": st.session_state.session_history,
                "feedback_ranker": st.session_state.get("bandit", {}),
                "saved_prompts": st.session_state.saved_prompts,
            }
            st.download_button("Download profile JSON", json.dumps(profile, indent=2), "genai_prompt_assistant_profile.json", "application/json", use_container_width=True)


def render_history_page() -> None:
    st.markdown('<div class="accent-rule"></div>', unsafe_allow_html=True)
    st.title("History")
    st.caption("Every prompt improved during this active session, in one timeline.")
    query = st.text_input("Search your prompts", placeholder="Search title, context, or prompt text")
    items = st.session_state.generation_log
    if query:
        q = query.lower()
        items = [item for item in items if q in json.dumps(item).lower()]
    if not items:
        st.info("No prompt history yet. Improve a prompt in the Workspace to create an entry.")
        return
    for item in items:
        with st.container(border=True):
            safe_title = html.escape(str(item["title"]))
            st.markdown(f'<span class="history-score">{item["score"]}</span><strong>{safe_title}</strong>', unsafe_allow_html=True)
            st.caption(f'{item["created_at"][:16].replace("T", " ")} UTC · {item["context"]}')
            with st.expander("Open prompt and improved version"):
                c1, c2 = st.columns(2)
                c1.code(item["prompt"], language="text")
                c2.code(item["improved"], language="text")


def render_library_page() -> None:
    st.markdown('<div class="accent-rule"></div>', unsafe_allow_html=True)
    st.title("Saved Prompts")
    st.caption("Start from a proven template, then customize it in the Workspace.")
    st.markdown("### Template library")
    cols = st.columns(3)
    for idx, (category, template) in enumerate(PROMPT_LIBRARY.items()):
        with cols[idx % 3].container(border=True):
            st.markdown(f"**{category}**")
            st.caption(template[:110] + "...")
            st.button(
                "Use template",
                key=f"template_{category}",
                use_container_width=True,
                on_click=set_prompt_text,
                args=(template,),
            )
    st.markdown("### Your saved prompts")
    if not st.session_state.saved_prompts:
        st.info("No saved prompts yet.")
    for idx, item in enumerate(st.session_state.saved_prompts):
        with st.container(border=True):
            st.markdown(f"**{item['title'] or 'Saved prompt'}**")
            st.caption(f"Quality score: {item['score']}")
            st.code(item["improved"], language="text")
            st.button(
                "Load in Workspace",
                key=f"load_saved_{idx}",
                on_click=set_prompt_text,
                args=(item["prompt"],),
            )


def render_training_page(uploaded) -> None:
    st.markdown('<div class="accent-rule"></div>', unsafe_allow_html=True)
    st.title("Teach GenAI Prompt")
    st.caption("Upload approved writing examples so suggestions can reflect the user's own style.")
    history = build_history(uploaded)
    engine = SuggestionEngine(history)
    insights = engine.behavior_insights()
    with st.container(border=True):
        st.markdown("#### Training data status")
        if uploaded is None:
            st.info("Using fictional sample data. Upload a CSV from the sidebar to personalize the model.")
        else:
            st.success("Uploaded CSV loaded successfully for this session.")
        a, b, c = st.columns(3)
        a.metric("Examples", insights["num_examples"])
        b.metric("Average content words", insights["avg_content_words"])
        c.metric("Contexts", len(insights["contexts"]))
        st.dataframe(history, use_container_width=True, hide_index=True)
    with st.container(border=True):
        st.markdown("#### Learned writing signals")
        terms = "".join(f'<span class="chip">{html.escape(str(word))}</span>' for word, _ in insights["common_terms"])
        st.markdown(terms, unsafe_allow_html=True)
        st.bar_chart(pd.Series(insights["contexts"], name="Examples"))
    with st.expander("Required CSV format"):
        st.code("context,user_input\nemail,Dear team thank you for the update\nsearch,best beginner Python project ideas", language="csv")


def render_settings_page() -> None:
    st.markdown('<div class="accent-rule"></div>', unsafe_allow_html=True)
    st.title("Settings")
    st.caption("Choose the default AI target, writing style, and accessibility preferences.")
    with st.container(border=True):
        st.selectbox("Default target AI", PROMPT_MODELS, key="target_model")
        st.selectbox("Default tone", PROMPT_TONES, key="prompt_tone")
        st.selectbox("Default audience", PROMPT_AUDIENCES, key="target_audience")
    with st.container(border=True):
        st.checkbox("Live prompt analysis", key="live_analysis")
        st.checkbox("High contrast mode", key="high_contrast")
        st.checkbox("Learn from session text by default", key="learn_from_session")
    st.info("Settings are kept in the active browser session for this prototype.")


def render_help_page() -> None:
    st.markdown('<div class="accent-rule"></div>', unsafe_allow_html=True)
    st.title("Quick start")
    st.caption("Five short steps to build a clearer, stronger AI prompt.")
    steps = [
        ("1", "Choose a task", "Start with a blank canvas, example, or prompt library template."),
        ("2", "Name the audience", "Select who will read or use the response."),
        ("3", "Set response rules", "Choose the target AI, tone, length, and output format."),
        ("4", "Improve the prompt", "Review the quality score and apply smart improvements."),
        ("5", "Learn from feedback", "Accept or reject next-phrase suggestions to adjust their ranking."),
    ]
    for number, title, detail in steps:
        with st.container(border=True):
            c1, c2 = st.columns([.4, 8])
            c1.markdown(f"### {number}")
            c2.markdown(f"**{title}**")
            c2.caption(detail)
    with st.expander("Privacy and prototype limitations"):
        st.write(
            "This demonstration runs lightweight local ML inside the Streamlit process and does not call an external AI API. "
            "It does not provide persistent accounts or a production database. A production browser extension or mobile keyboard "
            "would require explicit consent, secure storage, data deletion controls, authentication, and security review."
        )


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="✨", layout="wide", initial_sidebar_state="expanded")
    extend_session_defaults()
    inject_lovable_styles()
    uploaded = render_sidebar()
    render_topbar()

    page = st.session_state.navigation
    if page == "Workspace":
        render_workspace(uploaded)
    elif page == "History":
        render_history_page()
    elif page == "Saved Prompts":
        render_library_page()
    elif page == "Training":
        render_training_page(uploaded)
    elif page == "Settings":
        render_settings_page()
    else:
        render_help_page()

    st.markdown(
        f'<div class="footer-note">{APP_NAME} · Author: {AUTHOR_NAME} · Mentor: {MENTOR_NAME}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
