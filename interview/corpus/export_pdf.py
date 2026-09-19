"""Export the interview corpus as a printable PDF document.

    python -m interview.corpus.export_pdf

Generated from the same Markdown sources the assistant retrieves from, so the
document a visitor downloads and the answers the site gives cannot disagree.
Build-time only (needs reportlab); the site serves the committed PDF.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, ListFlowable, ListItem,
                                PageBreak, PageTemplate, Paragraph, Spacer)

from data.profile import PROFILE
from interview.corpus import build as corpus

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "static" / "files" / "Jeetendra_Kumar_Patel_Interview_QA.pdf"

INK, INK_2, INK_3, ACCENT = (colors.HexColor(c) for c in ("#111827", "#374151", "#6b7280", "#1d4ed8"))

BASE = ParagraphStyle("base", fontName="Helvetica", fontSize=10.5, leading=15, textColor=INK_2)
S = {
    "title": ParagraphStyle("title", parent=BASE, fontName="Helvetica-Bold", fontSize=26, leading=31,
                            textColor=INK, alignment=TA_CENTER),
    "subtitle": ParagraphStyle("subtitle", parent=BASE, fontSize=12, leading=17, textColor=INK_3,
                               alignment=TA_CENTER),
    "part": ParagraphStyle("part", parent=BASE, fontName="Helvetica-Bold", fontSize=17, leading=22,
                           textColor=INK, spaceAfter=6),
    "intro": ParagraphStyle("intro", parent=BASE, fontName="Helvetica-Oblique", textColor=INK_3, spaceAfter=10),
    "q": ParagraphStyle("q", parent=BASE, fontName="Helvetica-Bold", fontSize=11.2, leading=15,
                        textColor=INK, spaceBefore=10, spaceAfter=2),
    "meta": ParagraphStyle("meta", parent=BASE, fontSize=8, leading=11, textColor=INK_3, spaceAfter=5),
    "body": ParagraphStyle("body", parent=BASE, spaceAfter=5),
    "label": ParagraphStyle("label", parent=BASE, fontName="Helvetica-Bold", fontSize=8.6, textColor=ACCENT,
                            spaceBefore=3),
    "small": ParagraphStyle("small", parent=BASE, fontSize=8.2, leading=11.4, textColor=INK_3, spaceAfter=4),
    "toc": ParagraphStyle("toc", parent=BASE, fontSize=10.4, leading=17),
}


def inline(text: str) -> str:
    """Markdown inline syntax -> reportlab's mini-HTML, escaping first."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    return text


def blocks(markdown: str, style: ParagraphStyle) -> list:
    """Paragraphs and bullet lists from a Markdown answer."""
    out, bullets = [], []

    def flush():
        if bullets:
            out.append(ListFlowable([ListItem(Paragraph(inline(b), style), leftIndent=10) for b in bullets],
                                    bulletType="bullet", start="•", leftIndent=12, bulletFontSize=7))
            bullets.clear()

    for para in re.split(r"\n\s*\n", markdown.strip()):
        lines = [ln.rstrip() for ln in para.splitlines() if ln.strip()]
        if lines and all(re.match(r"^\s*[-*]\s+", ln) or ln.startswith("  ") for ln in lines):
            item = ""
            for ln in lines:
                if re.match(r"^\s*[-*]\s+", ln):
                    if item:
                        bullets.append(item)
                    item = re.sub(r"^\s*[-*]\s+", "", ln)
                else:
                    item += " " + ln.strip()
            bullets.append(item)
            continue
        flush()
        out.append(Paragraph(inline(" ".join(ln.strip() for ln in lines)), style))
    flush()
    return out


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.8)
    canvas.setFillColor(INK_3)
    canvas.drawString(18 * mm, 10 * mm, f"{PROFILE['name']} — Interview Q&A")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build() -> tuple[Path, int, dict]:
    doc = corpus.build()
    stats = doc["stats"]
    by_part: dict[int, list] = {}
    for q in doc["questions"]:
        by_part.setdefault(q["part"], []).append(q)

    story: list = [Spacer(1, 70 * mm),
                   Paragraph("Interview Questions &amp; Answers", S["title"]), Spacer(1, 6 * mm),
                   Paragraph(f"{PROFILE['name']} — {PROFILE['role']}", S["subtitle"]), Spacer(1, 3 * mm),
                   Paragraph(f"{stats['questions']} questions across {stats['parts']} parts · "
                             f"{stats['words']:,} words · {date.today():%B %Y}", S["subtitle"]),
                   Spacer(1, 30 * mm),
                   Paragraph("The questions recruiters, hiring managers and engineers ask about his record, "
                             "with the answers his portfolio assistant gives. Every answer lists the facts it "
                             f"rests on. Live and searchable at {PROFILE['site'].replace('https://', '')}.",
                             ParagraphStyle("c", parent=S["small"], alignment=TA_CENTER)),
                   PageBreak(),
                   Paragraph("Contents", S["part"]), Spacer(1, 3 * mm)]
    for p in doc["parts"]:
        story.append(Paragraph(f"<b>Part {p['part']}</b> — {inline(p['topic'])} "
                               f"<font color='#6b7280'>({p['count']} questions)</font>", S["toc"]))
    story.append(PageBreak())

    for p in doc["parts"]:
        story.append(Paragraph(f"Part {p['part']} — {inline(p['topic'])}", S["part"]))
        if p["intro"]:
            story.append(Paragraph(inline(p["intro"]), S["intro"]))
        for q in by_part[p["part"]]:
            head = [Paragraph(f"Q{q['id'].split('-', 1)[1].replace('-', '.')} — {inline(q['question'])}", S["q"]),
                    Paragraph(f"{q['difficulty']} · asked by {', '.join(q['asked_by'])} · "
                              f"{', '.join(q['tags'])}", S["meta"])]
            body = blocks(q["answer"], S["body"])
            story.append(KeepTogether(head + body[:1]))
            story.extend(body[1:])
            story.append(Paragraph("Follow-up", S["label"]))
            story.extend(blocks(q["follow_up"], S["body"]))
            story.append(Paragraph(f"<b>Grounded in:</b> {inline(', '.join(q['grounded_in']))}", S["small"]))
        story.append(PageBreak())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                          topMargin=16 * mm, bottomMargin=18 * mm,
                          title=f"{PROFILE['name']} - Interview Q&A", author=PROFILE["name"])
    frame = Frame(pdf.leftMargin, pdf.bottomMargin, pdf.width, pdf.height, id="f")
    pdf.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=_footer)])
    pdf.build(story)
    return OUT, pdf.page, stats


if __name__ == "__main__":
    path, pages, stats = build()
    print(f"wrote {path.relative_to(ROOT)}: {pages} pages, {stats['questions']} questions, "
          f"{path.stat().st_size / 1024:.0f} KB")
    sys.exit(0)
