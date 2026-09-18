"""Retrieved few-shot examples: the zero-cost stand-in for a fine-tuned model.

A LoRA adapter trained on `data/train.jsonl` would learn the assistant's register --
concise, direct, honest about level. Serving one costs GPU time; a portfolio on a
free tier cannot. So the live site gets part of that effect for free: for each
question it retrieves the two most similar training examples and shows them to the
model as examples of a good answer (prompt v4/v5). Whether that actually helps is
measured in the prompt eval, v3 against v4, rather than assumed.

Examples come from the *training* split only, and never duplicate an entry already
in the question's retrieved context -- an example that is also the source would teach
nothing about style and just repeat the facts.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from core.rag import BM25Index

PATH = Path(__file__).parent / "data" / "exemplars.json"


@lru_cache(maxsize=1)
def _load():
    if not PATH.exists():
        return [], None
    items = json.loads(PATH.read_text(encoding="utf-8"))
    index = BM25Index([{"id": e["id"], "title": e["question"], "tags": [], "text": e["question"]}
                       for e in items])
    return items, index


def select(question: str, exclude_ids: set[str], k: int = 2) -> list[dict]:
    items, index = _load()
    if not items:
        return []
    by_id = {e["id"]: e for e in items}
    picked = []
    for hit in index.search(question, top_k=k + len(exclude_ids) + 2, min_score=0.0):
        if hit["id"] not in exclude_ids:
            picked.append(by_id[hit["id"]])
        if len(picked) == k:
            break
    return picked
