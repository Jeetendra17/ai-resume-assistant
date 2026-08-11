"""Dependency-free retrieval over the resume corpus.

A small BM25 index is plenty here: the corpus is ~30 short chunks, so an embedding
model would add a network hop and a cold-start cost for no measurable recall gain.
Keeping it in-process also means the site still answers when no API key is set.

Two refinements on top of textbook BM25, both added after `eval_retrieval.py`
caught them scoring badly:

1. Light suffix stemming, so "LLMs" matches "LLM" and "hallucinating" matches
   "hallucination".
2. Query expansion terms carry a fraction of the weight of terms the visitor
   actually typed. Without this, a broad synonym like "shipped" -> "project"
   matches every project chunk equally and drowns out the one discriminating
   term in the query.
"""

import math
import re
from collections import Counter

from data.knowledge import CHUNKS

_TOKEN = re.compile(r"[a-z0-9+#.]+")

_STOPWORDS = {
    "a", "about", "an", "and", "any", "are", "as", "at", "be", "been", "but", "by", "can", "did",
    "do", "does", "for", "from", "had", "has", "have", "he", "her", "him", "his", "how", "i",
    "if", "in", "is", "it", "its", "me", "much", "of", "on", "or", "she", "so", "some", "tell",
    "that", "the", "their", "them", "there", "they", "this", "to", "was", "were", "what", "when",
    "which", "who", "why", "will", "with", "would", "you", "your",
}

# Suffixes stripped longest-first; a stem shorter than this is left alone so
# short technical tokens ("aws", "api") survive intact.
_SUFFIXES = ("ing", "ion", "ed", "s")
_MIN_STEM = 3

# How much a query-expansion term counts relative to one the visitor typed.
# At 1.0 a broad synonym outvotes the actual subject of the question.
_EXPANSION_WEIGHT = 0.3

# Question vocabulary -> resume vocabulary. Recruiters ask "can he", "has he
# shipped", "is he a fit" -- none of which appear literally in a resume.
# Keys and values are stems (see `_stem`).
_SYNONYMS = {
    "ai": ["llm", "genai", "machine", "learn"],
    "agent": ["langgraph", "multi", "workflow"],
    "chatbot": ["rag", "chatbot", "retrieval"],
    "experience": ["experience", "work", "job", "role"],
    "fit": ["hire", "fit", "recruiter", "candidate"],
    "good": ["hire", "fit", "strength"],
    "hallucinat": ["guardrail", "ground", "unsupported", "grounding"],
    "hire": ["hire", "fit", "recruiter"],
    "llm": ["llm", "openai", "langchain", "rag", "prompt", "transformer", "nlp", "huggingface"],
    "model": ["llm", "openai", "transformer"],
    "ml": ["llm", "nlp", "learn"],
    "product": ["experience", "aws", "deploy", "release"],
    "rag": ["rag", "pinecone", "langchain", "retrieval", "embedding"],
    "ship": ["built", "deliver", "shipped"],
    "vector": ["pinecone", "embedding", "rag"],
}


# Multi-word terms collapsed to their canonical token before tokenizing.
# Without this, "large language models" matches the *programming* languages chunk —
# the tokens overlap but the meaning doesn't. Longest phrases first.
_PHRASES = (
    ("natural language processing", "nlp"),
    ("large language model", "llm"),
    ("language model", "llm"),
    ("machine learning", "ml"),
    ("vector database", "pinecone embedding"),
    ("vector search", "pinecone embedding"),
    ("retrieval augmented generation", "rag"),
)


def _normalise_phrases(text):
    lowered = text.lower()
    for phrase, canonical in _PHRASES:
        if phrase in lowered:
            lowered = lowered.replace(phrase, canonical)
    return lowered


def _stem(token):
    """Crude but predictable suffix stripper — enough to merge plurals and -ing/-ion."""
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM:
            return token[: -len(suffix)]
    return token


def _tokenize(text):
    return [
        _stem(t)
        for t in _TOKEN.findall(_normalise_phrases(text))
        if t not in _STOPWORDS and len(t) > 1
    ]


def _weighted_terms(query):
    """Return {term: weight}; typed terms weigh 1.0, expansions much less."""
    terms = {}
    typed = _tokenize(query)
    for token in typed:
        terms[token] = 1.0
    for token in typed:
        for synonym in _SYNONYMS.get(token, ()):
            stem = _stem(synonym)
            # Never let an expansion downgrade a term the visitor actually typed.
            terms.setdefault(stem, _EXPANSION_WEIGHT)
    return terms


class BM25Index:
    K1 = 1.5
    B = 0.75

    def __init__(self, chunks):
        self.chunks = chunks
        # Titles and tags are repeated so a tag match outweighs an incidental
        # body match — but only x2, since some tags are shared by every chunk of
        # a category and carry no discriminating signal.
        self.docs = [
            _tokenize(c["title"]) * 2 + _tokenize(" ".join(c["tags"])) * 2 + _tokenize(c["text"])
            for c in chunks
        ]
        self.freqs = [Counter(d) for d in self.docs]
        self.lengths = [len(d) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0

        doc_freq = Counter()
        for doc in self.docs:
            doc_freq.update(set(doc))
        n = len(self.docs)
        self.idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()
        }

    def search(self, query, top_k=5, min_score=0.5):
        terms = _weighted_terms(query)
        if not terms:
            return []

        scored = []
        for i, freq in enumerate(self.freqs):
            length = self.lengths[i] or 1
            score = 0.0
            for term, weight in terms.items():
                tf = freq.get(term)
                if not tf:
                    continue
                idf = self.idf.get(term, 0.0)
                denom = tf + self.K1 * (1 - self.B + self.B * length / (self.avg_len or 1))
                score += weight * idf * (tf * (self.K1 + 1)) / denom
            if score > min_score:
                scored.append((score, i))

        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [{**self.chunks[i], "score": round(score, 3)} for score, i in scored[:top_k]]


INDEX = BM25Index(CHUNKS)


def retrieve(query, top_k=5):
    """Top matching resume chunks, or an empty list when nothing matches.

    Returning [] is deliberate. An earlier version substituted a few default
    chunks here so an answer always had *something* to work with, but that
    destroyed the only signal that says "the resume doesn't cover this" — so a
    question about hobbies came back with the career summary attached, reading
    as though it were the answer. Empty is the honest result; callers decide how
    to decline.
    """
    return INDEX.search(query, top_k=top_k)


def build_context(query, top_k=5):
    """Render retrieved chunks as a labelled context block for the prompt.

    Returns (context, hits, grounded). `grounded` is False when the corpus has
    nothing relevant, which callers must handle rather than answering anyway.
    """
    hits = retrieve(query, top_k=top_k)
    if not hits:
        return "", [], False
    blocks = [f"[{h['title']}]\n{h['text']}" for h in hits]
    return "\n\n".join(blocks), hits, True
