"""Retrieval evaluation set.

The whole premise of this site is that answer quality is measured rather than
eyeballed, so retrieval gets an eval set too. Each case is a question a recruiter
would plausibly ask, paired with the chunk(s) that must appear in the top 3.

Run:  python eval_retrieval.py           # summary
      python eval_retrieval.py -v        # show every case
"""

import sys

sys.path.insert(0, ".")

from core.rag import retrieve  # noqa: E402

TOP_K = 3

# (question, {chunk ids of which at least one must land in the top TOP_K})
CASES = [
    # --- the failure that prompted this eval set -------------------------------
    ("What has he actually shipped with LLMs?",
     {"proj-document-q&a-chatbot-(rag)", "proj-nlp-pipelines-with-hugging-face",
      "skill-ai-and-llm-engineering", "exp-2"}),
    ("Has he built anything with large language models?",
     {"proj-document-q&a-chatbot-(rag)", "proj-nlp-pipelines-with-hugging-face",
      "skill-ai-and-llm-engineering", "exp-2"}),
    ("Does he have hands-on LLM experience or just coursework?",
     {"proj-document-q&a-chatbot-(rag)", "proj-nlp-pipelines-with-hugging-face",
      "skill-ai-and-llm-engineering", "exp-2"}),

    # --- fit / screening -------------------------------------------------------
    ("Is he a fit for an AI Engineer role?", {"pitch", "identity", "skill-ai-and-llm-engineering"}),
    ("Why should we hire him?", {"pitch", "metrics"}),
    ("Is he available and how do I reach him?", {"availability"}),
    ("What are his strongest measurable results?", {"metrics"}),

    # --- experience ------------------------------------------------------------
    ("Where does he work right now?", {"exp-0", "identity"}),
    ("How much production experience does he have?", {"exp-0", "exp-1", "pitch"}),
    ("Tell me about his QA internship", {"exp-1"}),
    ("Has he done any mobile development?", {"exp-3", "proj-real-time-chat-app"}),

    # --- specific projects -----------------------------------------------------
    ("Walk me through his RAG project", {"proj-document-q&a-chatbot-(rag)"}),
    ("What did he do with Pinecone and vector search?",
     {"proj-document-q&a-chatbot-(rag)", "skill-ai-and-llm-engineering"}),
    ("Tell me about the Hugging Face work", {"proj-nlp-pipelines-with-hugging-face"}),
    ("Has he used Selenium?", {"proj-selenium-grid-automation", "skill-testing-and-quality", "exp-1"}),
    ("Any database work?", {"proj-student-data-entry-system", "skill-languages"}),

    # --- skills ----------------------------------------------------------------
    ("What programming languages does he know?", {"skill-languages"}),
    ("Does he know AWS or cloud platforms?", {"skill-cloud-and-devops", "exp-0", "exp-1"}),
    ("What testing tools has he used?", {"skill-testing-and-quality"}),
    ("Does he know LangChain and LangGraph?", {"skill-ai-and-llm-engineering", "exp-2"}),

    # --- education -------------------------------------------------------------
    ("What did he study and what was his CGPA?", {"education"}),
    ("What certifications does he hold?", {"certifications"}),
    ("What is he learning right now?", {"certifications", "exp-2", "about-bio"}),

    # --- about / meta ----------------------------------------------------------
    ("Tell me about his background and how he got into AI", {"about-bio", "identity"}),
    ("How does this assistant work?", {"case-overview"}),
    ("Why did he use BM25 instead of embeddings?", {"case-bm25-instead-of-embeddings"}),
    ("What happens if the AI provider goes down?",
     {"case-it-answers-with-zero-api-keys", "case-nine-providers-one-interface"}),
    ("How do you stop it from hallucinating?", {"case-guardrails"}),
    ("What would he improve about this system?", {"case-next"}),
]


# Questions the resume genuinely does not answer. These must return NO chunks —
# retrieval used to substitute the career summary here, which read as though it
# had answered. Declining is the correct behaviour.
OUT_OF_SCOPE_CASES = [
    "what are his hobbies?",
    "i dont know what are his hobbies",
    "is he married?",
    "does he play cricket",
    "what are his salary expectations?",
    "can he relocate to Germany?",
    "who is the president of France?",
]

# Documented limitations, reported but not failing the build.
#
# Both retrieve a weak spurious match, and measurement says no global score
# threshold can exclude them: the weakest true positive scores 2.23 ("where does
# he work right now?") while the strongest of these scores 3.19. Tuning a
# threshold to catch them would silently break legitimate questions, so these are
# handled one layer up — the system prompt instructs the model to decline when
# the retrieved context doesn't actually address the question.
KNOWN_WEAK = [
    ("what's his date of birth?",
     "matches 'dates' in the guardrails text; no birth date exists in the corpus"),
    ("write me a poem about databases",
     "databases ARE in the resume, so retrieval is arguably right — refusing the "
     "off-task request is the prompt's job, not the index's"),
]


def run(verbose=False):
    passed, failures = 0, []

    for question in OUT_OF_SCOPE_CASES:
        hits = retrieve(question, top_k=TOP_K)
        ok = len(hits) == 0
        if ok:
            passed += 1
        else:
            failures.append((f"[out-of-scope] {question}", {"<no chunks>"}, hits))
        if verbose:
            print(f"[{'PASS' if ok else 'FAIL'}] (out-of-scope) {question}")
            for h in hits:
                print(f"          {h.get('score', 0):6.2f}  {h['title']}")

    for question, expected in CASES:
        hits = retrieve(question, top_k=TOP_K)
        got = [h["id"] for h in hits]
        ok = bool(expected & set(got))

        if ok:
            passed += 1
        else:
            failures.append((question, expected, hits))

        if verbose:
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {question}")
            for h in hits:
                star = "*" if h["id"] in expected else " "
                print(f"        {star} {h.get('score', 0):6.2f}  {h['title']}")

    total = len(CASES) + len(OUT_OF_SCOPE_CASES)
    pct = passed / total * 100
    print(f"\n{'=' * 62}")
    print(f"recall@{TOP_K} + out-of-scope: {passed}/{total} ({pct:.0f}%)")
    print(f"  {len(CASES)} questions that must retrieve the right chunk")
    print(f"  {len(OUT_OF_SCOPE_CASES)} questions that must retrieve nothing")
    print("=" * 62)

    if KNOWN_WEAK:
        print(f"\n{len(KNOWN_WEAK)} known limitation(s), handled by the prompt layer:")
        for question, note in KNOWN_WEAK:
            hits = retrieve(question, top_k=1)
            top = f"{hits[0]['score']:.2f} {hits[0]['id']}" if hits else "no match"
            print(f"  \"{question}\"")
            print(f"     top hit: {top}")
            print(f"     {note}")

    if failures:
        print(f"\n{len(failures)} failing case(s):\n")
        for question, expected, hits in failures:
            print(f"  Q: {question}")
            print(f"     expected one of: {sorted(expected)}")
            print("     got:")
            for h in hits:
                print(f"        {h.get('score', 0):6.2f}  {h['id']}")
            print()

    return passed, total


def run_quiet():
    """(passed, total) with no output — used by the app to display a live score."""
    passed = sum(1 for q in OUT_OF_SCOPE_CASES if not retrieve(q, top_k=TOP_K))
    passed += sum(
        1 for q, expected in CASES if expected & {h["id"] for h in retrieve(q, top_k=TOP_K)}
    )
    return passed, len(CASES) + len(OUT_OF_SCOPE_CASES)


if __name__ == "__main__":
    p, t = run(verbose="-v" in sys.argv)
    sys.exit(0 if p == t else 1)
