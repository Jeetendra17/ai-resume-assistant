"""Build the interview corpus retrieval index. Offline; needs numpy.

    python -m interview.index.build_index            # write the artifact
    python -m interview.index.build_index --check    # fail if it is stale

The live site must not need numpy, an embedding API or a vector database -- the
same zero-cost, zero-dependency rule the resume index follows. So the expensive
part happens here, once, and ships as a compact artifact:

* **Documents.** One per corpus question: the question, answer, follow-up, tags
  and grounding facts. Retrieval returns whole Q&A pairs because that is the unit a
  visitor's question maps to.
* **A latent semantic space (LSA).** A TF-IDF term-document matrix factorised with
  a truncated SVD. Terms that occur in the same answers land near each other, so a
  query about "making things up" can reach an answer that only ever says
  "hallucination". It is a small, honest form of semantic retrieval: no model,
  fully reproducible, and computed from this corpus alone.

At query time the runtime folds the query into the same space with plain Python
arithmetic -- a few thousand multiply-adds -- and fuses the result with BM25.

The vectors are quantised to int8 with one scale per matrix, which cuts the file
roughly 4x at a cost in cosine similarity well below anything that changes a
ranking at this corpus size.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

from core.rag import tokenize
from interview.corpus import build as corpus

ARTIFACT = Path(__file__).parent / "corpus_index.json.gz"
FORMAT_VERSION = 1

# Latent dimensions. A conventional default, not a tuned one: LSA only ranks when
# the embedding call is unavailable, and there it recalls 21/52 reworded questions
# against 47/52 for embeddings -- its dimension count is not what limits it.
DEFAULT_DIMS = 64

# Terms seen in only one document carry no co-occurrence signal for LSA and would
# only bloat the vocabulary. BM25 still indexes them at runtime.
MIN_DF = 2


def source_hash() -> str:
    """Content hash of every corpus source file, so staleness is checkable."""
    digest = hashlib.sha256()
    for path in sorted(corpus.SOURCE_DIR.glob("*.md")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def document_text(q: dict) -> str:
    """The text a document is indexed on. Mirrors how the runtime scores BM25."""
    return "\n".join(
        [q["question"], " ".join(q["tags"]), q["answer"], q["follow_up"], " ".join(q["grounded_in"])]
    )


def build(dims: int = DEFAULT_DIMS) -> dict:
    import numpy as np  # build-time only; the runtime never imports it

    doc = corpus.build()
    questions = doc["questions"]

    token_lists = [tokenize(document_text(q)) for q in questions]
    df = Counter(t for toks in token_lists for t in set(toks))
    vocab = sorted(t for t, n in df.items() if n >= MIN_DF)
    index = {t: i for i, t in enumerate(vocab)}
    n_docs = len(questions)

    idf = np.array([math.log(1 + n_docs / df[t]) for t in vocab])
    matrix = np.zeros((len(vocab), n_docs))
    for j, toks in enumerate(token_lists):
        for term, tf in Counter(toks).items():
            i = index.get(term)
            if i is not None:
                matrix[i, j] = (1 + math.log(tf)) * idf[i]

    u, s, vt = np.linalg.svd(matrix, full_matrices=False)
    k = min(dims, len(s))
    term_vecs = u[:, :k]                      # query folds in as sum of these
    doc_vecs = (vt[:k, :].T) * s[:k]          # document coordinates in the same space
    doc_vecs /= np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-12

    term_scale = float(np.abs(term_vecs).max() / 127.0)
    doc_scale = 1.0 / 127.0
    energy = float((s[:k] ** 2).sum() / (s ** 2).sum())

    return {
        "format": FORMAT_VERSION,
        "source_hash": source_hash(),
        "stats": {**doc["stats"], "vocab": len(vocab), "dims": k, "energy_retained": round(energy, 3)},
        "parts": doc["parts"],
        "docs": [
            {
                "id": q["id"],
                "part": q["part"],
                "topic": q["topic"],
                "question": q["question"],
                "answer": q["answer"],
                "follow_up": q["follow_up"],
                "tags": q["tags"],
                "grounded_in": q["grounded_in"],
                "difficulty": q["difficulty"],
                "asked_by": q["asked_by"],
            }
            for q in questions
        ],
        "lsa": {
            "dims": k,
            "vocab": vocab,
            "idf": [round(float(x), 4) for x in idf],
            "term_scale": term_scale,
            "term_vecs": np.rint(term_vecs / term_scale).astype(int).tolist(),
            "doc_scale": doc_scale,
            "doc_vecs": np.rint(doc_vecs / doc_scale).astype(int).tolist(),
        },
    }


# ── dense embeddings (optional, needs GEMINI_API_KEY at build time) ─────────
#
# LSA can only relate words that co-occur inside these 163 answers, so it cannot
# know that "pay" means "salary" when the corpus never uses both -- and the eval
# showed exactly that: hybrid BM25+LSA reached 44% recall@3 on reworded questions,
# no better than BM25 alone. A general embedding model carries that world
# knowledge. Documents are embedded once here; the runtime embeds only the query,
# and falls back to BM25+LSA if that call fails, so retrieval never *depends* on
# the network.

EMBED_MODEL = "gemini-embedding-2"
EMBED_DIMS = 256          # Matryoshka truncation: small artifact, little recall loss
# The free tier allows 100 embed requests per minute per model, and every item in
# a batch counts as one. A 100-item batch spends the whole minute on its own, so
# batches stay under it and the build waits out the window between them.
EMBED_BATCH = 80


def _embed_batch(texts: list[str], titles: list[str], api_key: str) -> list[list[float]]:
    """One batchEmbedContents call, retrying on 429 after the delay the API asks for."""
    import time
    import urllib.error

    for attempt in range(5):
        try:
            return _embed_batch_once(texts, titles, api_key)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            try:
                details = json.loads(exc.read().decode("utf-8"))["error"].get("details", [])
                delay = next(float(d["retryDelay"].rstrip("s")) for d in details if "retryDelay" in d)
            except Exception:
                delay = 60.0
            print(f"  rate limited; waiting {delay + 2:.0f}s (attempt {attempt + 1}/5)")
            time.sleep(delay + 2)
    raise RuntimeError("unreachable")


def _embed_batch_once(texts: list[str], titles: list[str], api_key: str) -> list[list[float]]:
    import urllib.request

    body = {
        "requests": [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": text}]},
                "taskType": "RETRIEVAL_DOCUMENT",
                "title": title,
                "outputDimensionality": EMBED_DIMS,
            }
            for text, title in zip(texts, titles)
        ]
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:batchEmbedContents",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "jeetendra-portfolio/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return [e["values"] for e in json.load(resp)["embeddings"]]


def dense_vectors(docs: list[dict], api_key: str) -> dict:
    import numpy as np

    texts = [document_text(d) for d in docs]
    titles = [d["question"] for d in docs]
    import time

    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        if i:
            time.sleep(62)  # let the per-minute quota window roll over between batches
        print(f"  embedding documents {i + 1}-{min(i + EMBED_BATCH, len(texts))} of {len(texts)}")
        vectors.extend(_embed_batch(texts[i : i + EMBED_BATCH], titles[i : i + EMBED_BATCH], api_key))
    matrix = np.array(vectors)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    scale = 1.0 / 127.0
    return {
        "model": EMBED_MODEL,
        "dims": EMBED_DIMS,
        "scale": scale,
        "doc_vecs": np.rint(matrix / scale).astype(int).tolist(),
    }


def write(dims: int = DEFAULT_DIMS, embed: bool = True) -> dict:
    artifact = build(dims)
    if embed:
        import os

        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if api_key:
            artifact["dense"] = dense_vectors(artifact["docs"], api_key)
        else:
            print("[warn] GEMINI_API_KEY not set: building without dense vectors (BM25+LSA only)")
    raw = json.dumps(artifact, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    # mtime=0 and no build timestamp in the payload: rebuilding an unchanged corpus
    # with the same vectors yields identical bytes, so git shows no spurious diff.
    with open(ARTIFACT, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(raw)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dims", type=int, default=DEFAULT_DIMS)
    parser.add_argument("--check", action="store_true", help="exit non-zero if the artifact is stale")
    parser.add_argument("--no-embed", action="store_true", help="skip dense vectors (no API call)")
    args = parser.parse_args()

    if args.check:
        if not ARTIFACT.exists():
            print(f"[stale] {ARTIFACT.name} is missing -- run: python -m interview.index.build_index")
            return 1
        with gzip.open(ARTIFACT, "rt", encoding="utf-8") as fh:
            stored = json.load(fh).get("source_hash")
        if stored != source_hash():
            print(f"[stale] corpus sources changed since {ARTIFACT.name} was built -- rebuild it")
            return 1
        print(f"[ok] {ARTIFACT.name} matches the corpus sources")
        return 0

    artifact = write(args.dims, embed=not args.no_embed)
    s = artifact["stats"]
    dense = artifact.get("dense")
    print(f"docs {s['questions']}  vocab {s['vocab']}  lsa dims {s['dims']}  "
          f"energy {s['energy_retained']:.1%}  "
          f"dense {dense['model'] + ' x' + str(dense['dims']) if dense else 'none'}  "
          f"-> {ARTIFACT.name} ({ARTIFACT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
