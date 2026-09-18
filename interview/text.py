"""Small text helpers shared by the live pipeline and the offline dataset builder."""


def concise(answer: str, min_words: int = 60, max_words: int = 150) -> str:
    """Leading paragraphs of an answer, whole paragraphs only, within a word budget.

    Corpus answers run ~300 words; the live assistant answers in ~150. Used both for
    fine-tuning targets and for the extractive fallback, so the two stay consistent.
    """
    paragraphs = [p.strip() for p in answer.split("\n\n") if p.strip()]
    out, words = [], 0
    for p in paragraphs:
        n = len(p.split())
        if out and words + n > max_words:
            break
        out.append(p)
        words += n
        if words >= min_words:
            break
    return "\n\n".join(out)
