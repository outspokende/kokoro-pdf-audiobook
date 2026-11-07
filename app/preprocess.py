"""Standalone adaptation of KokoroBooks PDF extraction and TTS preparation."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

import fitz


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


def prepare_pdf(path: str, skip_front_matter: bool = False) -> dict:
    """Extract PDF text, suppress repeated edge furniture, retain TOC chapters."""
    doc = fitz.open(path)
    try:
        pages: list[list[tuple[str, str | None]]] = []
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
                edge = "header" if block[3] / h <= .09 else "footer" if block[1] / h >= .91 else None
                norm = re.sub(r"\d+", "#", re.sub(r"\s+", " ", text.casefold())).strip()
                key = (parity, norm) if edge and len(norm) > 4 else None
                records.append((text, edge, key))
                if key:
                    counts[key] += 1
            pages.append(records)
        repeated = {k for k, n in counts.items() if n >= max(3, int(totals[k[0]] * .3))}
        page_texts = []
        for records in pages:
            kept = []
            for text, edge, key in records:
                if edge and key in repeated:
                    continue
                if edge and re.fullmatch(r"\s*(?:page\s+)?[0-9ivxlcdm]+\s*", text, re.I):
                    continue
                kept.append(text)
            page_texts.append("\n".join(kept))
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
    for title, body in sections:
        cleaned = _clean(body)
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
