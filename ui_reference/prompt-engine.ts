export type ModelId = "chatgpt" | "claude" | "gemini" | "perplexity" | "copilot";

export const MODELS: { id: ModelId; name: string; hint: string }[] = [
  { id: "chatgpt", name: "ChatGPT", hint: "Responds best to explicit role + step framing." },
  { id: "claude", name: "Claude", hint: "Prefers rich context and clear XML-ish sections." },
  { id: "gemini", name: "Gemini", hint: "Likes concrete goals and structured output rules." },
  { id: "perplexity", name: "Perplexity", hint: "Add sourcing and recency requirements." },
  { id: "copilot", name: "Copilot", hint: "Be precise about files, language and constraints." },
];

export const CONTEXTS = [
  "Email",
  "Research",
  "Coding",
  "Meeting Notes",
  "School",
  "Business",
  "Marketing",
  "General",
] as const;

export const LENGTHS = ["Short", "Medium", "Long"] as const;
export const TONES = ["Professional", "Friendly", "Academic", "Persuasive", "Creative"] as const;
export const AUDIENCES = ["Beginner", "Intermediate", "Expert"] as const;
export const FORMATS = ["Paragraph", "Bullets", "Table", "JSON", "Checklist"] as const;

export const EXAMPLE_PROMPTS = [
  "Write an email",
  "Research a topic",
  "Summarize notes",
  "Create a presentation",
  "Build code",
  "Analyze data",
];

export type Settings = {
  context: string;
  model: ModelId;
  length: (typeof LENGTHS)[number];
  tone: (typeof TONES)[number];
  audience: (typeof AUDIENCES)[number];
  format: (typeof FORMATS)[number];
};

export type Suggestion = {
  id: string;
  title: string;
  detail: string;
  fix: string;
};

export type Analysis = {
  score: number;
  breakdown: { label: string; value: number }[];
  suggestions: Suggestion[];
};

const WEAK_VERBS = ["help", "do", "make", "stuff", "things", "some", "nice", "good"];

function clamp(n: number) {
  return Math.max(0, Math.min(100, Math.round(n)));
}

export function analyze(prompt: string, settings: Settings): Analysis {
  const text = prompt.trim();
  const words = text ? text.split(/\s+/).length : 0;
  const lower = text.toLowerCase();

  const clarity = clamp(30 + Math.min(words, 60) * 0.9 + (/[.?!]/.test(text) ? 12 : 0));
  const specificity = clamp(
    20 +
      Math.min(words, 80) * 0.7 +
      (/\d/.test(text) ? 15 : 0) -
      WEAK_VERBS.filter((w) => lower.includes(` ${w} `)).length * 8,
  );
  const context = clamp(
    18 + (words > 25 ? 35 : words) + (/(audience|for |context|because)/.test(lower) ? 25 : 0),
  );
  const constraints = clamp(
    10 +
      (/(within|limit|no more|avoid|must|only|word|tone)/.test(lower) ? 55 : 0) +
      Math.min(words, 40) * 0.6,
  );
  const examples = clamp((/(example|e\.g\.|for instance|sample)/.test(lower) ? 80 : 15) + words * 0.2);

  const breakdown = [
    { label: "Clarity", value: clarity },
    { label: "Specificity", value: specificity },
    { label: "Context", value: context },
    { label: "Constraints", value: constraints },
    { label: "Examples", value: examples },
  ];

  const score = text
    ? clamp(breakdown.reduce((a, b) => a + b.value, 0) / breakdown.length)
    : 0;

  const suggestions: Suggestion[] = [];
  if (context < 70)
    suggestions.push({
      id: "audience",
      title: "Clarify your audience",
      detail: "Naming who the answer is for makes the response far more relevant.",
      fix: `Write this for a ${settings.audience.toLowerCase()} audience.`,
    });
  if (constraints < 70)
    suggestions.push({
      id: "constraints",
      title: "Specify constraints",
      detail: "Length, tone and things to avoid keep the model on target.",
      fix: `Keep it ${settings.length.toLowerCase()} and use a ${settings.tone.toLowerCase()} tone.`,
    });
  if (!/(bullet|table|json|checklist|paragraph|format)/.test(lower))
    suggestions.push({
      id: "format",
      title: "Add desired output format",
      detail: "Telling the model how to structure the answer removes guesswork.",
      fix: `Return the answer as ${settings.format.toLowerCase()}.`,
    });
  if (examples < 60)
    suggestions.push({
      id: "examples",
      title: "Include an example",
      detail: "One example of a good answer sharply improves output quality.",
      fix: "For example: include one short sample of the ideal answer.",
    });
  if (words > 0 && words < 12)
    suggestions.push({
      id: "broad",
      title: "Your request is too broad",
      detail: "Add the goal, the subject and the outcome you expect.",
      fix: "Add the specific goal and the outcome you want to achieve.",
    });

  return { score, breakdown, suggestions };
}

const MODEL_PREAMBLE: Record<ModelId, string> = {
  chatgpt: "Think step by step before answering.",
  claude: "Reason carefully, then give the final answer in clearly labelled sections.",
  gemini: "Be concrete and factual, and structure the response clearly.",
  perplexity: "Use current, credible sources and cite them inline.",
  copilot: "Prefer production-ready code with brief inline comments.",
};

export function improve(prompt: string, settings: Settings, applied: string[] = []) {
  const text = prompt.trim();
  if (!text) return "";
  const lengthGuide = { Short: "under 150 words", Medium: "around 350 words", Long: "800+ words" }[
    settings.length
  ];

  const lines = [
    `You are an expert ${settings.context.toLowerCase()} specialist.`,
    "",
    `Task: ${text}`,
    "",
    "Requirements:",
    `• Audience: ${settings.audience.toLowerCase()} readers`,
    `• Tone: ${settings.tone.toLowerCase()}`,
    `• Length: ${lengthGuide}`,
    `• Output format: ${settings.format.toLowerCase()}`,
    `• ${MODEL_PREAMBLE[settings.model]}`,
    "• Ask for missing details before assuming them.",
  ];
  if (applied.length) {
    lines.push("", "Additional guidance:", ...applied.map((a) => `• ${a}`));
  }
  return lines.join("\n");
}