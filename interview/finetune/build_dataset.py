"""Build the fine-tuning dataset from the interview corpus.

    python -m interview.finetune.build_dataset

Writes, under interview/finetune/data/:

* train.jsonl / val.jsonl -- chat-format supervised examples (system, user, assistant),
  the shape every open-weight SFT trainer and the hosted fine-tuning APIs accept.
* exemplars.json -- short question/answer pairs from the *training* split only, which
  the live site retrieves as few-shot examples (prompt v4/v5): the zero-cost stand-in
  for serving a tuned model.
* stats.json -- sizes, split, and the contamination report.

Design decisions, each one there because the alternative fails silently:

* **The source answer is always inside the example's context.** If retrieval missed it
  and the target still contained its facts, the model would be trained to state things
  its context does not support -- i.e. trained to hallucinate. The gold entry is placed
  among two retrieved neighbours at a deterministic position, so position is not a cue.
* **Targets are concise.** The corpus answers run ~300 words; the live assistant answers
  in ~150. Training on the long form would teach a register the site then fights.
* **Refusals are in the data.** A dataset of only answerable questions teaches that every
  question has an answer. The refusal questions here are disjoint from the retrieval
  eval's must-decline set, and the build asserts it.
* **Validation is held out by question, stratified by part, and contamination-checked**
  against both the training split and the retrieval eval.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from core.rag import tokenize
from interview.prompting.registry import DECLINE, VERSIONS, format_context
from interview.retrieval import eval as retrieval_eval
from interview.retrieval import hybrid
from interview.text import concise

DATA = Path(__file__).parent / "data"
SYSTEM = VERSIONS["v3"].system          # the scoped, grounded system prompt
VAL_EVERY = 6                            # every 6th question within a part -> ~16% validation

# Out-of-scope questions for refusal training. Deliberately different from the
# retrieval eval's MUST_DECLINE list, which must stay unseen by any trained model.
REFUSALS = [
    "what is his star sign",
    "does he have any siblings",
    "what did he have for breakfast",
    "who is the prime minister of india",
    "can you write me a cover letter for my own job application",
    "what is his favourite food",
    "is he a morning person",
    "what music does he listen to",
    "explain quantum computing to me",
    "what is 17 times 23",
    "does he like dogs or cats",
    "what is his home address",
    "which political party does he support",
    "translate hello into french",
    "what games does he play",
    "how old is his father",
]


def _shingles(text: str, n: int = 8) -> set:
    toks = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(toks[i : i + n]) for i in range(max(0, len(toks) - n + 1))}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def build() -> dict:
    index = hybrid.load()                 # local retrieval only: no API calls, reproducible
    docs = index.docs

    # Stratified hold-out by question.
    position_in_part = Counter()
    split = {}
    for d in docs:
        position_in_part[d["part"]] += 1
        split[d["id"]] = "val" if position_in_part[d["part"]] % VAL_EVERY == 0 else "train"

    records = {"train": [], "val": []}
    for d in docs:
        neighbours, _ = index.search(d["question"], top_k=4, retrievers=("bm25", "lsa"))
        others = [n for n in neighbours if n["id"] != d["id"]][:2]
        slot = sum(map(ord, d["id"])) % 3          # deterministic, not always first
        context = others[:slot] + [d] + others[slot:]
        records[split[d["id"]]].append({
            "id": d["id"],
            "kind": "answer",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"CONTEXT\n{format_context(context)}\n\nQUESTION\n{d['question']}"},
                {"role": "assistant", "content": concise(d["answer"])},
            ],
        })

    overlap = set(REFUSALS) & set(retrieval_eval.MUST_DECLINE)
    assert not overlap, f"refusal training questions leak into the eval: {overlap}"
    for i, question in enumerate(REFUSALS):
        neighbours, _ = index.search(question, top_k=3, retrievers=("bm25", "lsa"))
        records["val" if i % VAL_EVERY == VAL_EVERY - 1 else "train"].append({
            "id": f"refusal-{i:02d}",
            "kind": "refusal",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"CONTEXT\n{format_context(neighbours)}\n\nQUESTION\n{question}"},
                {"role": "assistant", "content": DECLINE},
            ],
        })

    # ── contamination report ──────────────────────────────────────────────
    train_answers = {r["id"]: _shingles(r["messages"][-1]["content"])
                     for r in records["train"] if r["kind"] == "answer"}
    near_dupes = []
    for r in records["val"]:
        if r["kind"] != "answer":
            continue
        s = _shingles(r["messages"][-1]["content"])
        for tid, ts in train_answers.items():
            j = _jaccard(s, ts)
            if j >= 0.3:
                near_dupes.append({"val": r["id"], "train": tid, "jaccard": round(j, 3)})

    eval_questions = [q for q, _ in retrieval_eval.MUST_MATCH + retrieval_eval.EXACT_TERM]
    train_questions = {r["id"]: set(tokenize(r["messages"][1]["content"].rsplit("QUESTION\n", 1)[-1]))
                       for r in records["train"]}
    eval_verbatim = []
    for q in eval_questions:
        qt = set(tokenize(q))
        for tid, tt in train_questions.items():
            if qt and _jaccard(qt, tt) >= 0.8:
                eval_verbatim.append({"eval": q, "train": tid})

    stats = {
        "train": len(records["train"]),
        "val": len(records["val"]),
        "answer_examples": sum(r["kind"] == "answer" for s in records.values() for r in s),
        "refusal_examples": sum(r["kind"] == "refusal" for s in records.values() for r in s),
        "target_words_mean": round(
            sum(len(r["messages"][-1]["content"].split()) for s in records.values() for r in s)
            / sum(len(s) for s in records.values()), 1),
        "system_prompt": "v3",
        "contamination": {
            "val_vs_train_near_duplicates": near_dupes,
            "retrieval_eval_questions_near_verbatim_in_train": eval_verbatim,
            "note": (
                "Retrieval-eval questions are reworded paraphrases of corpus questions by design, so "
                "a model fine-tuned on this corpus has seen the *answers* those questions target. "
                "Evaluate a fine-tuned model on the val split, not on the retrieval eval."
            ),
        },
    }

    exemplars = [
        {"id": r["id"], "question": r["messages"][1]["content"].rsplit("QUESTION\n", 1)[-1],
         "answer": r["messages"][-1]["content"]}
        for r in records["train"] if r["kind"] == "answer"
    ]
    return {"records": records, "stats": stats, "exemplars": exemplars}


def write() -> dict:
    out = build()
    DATA.mkdir(exist_ok=True)
    for name in ("train", "val"):
        with open(DATA / f"{name}.jsonl", "w", encoding="utf-8", newline="\n") as fh:
            for r in out["records"][name]:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (DATA / "exemplars.json").write_text(json.dumps(out["exemplars"], ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "stats.json").write_text(json.dumps(out["stats"], indent=2), encoding="utf-8")
    return out["stats"]


if __name__ == "__main__":
    s = write()
    c = s["contamination"]
    print(f"train {s['train']}  val {s['val']}  "
          f"(answers {s['answer_examples']}, refusals {s['refusal_examples']})  "
          f"mean target {s['target_words_mean']} words")
    print(f"contamination: {len(c['val_vs_train_near_duplicates'])} val/train near-duplicates, "
          f"{len(c['retrieval_eval_questions_near_verbatim_in_train'])} eval questions near-verbatim in train")
    for d in c["val_vs_train_near_duplicates"]:
        print(f"  near-duplicate: {d}")
    print(f"-> {DATA}")
