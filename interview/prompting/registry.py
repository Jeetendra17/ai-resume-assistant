"""Versioned prompts for the interview assistant.

Each version records what it was written to fix. That is what lets a clause be
deleted later instead of accumulating forever, and it is why a prompt change is
scored (`python -m interview.prompting.evaluate`) rather than eyeballed.

The live version is whichever scored best without regressing refusals; see
`LIVE_VERSION` and `results.json`. Override with INTERVIEW_PROMPT_VERSION.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from core.llm import OUT_OF_SCOPE
from data.profile import PROFILE
from interview.text import concise

DECLINE = OUT_OF_SCOPE.format(email=PROFILE["email"])

_IDENTITY = (
    f"You are the portfolio assistant for {PROFILE['name']}, an {PROFILE['role']} based in "
    f"{PROFILE['location']}. You are talking to recruiters, hiring managers and engineers "
    "evaluating him for AI/ML engineering roles."
)

_GROUNDING = """Rules:
- Answer only from the CONTEXT in the user turn. It is the complete record.
- Never invent employers, dates, titles, tools, numbers or anything he has not done.
- If the context does not answer the question, say his record doesn't cover it and point to \
his email ({email}) rather than guessing.
- Refer to him as "Jeetendra" or "he". Lead with the direct answer. Keep it under about 150 \
words unless asked to go deeper; short markdown bullets are fine for lists.""".format(email=PROFILE["email"])

_SCOPE = f"""- Scope: answer only questions about his professional background, skills, work, \
projects, education, how this website works, or hiring logistics. For anything else -- his \
personal life, opinions, general knowledge, or requests unrelated to him -- reply with exactly:
{DECLINE}
- Be honest about level: he is early-career. Do not oversell him as senior."""

_CITE = """- Cite the context entries you used as [1], [2] matching their numbers. Every factual \
claim must come from a cited entry. Do not cite an entry you did not use."""


@dataclass(frozen=True)
class PromptVersion:
    id: str
    name: str
    fixes: str
    system: str
    examples: int = 0          # retrieved few-shot exemplars to include
    cite: bool = False
    context_words: int | None = None   # trim each context entry to its leading ~N words


VERSIONS = {
    "v1": PromptVersion(
        id="v1",
        name="Baseline",
        fixes="Starting point: context plus question, no rules.",
        system="You are a helpful assistant answering questions about a job candidate.",
    ),
    "v2": PromptVersion(
        id="v2",
        name="Grounded",
        fixes="v1 fills gaps from general knowledge and states plausible facts the record never "
        "says. Adds a role, the rule that the context is the whole record, and a named list of "
        "what must never be invented.",
        system=f"{_IDENTITY}\n\n{_GROUNDING}",
    ),
    "v3": PromptVersion(
        id="v3",
        name="Scoped",
        fixes="The retrieval eval showed similarity cannot decide scope: junk questions about "
        "'him' score as high as real ones, so personal and general-knowledge questions reach the "
        "model with plausible-looking context. Adds an explicit scope rule with the exact decline "
        "text, and the honesty-about-level rule.",
        system=f"{_IDENTITY}\n\n{_GROUNDING}\n{_SCOPE}",
    ),
    "v4": PromptVersion(
        id="v4",
        name="Scoped + retrieved examples",
        fixes="Answers drift long and generic. Adds two retrieved examples of concise, direct "
        "answers from the training split -- the zero-cost stand-in for a fine-tuned model's "
        "learned register.",
        system=f"{_IDENTITY}\n\n{_GROUNDING}\n{_SCOPE}",
        examples=2,
    ),
    "v5": PromptVersion(
        id="v5",
        name="Scoped + examples + citations",
        fixes="Claims are not traceable to the entry they came from. Requires numbered citations "
        "that the verify step can check against the retrieved set.",
        system=f"{_IDENTITY}\n\n{_GROUNDING}\n{_SCOPE}\n{_CITE}",
        examples=2,
        cite=True,
    ),
    "v6": PromptVersion(
        id="v6",
        name="v5 with trimmed context",
        fixes="Efficiency. Groq's free tier allows 8,000 tokens a minute and v5 sends ~2,400 per "
        "question, mostly three full ~350-word answers as context -- so only about 3 visitors a "
        "minute before failover. Trims each context entry to its leading ~150 words (whole "
        "paragraphs), cutting the prompt by about a fifth (~1,900). Kept only if it loses nothing "
        "on the other scores.",
        system=f"{_IDENTITY}\n\n{_GROUNDING}\n{_SCOPE}\n{_CITE}",
        examples=2,
        cite=True,
        context_words=150,
    ),
}

# Chosen by interview/prompting/evaluate.py; see results.json for the scores.
LIVE_VERSION = "v6"


def live() -> PromptVersion:
    return VERSIONS[os.environ.get("INTERVIEW_PROMPT_VERSION", LIVE_VERSION)]


def format_context(docs: list[dict], max_words: int | None = None) -> str:
    def body(d):
        if not max_words:
            return d["answer"]
        return concise(d["answer"], min_words=max_words, max_words=max_words + 60)

    return "\n\n".join(f"[{i}] Q: {d['question']}\nA: {body(d)}" for i, d in enumerate(docs, start=1))


def format_examples(examples: list[dict]) -> str:
    return "\n\n".join(f"Q: {e['question']}\nA: {e['answer']}" for e in examples)


def render(version: PromptVersion, question: str, docs: list[dict],
           examples: list[dict] | None = None, history: list[dict] | None = None):
    """Return (system prompt, messages) for the provider chain."""
    parts = []
    if version.examples and examples:
        parts.append("EXAMPLES OF GOOD ANSWERS (style only -- facts come from CONTEXT)\n"
                     + format_examples(examples[: version.examples]))
    parts.append("CONTEXT\n" + (format_context(docs, version.context_words) if docs
                                 else "(nothing in his record matched)"))
    parts.append("QUESTION\n" + question)
    messages = list(history or []) + [{"role": "user", "content": "\n\n".join(parts)}]
    return version.system, messages
