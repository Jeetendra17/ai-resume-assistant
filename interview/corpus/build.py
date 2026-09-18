"""Parse the interview corpus from Markdown into structured records.

The corpus is the set of questions visitors ask this site about Jeetendra, with
the answers the assistant should give. It is authored as Markdown because a human
has to be able to read and edit it — a document first and a dataset second. This
module is the single place that turns it into records, so retrieval, the
fine-tuning dataset builder and the site all consume exactly the same objects.

Format, per source file:

    # Part 2 — The Venera Generative-AI Chatbot

    > One-paragraph introduction to the part.

    ### Q2.2 — Why Qwen and open-weight models rather than an API?

    - **Difficulty:** engineer
    - **Tags:** qwen, open-weights, on-premise
    - **Asked by:** Engineer, Hiring Manager

    **Answer.**

    ...prose, which may itself use **Bold lead-ins.** freely...

    **Follow-up.** ...

    **Grounded in.** Pulsar on-premise deployment, Qwen open-weight models

Parsing is strict about the structural markers: `### Q<id> —` headings,
`- **Key:** value` metadata lines, and exactly three section labels —
`**Answer.**`, `**Follow-up.**` and `**Grounded in.**`. Any other bold lead-in
is ordinary prose and stays inside the answer.

Run directly to rebuild `questions.json`:

    python -m interview.corpus.build
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

SOURCE_DIR = Path(__file__).parent / "source"
OUTPUT = Path(__file__).parent / "questions.json"

# A "page" is not a real unit for a Markdown file, so the document's length is
# reported against a stated constant rather than implied. 500 words is a full
# single-spaced page; the README says so too, so the 100-page claim is checkable
# rather than asserted.
WORDS_PER_PAGE = 500

_PART_RE = re.compile(r"^#\s+Part\s+(\d+)\s+[—-]\s+(.+?)\s*$", re.M)
_QUESTION_RE = re.compile(r"^###\s+Q([\d.]+)\s+[—-]\s+(.+?)\s*$", re.M)
_META_RE = re.compile(r"^-\s+\*\*(?P<key>[A-Za-z ]+):\*\*\s*(?P<value>.+?)\s*$", re.M)
# Only these labels delimit sections. An earlier version accepted any bold
# lead-in (`**Anything.**`) as a new section, which silently chopped every
# answer that uses bold lead-ins in its own prose -- "**Situation.**" in the
# behavioural answers, "**Scale.**" in a list of gaps -- into fragments. The
# page count still looked right because it summed the fragments; retrieval,
# which indexes the answer field, would have searched truncated text.
SECTION_LABELS = ("Answer", "Follow-up", "Grounded in")
_BLOCK_RE = re.compile(
    r"^\*\*(?P<label>" + "|".join(re.escape(l) for l in SECTION_LABELS) + r")\.\*\*\s*",
    re.M,
)

_LIST_KEYS = {"tags", "asked by"}


@dataclass
class Question:
    """One interview question and everything the corpus says about it."""

    id: str
    part: int
    topic: str
    question: str
    answer: str
    difficulty: str = "intermediate"
    tags: list[str] = field(default_factory=list)
    asked_by: list[str] = field(default_factory=list)
    follow_up: str = ""
    # Which resume facts the answer rests on. This is not decoration: the corpus
    # makes claims about a real person's record, so every answer has to be
    # traceable to something `data/profile.py` actually says. `build()` refuses
    # to produce a corpus containing an answer that cites nothing.
    grounded_in: list[str] = field(default_factory=list)
    extras: dict[str, str] = field(default_factory=dict)

    @property
    def words(self) -> int:
        parts = [self.question, self.answer, self.follow_up]
        parts.extend(self.extras.values())
        return sum(len(p.split()) for p in parts)

    def as_text(self) -> str:
        """Flat text used for indexing and for extractive fallback answers."""
        chunks = [self.question, self.answer]
        if self.follow_up:
            chunks.append(f"Follow-up: {self.follow_up}")
        return "\n\n".join(chunks)


def _slug(label: str) -> str:
    return label.strip().lower().replace(" ", "_").replace("-", "_").replace("'", "")


def _split_blocks(body: str) -> dict[str, str]:
    """Split a question body into its Answer / Follow-up / Grounded-in sections.

    Text before the first label is returned under the empty key, so a question
    that omits the `**Answer.**` label still parses.
    """
    marks = list(_BLOCK_RE.finditer(body))
    if not marks:
        return {"": body.strip()}

    blocks: dict[str, str] = {}
    lead = body[: marks[0].start()].strip()
    if lead:
        blocks[""] = lead

    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        text = body[mark.end() : end].strip()
        key = _slug(mark.group("label"))
        # A repeated label appends rather than overwrites.
        blocks[key] = f"{blocks[key]}\n\n{text}" if key in blocks else text

    return blocks


def parse_file(path: Path) -> tuple[int, str, str, list[Question]]:
    """Return (part number, topic, intro, questions) for one source file."""
    raw = path.read_text(encoding="utf-8")

    head = _PART_RE.search(raw)
    if not head:
        raise ValueError(f"{path.name}: missing a `# Part N — Title` heading")
    part, topic = int(head.group(1)), head.group(2).strip()

    marks = list(_QUESTION_RE.finditer(raw))
    intro_end = marks[0].start() if marks else len(raw)
    intro = "\n".join(
        line.lstrip("> ").rstrip()
        for line in raw[head.end() : intro_end].splitlines()
        if line.startswith(">")
    ).strip()

    questions: list[Question] = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        body = raw[mark.end() : end]

        meta: dict[str, object] = {}
        for m in _META_RE.finditer(body):
            key = m.group("key").strip().lower()
            value = m.group("value").strip()
            meta[key] = [v.strip() for v in value.split(",") if v.strip()] if key in _LIST_KEYS else value
        body = _META_RE.sub("", body)

        blocks = _split_blocks(body)
        answer = blocks.pop("answer", blocks.pop("", ""))
        follow_up = blocks.pop("follow_up", "")
        grounded = blocks.pop("grounded_in", "")

        qid = f"{path.stem.split('-')[0]}-{mark.group(1).replace('.', '-')}"
        questions.append(
            Question(
                id=qid,
                part=part,
                topic=topic,
                question=mark.group(2).strip(),
                answer=answer.strip(),
                difficulty=str(meta.get("difficulty", "recruiter")),
                tags=list(meta.get("tags", [])),
                asked_by=list(meta.get("asked by", [])),
                follow_up=follow_up.strip(),
                grounded_in=[g.strip() for g in grounded.split(",") if g.strip()],
                extras={k: v for k, v in blocks.items() if v},
            )
        )

    return part, topic, intro, questions


def build() -> dict:
    """Parse every source file into one corpus document."""
    files = sorted(SOURCE_DIR.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"no corpus sources in {SOURCE_DIR}")

    parts, questions = [], []
    for path in files:
        part, topic, intro, found = parse_file(path)
        if not found:
            raise ValueError(f"{path.name}: parsed 0 questions — check the `### Q…` headings")
        parts.append({"part": part, "topic": topic, "intro": intro, "count": len(found), "file": path.name})
        questions.extend(found)

    # Fail loudly on a malformed entry. A missing section does not raise on its
    # own -- it just produces an empty field -- and a truncated answer is exactly
    # the kind of fault that looks fine in aggregate statistics.
    problems = []
    for q in questions:
        if len(q.answer.split()) < 60:
            problems.append(f"{q.id}: answer is only {len(q.answer.split())} words")
        if not q.grounded_in:
            problems.append(f"{q.id}: no **Grounded in.** facts")
        if not q.follow_up:
            problems.append(f"{q.id}: no **Follow-up.**")
        if q.extras:
            problems.append(f"{q.id}: unexpected sections {sorted(q.extras)}")
    if problems:
        raise ValueError("corpus check failed:\n  " + "\n  ".join(problems))

    seen: dict[str, str] = {}
    for q in questions:
        if q.id in seen:
            raise ValueError(f"duplicate question id {q.id!r} ({seen[q.id]} and {q.topic})")
        seen[q.id] = q.topic

    words = sum(q.words for q in questions)
    return {
        "parts": parts,
        "questions": [asdict(q) for q in questions],
        "stats": {
            "parts": len(parts),
            "questions": len(questions),
            "words": words,
            "pages": round(words / WORDS_PER_PAGE, 1),
            "words_per_page": WORDS_PER_PAGE,
            "topics": sorted({q.topic for q in questions}),
            "tags": sorted({t for q in questions for t in q.tags}),
        },
    }


def load() -> dict:
    """Read the built corpus, building it first if it is missing or stale."""
    if not OUTPUT.exists():
        return write()
    built = json.loads(OUTPUT.read_text(encoding="utf-8"))
    newest = max((p.stat().st_mtime for p in SOURCE_DIR.glob("*.md")), default=0)
    if newest > OUTPUT.stat().st_mtime:
        return write()
    return built


def write() -> dict:
    doc = build()
    OUTPUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


if __name__ == "__main__":
    doc = write()
    s = doc["stats"]
    print(f"parts      {s['parts']}")
    print(f"questions  {s['questions']}")
    print(f"words      {s['words']:,}")
    print(f"pages      {s['pages']}  (at {s['words_per_page']} words/page)")
    print(f"topics     {len(s['topics'])}")
    print(f"tags       {len(s['tags'])}")
    print(f"-> {OUTPUT}")
