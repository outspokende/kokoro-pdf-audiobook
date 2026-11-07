"""Standalone adaptation of KokoroBooks PDF extraction and TTS preparation."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

import pymupdf as fitz


def _clean(text: str) -> str:
    replacements = {
        "“": '"', "”": '"', "„": '"', "‘": "'", "’": "'",
        "–": "-", "−": "-", "—": ", ", "…": "...", "\u00a0": " ",
        "\u00ad": "", "\ufeff": "", "•": " ", "ﬁ": "fi", "ﬂ": "fl",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if c in "\n\t" or unicodedata.category(c)[0] != "C")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"(?<![.!?:\n])\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return re.sub(r"\n{2,}", "\n\n", text).strip()


def _normal_heading(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"\s*[-‐‑‒–—]\s*", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def _toc_chapters(page_texts: list[str]) -> tuple[list[str], int | None]:
    """Infer chapter headings from a printed contents page in OCR text."""
    contents_pages = [i for i, text in enumerate(page_texts[:50])
                      if re.search(r"\b(?:contents|table of contents)\b", text, re.I)]
    if not contents_pages:
        return [], None

    titles: list[str] = []
    for page_index in contents_pages:
        lines = page_texts[page_index].splitlines()
        for i, line in enumerate(lines):
            match = re.match(r"^\s*(?:[ivxlcdm]{1,8}|\d{1,3})[.)]\s+(.+?)\s*$", line, re.I)
            if not match:
                continue
            title = match.group(1).strip(" .\t")
            if len(re.sub(r"[^a-z]", "", title.casefold())) < 5:
                continue
            # A few scanned contents lines wrap before their printed page number.
            if i + 1 < len(lines) and re.match(r"^\s*[A-Z][A-Za-z -]{2,45}\s*$", lines[i + 1]):
                title = f"{title} {lines[i + 1].strip()}"
            key = _normal_heading(title)
            if key and key not in {_normal_heading(x) for x in titles}:
                titles.append(title)
    return titles, max(contents_pages)


def prepare_pdf(path: str, skip_front_matter: bool = False) -> dict:
    """Extract PDF text, suppress repeated edge furniture, retain TOC chapters."""
    doc = fitz.open(path)
    try:
        pages: list[list[tuple[str, str | None, tuple[str, str] | None, float, float]]] = []
        counts: Counter[tuple[str, str]] = Counter()
        totals = Counter()
        for i, page in enumerate(doc):
            parity = str(i % 2)
            totals[parity] += 1
            records = []
            h = page.rect.height or 1
            for block in page.get_text("blocks", sort=True):
                text = str(block[4]).strip()
                if not text:
                    continue
                y0, y1 = float(block[1]), float(block[3])
                edge = "header" if y0 / h <= .09 else "footer" if y1 / h >= .91 else None
                norm = re.sub(r"\d+", "#", re.sub(r"\s+", " ", text.casefold())).strip()
                key = (parity, norm) if edge and len(norm) > 4 else None
                records.append((text, edge, key, y0, y1))
                if key:
                    counts[key] += 1
            pages.append(records)
        repeated = {k for k, n in counts.items() if n >= max(3, int(totals[k[0]] * .3))}
        page_texts = []
        page_lines = []
        for records in pages:
            kept_blocks = []
            kept_page_lines = []
            previous_y1 = None
            for text, edge, key, y0, y1 in records:
                if edge and key in repeated:
                    continue
                if edge and re.fullmatch(r"\s*(?:page\s+)?[0-9ivxlcdm]+\s*", text, re.I):
                    continue
                if re.fullmatch(r"\s*[0-9]{1,4}\s*", text):
                    continue
                # Keep OCR reading order but restore paragraph breaks only for
                # a visible vertical gap, not between every scanned text block.
                if kept_blocks and previous_y1 is not None and y0 - previous_y1 > 24:
                    kept_blocks.append("\n\n")
                elif kept_blocks:
                    kept_blocks.append("\n")
                kept_blocks.append(text)
                kept_page_lines.extend(line.strip() for line in text.splitlines() if line.strip())
                previous_y1 = y1
            page_texts.append("".join(kept_blocks))
            page_lines.append(kept_page_lines)
        toc = doc.get_toc(simple=True) or []
    finally:
        doc.close()

    # TOC pages are 1-based. Keep top-level entries, or children when the TOC
    # has only a single root heading.
    entries = [(int(level), str(title).strip(), int(page)) for level, title, page, *_ in toc
               if str(title).strip() and 1 <= int(page) <= len(page_texts)]
    chapter_starts = []
    if entries:
        level = min(x[0] for x in entries)
        top = [x for x in entries if x[0] == level]
        if len(top) < 2:
            top = [x for x in entries if x[0] > level] or entries
        chapter_starts = sorted({(page - 1, title) for _, title, page in top})
    else:
        inferred_titles, contents_end = _toc_chapters(page_texts)
        if inferred_titles and contents_end is not None:
            previous = contents_end
            for title in inferred_titles:
                target = _normal_heading(title)
                found = None
                for page_index in range(previous + 1, len(page_lines)):
                    if any(_normal_heading(line) == target for line in page_lines[page_index]):
                        found = page_index
                        break
                if found is not None:
                    chapter_starts.append((found, title))
                    previous = found

    if chapter_starts:
        sections = []
        front_titles = {"title page", "cover", "copyright", "dedication", "contents",
                        "table of contents", "acknowledgments", "acknowledgements",
                        "dramatis personae", "newsletter", "map", "maps"}
        if skip_front_matter:
            narrative = [(start, title) for start, title in chapter_starts
                         if title.casefold().strip() not in front_titles]
            if narrative:
                chapter_starts = narrative
        if not skip_front_matter and chapter_starts[0][0] > 0:
            front = "\n".join(page_texts[:chapter_starts[0][0]])
            if front.strip():
                sections.append(("Front matter", front))
        for i, (start, title) in enumerate(chapter_starts):
            end = chapter_starts[i + 1][0] if i + 1 < len(chapter_starts) else len(page_texts)
            body = "\n".join(page_texts[start:end])
            if body.strip():
                sections.append((title, body))
    else:
        start = 0
        if skip_front_matter:
            for i, body in enumerate(page_texts[:min(30, len(page_texts))]):
                if re.search(r"(?im)^\s*(?:prologue|chapter\s+(?:1|one|i))\b", body):
                    start = i
                    break
        sections = [("Full text", "\n".join(page_texts[start:]))]

    prepared = []
    for section_index, (title, body) in enumerate(sections):
        cleaned = _clean(body)
        if section_index == len(sections) - 1:
            end_marker = re.search(r"(?im)^\s*THE END\s*[.!]?\s*$", cleaned)
            if end_marker and len(cleaned) - end_marker.end() < 1200:
                cleaned = cleaned[:end_marker.end()].strip()
        if not cleaned:
            continue
        first_line = cleaned.splitlines()[0].strip().casefold() if cleaned.splitlines() else ""
        if title.casefold().strip() not in first_line and title.casefold() != "full text":
            cleaned = f"{title}.\n\n{cleaned}"
        paras = [p.strip().replace("\n", " ") for p in cleaned.split("\n\n") if p.strip()]
        for para in paras:
            sentences = re.split(r'(?<=[.!?])["\')\]]*\s+', para)
            current = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if current and len(current) + len(sentence) + 1 > 380:
                    prepared.append((current, False))
                    current = ""
                if len(sentence) > 380:
                    while len(sentence) > 380:
                        cut = max(sentence.rfind(" ", 0, 360), sentence.rfind(",", 0, 360))
                        cut = cut if cut > 0 else 360
                        prepared.append((sentence[:cut].strip(), False))
                        sentence = sentence[cut:].strip()
                    if sentence:
                        current = sentence
                else:
                    current = f"{current} {sentence}".strip()
            if current:
                prepared.append((current, True))
    if not prepared:
        raise ValueError("No selectable text found. This may be a scanned PDF; run OCR first.")
    return {"chunks": prepared, "chapters": [title for title, _ in sections],
            "text": "\n\n".join(text for text, _ in prepared),
            "page_count": len(page_texts)}
