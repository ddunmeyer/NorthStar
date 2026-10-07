"""Build docs/North_Star_AAR.pdf from docs/AAR.md.

    pip install reportlab
    python scripts/build_aar_pdf.py

The report is written in Markdown so it reads well on GitHub; this lays the same
text out as a PDF in the North Star palette, with a cover page. It handles the
Markdown the report uses: headings, paragraphs, lists, tables, images, bold,
italic and inline code.
"""
from __future__ import annotations

import re
import tempfile
from html import escape
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, ListFlowable, ListItem, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SOURCE, OUTPUT = DOCS / "AAR.md", DOCS / "North_Star_AAR.pdf"
COVER_ART = DOCS / "screenshots" / "desktop-00-entry-screen.png"

MIDNIGHT, PANEL, OCEAN = colors.HexColor("#0C1626"), colors.HexColor("#15243A"), colors.HexColor("#2F6C8A")
AURORA, SILVER, ICE = colors.HexColor("#9DE5F4"), colors.HexColor("#B6CFEB"), colors.HexColor("#F3F7FC")
INK, MUTED, RULE = colors.HexColor("#1B2738"), colors.HexColor("#5B6B80"), colors.HexColor("#D5E0EE")

PAGE_W, PAGE_H = letter
MARGIN = 0.9 * inch
TEXT_W = PAGE_W - 2 * MARGIN
SCRATCH = Path(tempfile.mkdtemp(prefix="northstar-aar-"))  # resized working copies of images

BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=15.5, textColor=INK, spaceAfter=8)
STYLES = {
    "body": BODY,
    "h2": ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=MIDNIGHT,
                         spaceBefore=20, spaceAfter=9),
    "h3": ParagraphStyle("h3", parent=BODY, fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=OCEAN,
                         spaceBefore=12, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", parent=BODY, spaceAfter=4),
    "cell": ParagraphStyle("cell", parent=BODY, fontSize=9.2, leading=12.5, spaceAfter=0),
    "head": ParagraphStyle("head", parent=BODY, fontName="Helvetica-Bold", fontSize=9.2, leading=12.5, spaceAfter=0,
                           textColor=colors.white),
    "caption": ParagraphStyle("caption", parent=BODY, fontName="Helvetica-Oblique", fontSize=8.8, leading=12,
                              textColor=MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12),
}

STAR = [(0, 1), (0.16, 0.16), (1, 0), (0.16, -0.16), (0, -1), (-0.16, -0.16), (-1, 0), (-0.16, 0.16)]


def inline(text: str) -> str:
    """Markdown emphasis and code to ReportLab's paragraph markup."""
    text = escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9.4" color="#2F6C8A">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<i>\1</i>", text)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def star(canvas, x: float, y: float, size: float, fill) -> None:
    path = canvas.beginPath()
    path.moveTo(x + STAR[0][0] * size, y + STAR[0][1] * size)
    for px, py in STAR[1:]:
        path.lineTo(x + px * size, y + py * size)
    path.close()
    canvas.setFillColor(fill)
    canvas.drawPath(path, stroke=0, fill=1)


# --------------------------------------------------------------------------- page furniture
def cover_art() -> Path | None:
    """The aurora band from the entry-screen screenshot, cropped clear of the browser bar and the heading."""
    if not COVER_ART.exists():
        return None
    out = SCRATCH / "cover_band.jpg"
    image = PILImage.open(COVER_ART).convert("RGB")
    width, height = image.size
    band = image.crop((int(width * 0.16), int(height * 0.047), width, int(height * 0.378)))
    # Blend the lower third into the page colour so the picture has no hard bottom edge.
    fade = PILImage.linear_gradient("L").resize(band.size)
    start = int(band.height * 0.66)
    mask = PILImage.new("L", band.size, 0)
    mask.paste(fade.resize((band.width, band.height - start)), (0, start))
    band = PILImage.composite(PILImage.new("RGB", band.size, (12, 22, 38)), band, mask)
    band.save(out, quality=93)
    return out


def draw_cover(meta: dict):
    art = cover_art()

    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(MIDNIGHT)
        canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        top = PAGE_H
        if art:
            band_w, band_h = PILImage.open(art).size
            height = PAGE_W * band_h / band_w
            canvas.drawImage(str(art), 0, PAGE_H - height, width=PAGE_W, height=height)
            top = PAGE_H - height

        x = MARGIN
        y = top - 1.05 * inch
        canvas.setStrokeColor(colors.HexColor("#3A5677"))
        canvas.setFillColor(PANEL)
        canvas.roundRect(x, y - 8, 46, 46, 9, stroke=1, fill=1)
        star(canvas, x + 23, y + 15, 15, AURORA)
        star(canvas, x + 23, y + 15, 6, colors.white)
        canvas.setFillColor(ICE)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawString(x + 62, y + 16, "N O R T H   S T A R")
        canvas.setFillColor(SILVER)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(x + 62, y - 1, "Your workday. On course.")

        y -= 1.5 * inch
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 40)
        canvas.drawString(x, y, "After Action Report")
        canvas.setStrokeColor(AURORA)
        canvas.setLineWidth(2.2)
        canvas.line(x, y - 20, x + 1.1 * inch, y - 20)
        canvas.setFillColor(SILVER)
        canvas.setFont("Helvetica", 14)
        canvas.drawString(x, y - 50, "An employee assistant built with AI agents on AWS")

        y -= 1.55 * inch
        for label, value in meta.items():
            canvas.setFillColor(AURORA)
            canvas.setFont("Helvetica-Bold", 8.5)
            canvas.drawString(x, y, label.upper())
            canvas.setFillColor(ICE)
            canvas.setFont("Helvetica", 12.5)
            canvas.drawString(x + 1.55 * inch, y - 1, value)
            y -= 0.34 * inch

        canvas.setFillColor(colors.HexColor("#7F96B5"))
        canvas.setFont("Helvetica", 9)
        canvas.drawString(x, 0.7 * inch, "All employee records, policies and requests in North Star are fictional.")
        canvas.restoreState()

    return draw


def draw_page(canvas, doc):
    canvas.saveState()
    star(canvas, MARGIN + 5, PAGE_H - 0.55 * inch + 3, 5.5, OCEAN)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(MARGIN + 16, PAGE_H - 0.55 * inch, "NORTH STAR")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN + 76, PAGE_H - 0.55 * inch, "After Action Report")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, PAGE_H - 0.66 * inch, PAGE_W - MARGIN, PAGE_H - 0.66 * inch)
    canvas.line(MARGIN, 0.68 * inch, PAGE_W - MARGIN, 0.68 * inch)
    canvas.drawString(MARGIN, 0.5 * inch, "Agentic AI, IT Expert System")
    canvas.drawRightString(PAGE_W - MARGIN, 0.5 * inch, f"Page {doc.page - 1}")
    canvas.restoreState()


# --------------------------------------------------------------------------- Markdown to flowables
def table(rows: list[list[str]]) -> Table:
    header, body = rows[0], rows[1:]
    columns = len(header)
    # Share the width by how much each column has to hold, within sensible limits.
    weights = []
    for c in range(columns):
        longest = max(len(r[c]) for r in rows if c < len(r))
        weights.append(min(max(longest, 9), 62))
    widths = [TEXT_W * w / sum(weights) for w in weights]
    needed = [stringWidth(cell, "Helvetica-Bold", 9.2) + 16 for cell in header]
    short = sum(max(0, n - w) for n, w in zip(needed, widths))
    spare = sum(max(0, w - n) for n, w in zip(needed, widths))
    if short and spare:
        widths = [n if w < n else w - (w - n) * short / spare for n, w in zip(needed, widths)]
    data = [[Paragraph(inline(cell), STYLES["head"]) for cell in header]]
    data += [[Paragraph(inline(cell), STYLES["cell"]) for cell in row + [""] * (columns - len(row))] for row in body]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), MIDNIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, RULE),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
    ]
    style += [("BACKGROUND", (0, r), (-1, r), ICE) for r in range(2, len(data), 2)]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle(style))
    return result


def trimmed(path: Path) -> Path:
    """Crop away rows at the bottom of a screenshot that hold nothing but background."""
    image = PILImage.open(path).convert("RGB")
    small = image.convert("L").resize((64, image.height))
    rows = (small.crop((0, y, 64, y + 1)).getextrema() for y in range(small.height))
    busy = [y for y, (darkest, lightest) in enumerate(rows) if lightest - darkest > 14]
    last = min(image.height, (busy[-1] if busy else image.height) + int(image.height * 0.04))
    if last > image.height * 0.93:
        return path
    out = SCRATCH / f"{path.stem}.png"
    image.crop((0, 0, image.width, last)).save(out)
    return out


def picture(path: Path, caption: str) -> KeepTogether:
    path = trimmed(path)
    width, height = PILImage.open(path).size
    shown_w = TEXT_W
    shown_h = shown_w * height / width
    frame = Table([[Image(str(path), width=shown_w - 2, height=shown_h - 2 * height / width)]], colWidths=[shown_w])
    frame.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, RULE), ("LEFTPADDING", (0, 0), (-1, -1), 1),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return KeepTogether([Spacer(1, 4), frame, Paragraph(inline(caption), STYLES["caption"])])


def parse(markdown: str):
    """Return (cover metadata, flowables)."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    meta, story, i = {}, [], 0
    while i < len(lines) and not lines[i].startswith("## "):  # the title block goes on the cover
        found = re.match(r"\*\*(.+?):\*\*\s*(.+)", lines[i])
        if found:
            meta[found.group(1)] = found.group(2)
        i += 1

    paragraph: list[str] = []

    def flush():
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph)), STYLES["body"]))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            flush()
            heading = Paragraph(inline(line[3:]), STYLES["h2"])
            rule = Table([[""]], colWidths=[TEXT_W], rowHeights=[2])
            rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.6, OCEAN)]))
            story.append(KeepTogether([Spacer(1, 6), rule, heading]))
        elif line.startswith("### "):
            flush()
            story.append(Paragraph(inline(line[4:]), STYLES["h3"]))
        elif line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            story += [Spacer(1, 2), table(rows), Spacer(1, 12)]
            continue
        elif re.match(r"(-|\d+\.)\s+", line):
            flush()
            numbered = line[0].isdigit()
            items = []
            while i < len(lines) and re.match(r"(-|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^(-|\d+\.)\s+", "", lines[i]))
                i += 1
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(item), STYLES["bullet"]), leftIndent=18) for item in items],
                bulletType="1" if numbered else "bullet", bulletFontName="Helvetica-Bold" if numbered else "Helvetica",
                bulletFontSize=10 if numbered else 7, bulletColor=OCEAN, bulletOffsetY=0 if numbered else -2,
                leftIndent=18, start=None if numbered else "circle"))
            story.append(Spacer(1, 6))
            continue
        elif line.startswith("!["):
            flush()
            found = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            image_path = DOCS / found.group(2)
            if image_path.exists():
                story.append(picture(image_path, found.group(1)))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
        i += 1
    flush()
    return meta, story


def main() -> None:
    meta, story = parse(SOURCE.read_text(encoding="utf-8"))
    doc = BaseDocTemplate(str(OUTPUT), pagesize=letter, title="North Star: After Action Report",
                          author="David Dunmeyer and Biswa", subject="Agentic AI class project, IT Expert System",
                          leftMargin=MARGIN, rightMargin=MARGIN, topMargin=0.95 * inch, bottomMargin=0.95 * inch)
    frame = Frame(MARGIN, 0.95 * inch, TEXT_W, PAGE_H - 1.9 * inch, id="body", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=draw_cover(meta)),
                          PageTemplate(id="page", frames=[frame], onPage=draw_page)])
    doc.build([NextPageTemplate("page"), PageBreak()] + story)
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} KB, {doc.page} pages)")


if __name__ == "__main__":
    main()
