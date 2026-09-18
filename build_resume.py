"""Render the resume PDF from `data/profile.py`.

The resume used to be a hand-maintained Word export, which meant the site and the
PDF a recruiter downloaded could disagree — and did: the CGPA on the page and the
CGPA in the file were different numbers for months, because nobody edits both.
This generates the PDF from the same module the site and the retrieval index read,
so a content change updates all three or none of them.

    python build_resume.py            # writes static/files/<resume_file>
    python build_resume.py --check    # fails if the PDF is older than profile.py

Layout notes: single column, real text, standard section names, no tables used for
positioning and nothing in the page margins. That is deliberate — applicant
tracking systems parse a two-column resume by reading straight across the page and
interleaving the columns into nonsense.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
)

from data.profile import (
    CERTIFICATIONS,
    EDUCATION,
    EXPERIENCE,
    PROFILE,
    PROJECTS,
    SKILL_GROUPS,
)

ROOT = Path(__file__).parent
OUT = ROOT / "static" / "files" / PROFILE["resume_file"]

INK = colors.HexColor("#111827")
INK_2 = colors.HexColor("#374151")
INK_3 = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#1d4ed8")
RULE = colors.HexColor("#d1d5db")

BODY = 8.8
LEAD = 11.3

# Experience entries whose "company" is really a self-directed track. They are
# rendered under Selected Projects instead, so they do not appear twice.
SKIP_AS_EMPLOYMENT = {"Self-directed / Bootcamp"}


def _styles(scale: float = 1.0) -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "base",
        fontName="Helvetica",
        fontSize=BODY * scale,
        leading=LEAD * scale,
        textColor=INK_2,
        spaceAfter=0,
    )
    return {
        "name": ParagraphStyle(
            "name", parent=base, fontName="Helvetica-Bold", fontSize=19 * scale, leading=22 * scale,
            textColor=INK, spaceAfter=2.5,
        ),
        "role": ParagraphStyle(
            "role", parent=base, fontSize=9.6 * scale, leading=12 * scale, textColor=ACCENT,
            fontName="Helvetica-Bold", spaceAfter=3.5,
        ),
        "contact": ParagraphStyle(
            "contact", parent=base, fontSize=8.3 * scale, leading=11 * scale, textColor=INK_3,
        ),
        "section": ParagraphStyle(
            "section", parent=base, fontName="Helvetica-Bold", fontSize=8.6 * scale, leading=10 * scale,
            textColor=INK, spaceBefore=0, spaceAfter=0,
        ),
        "summary": ParagraphStyle(
            "summary", parent=base, alignment=TA_JUSTIFY, spaceAfter=0,
        ),
        "jobhead": ParagraphStyle(
            "jobhead", parent=base, fontName="Helvetica-Bold", fontSize=9.4 * scale, leading=12 * scale,
            textColor=INK, spaceAfter=0.5,
        ),
        "jobmeta": ParagraphStyle(
            "jobmeta", parent=base, fontSize=8.2 * scale, leading=10.5 * scale, textColor=INK_3,
            spaceAfter=2.5 * scale,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base, leftIndent=8.5, bulletIndent=1.5,
            spaceAfter=1.9 * scale, alignment=TA_JUSTIFY,
        ),
        "skill": ParagraphStyle(
            "skill", parent=base, leftIndent=52, firstLineIndent=-52, spaceAfter=2.6 * scale,
        ),
        "line": ParagraphStyle("line", parent=base, spaceAfter=2.6),
    }


class Rule(Flowable):
    """A hairline under a section heading, drawn the full frame width."""

    def __init__(self, width: float = 0, thickness: float = 0.6):
        super().__init__()
        self.width, self.thickness = width, thickness
        self.height = thickness

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        return avail_w, self.thickness

    def draw(self):
        self.canv.setStrokeColor(RULE)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


def _esc(text: str) -> str:
    """Escape for reportlab's mini-HTML, and normalise punctuation it renders badly."""
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    return text


def _summarise(text: str, min_words: int, max_words: int) -> str:
    """Whole sentences from the start of `text`, until `min_words` is reached.

    Keeps taking sentences until the line actually says something, then stops —
    rather than stopping at a budget, which cut the portfolio entry down to
    "The site you're reading." and told a recruiter nothing. `max_words` only
    prevents *starting* another sentence once the line is already long, so the
    result is always whole sentences and never a fragment.
    """
    sentences = [s for s in re.split(r"(?<=\.)\s+", text.strip()) if s]
    out: list[str] = []
    words = 0
    for sentence in sentences:
        if out and words >= max_words:
            break
        out.append(sentence)
        words += len(sentence.split())
        if words >= min_words:
            break
    return " ".join(out).strip()


def _section(title: str, styles, scale: float = 1.0) -> list:
    return [
        Spacer(1, 5.5 * scale),
        Paragraph(f"<b>{_esc(title).upper()}</b>", styles["section"]),
        Spacer(1, 2.2 * scale),
        Rule(),
        Spacer(1, 4 * scale),
    ]


def _titled(title: str, meta: str, styles, style: str = "jobhead") -> Paragraph:
    """A bold title followed by dimmed secondary text on the same line.

    Deliberately not a two-column table with the date flush right: that reads
    well to a human and badly to a resume parser, which flattens the row and can
    splice the date into the job title.
    """
    return Paragraph(
        f'{_esc(title)}'
        f'<font color="#6b7280" size="8.2">  |  {_esc(meta)}</font>',
        styles[style],
    )


def build(scale: float = 1.0) -> Path:
    styles = _styles(scale)
    story: list = []

    # ── header ────────────────────────────────────────────────────────────
    story.append(Paragraph(_esc(PROFILE["name"]), styles["name"]))
    story.append(Paragraph(_esc(PROFILE["role"]), styles["role"]))

    linkedin = PROFILE["linkedin"].replace("https://", "")
    contact = "  |  ".join(
        [
            PROFILE["phone"],
            PROFILE["email"],
            PROFILE["location"].replace(", India", ""),
            linkedin,
            PROFILE["site"].replace("https://", ""),
        ]
    )
    story.append(Paragraph(_esc(contact), styles["contact"]))
    story.append(Spacer(1, 3))
    story.append(Rule(thickness=1.1))

    # ── summary ───────────────────────────────────────────────────────────
    story += _section("Professional Summary", styles, scale)
    story.append(Paragraph(_esc(PROFILE["summary"]), styles["summary"]))

    # ── skills ────────────────────────────────────────────────────────────
    story += _section("Technical Skills", styles, scale)
    for group in SKILL_GROUPS:
        items = ", ".join(group["items"])
        story.append(
            Paragraph(
                f'<b><font color="#111827">{_esc(group["name"])}:</font></b> {_esc(items)}',
                styles["skill"],
            )
        )

    # ── experience ────────────────────────────────────────────────────────
    # The self-directed track is real work but it is not employment, and every
    # item in it already appears under Selected Projects. Listing it in both
    # places reads as padding and costs the space that pushed this to two pages.
    story += _section("Experience", styles, scale)
    for job in EXPERIENCE:
        if job["company"] in SKIP_AS_EMPLOYMENT:
            continue
        block = [
            _titled(job["role"], job["period"], styles),
            Paragraph(
                f'{_esc(job["company"])}, {_esc(job["location"])}', styles["jobmeta"]
            ),
        ]
        for point in job["points"]:
            block.append(
                Paragraph(_esc(point), styles["bullet"], bulletText="•")
            )
        block.append(Spacer(1, 3.8 * scale))
        # Keep the heading with at least its first bullet across a page break.
        story.append(KeepTogether(block[:3]))
        story.extend(block[3:])

    # ── projects ──────────────────────────────────────────────────────────
    story += _section("Selected Projects", styles, scale)
    for project in PROJECTS:
        if not project.get("featured"):
            continue
        # Take whole sentences up to a budget rather than a fixed count: the
        # first sentence alone gave "The site you're reading." for the portfolio
        # entry, which is true and tells a recruiter nothing.
        blurb = _summarise(project["blurb"], min_words=14, max_words=34)
        impact = _esc(project["impact"]) if project.get("impact") else ""
        stack = _esc(", ".join(project["stack"]))

        line = f"{_esc(blurb)} "
        if impact:
            line += f"<b>Impact:</b> {impact}. "
        line += f'<font color="#6b7280"><b>Stack:</b> {stack}</font>'

        story.append(
            KeepTogether(
                [
                    _titled(project["name"], project["category"], styles),
                    Paragraph(line, styles["bullet"], bulletText="•"),
                    Spacer(1, 3.5 * scale),
                ]
            )
        )

    # ── education ─────────────────────────────────────────────────────────
    story += _section("Education", styles, scale)
    for edu in EDUCATION:
        story.append(_titled(edu["degree"], edu["period"], styles))
        story.append(
            Paragraph(
                f'{_esc(edu["school"])}  |  {_esc(edu["score"])}', styles["jobmeta"]
            )
        )

    # ── certifications ────────────────────────────────────────────────────
    # In-progress training gets its own line with the syllabus, since that is
    # the part that speaks to the AI roles. Everything already completed is
    # condensed onto one line — four bullets of finished badges is the kind of
    # thing that pushes a resume onto a second page for no added signal.
    story += _section("Certifications & Training", styles, scale)
    ongoing = [c for c in CERTIFICATIONS if c["status"] != "Completed"]
    done = [c for c in CERTIFICATIONS if c["status"] == "Completed"]

    for cert in ongoing:
        story.append(
            Paragraph(
                f'<b><font color="#111827">{_esc(cert["name"])}</font></b> - '
                f'{_esc(cert["issuer"])} ({_esc(cert["status"])}). {_esc(cert["detail"])}',
                styles["bullet"],
                bulletText="•",
            )
        )
    if done:
        listed = "; ".join(f'{_esc(c["name"])} ({_esc(c["issuer"])})' for c in done)
        story.append(
            Paragraph(
                f'<b><font color="#111827">Completed:</font></b> {listed}',
                styles["bullet"],
                bulletText="•",
            )
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm * scale,
        bottomMargin=12 * mm * scale,
        title=f'{PROFILE["name"]} - {PROFILE["role"]}',
        author=PROFILE["name"],
        subject="Resume",
        creator="build_resume.py",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="resume", frames=[frame])])
    doc.build(story)
    return OUT


def page_count(path: Path) -> int:
    """Pages in the rendered PDF, without needing a PDF library to be installed.

    Counting `/Type /Page` occurrences is crude but exact for documents reportlab
    produces here — it writes one uncompressed page object each, and there are no
    external page trees to confuse the count.
    """
    return path.read_bytes().count(b"/Type /Page\n") or path.read_bytes().count(b"/Type /Page")


def build_one_page(floor: float = 0.86, step: float = 0.02) -> tuple[Path, float, int]:
    """Render at 100%, then shrink in small steps until it fits on one page.

    A one-page resume is the expectation for this level of experience, and the
    alternative — a second page holding four lines — looks worse than slightly
    tighter type. The floor exists so this degrades into an honest warning rather
    than silently producing something unreadable when content really is too long.
    """
    scale = 1.0
    while True:
        path = build(scale)
        pages = page_count(path)
        if pages <= 1 or scale <= floor:
            return path, scale, pages
        scale = round(scale - step, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the PDF is missing or older than data/profile.py",
    )
    args = parser.parse_args()

    profile_src = ROOT / "data" / "profile.py"
    if args.check:
        if not OUT.exists():
            print(f"[stale] {OUT.name} does not exist -- run: python build_resume.py")
            return 1
        if profile_src.stat().st_mtime > OUT.stat().st_mtime:
            print(f"[stale] profile.py is newer than {OUT.name} -- run: python build_resume.py")
            return 1
        print(f"[ok] {OUT.name} is up to date with profile.py")
        return 0

    path, scale, pages = build_one_page()
    fit = "1 page" if pages == 1 else f"{pages} pages (could not fit one)"
    print(
        f"wrote {path.relative_to(ROOT)}  "
        f"({path.stat().st_size / 1024:.0f} KB, {fit}, scale {scale:.2f})"
    )
    if pages > 1:
        print(
            "  Content exceeds one page even at minimum scale. Cut a bullet in "
            "data/profile.py rather than shrinking the type further."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
