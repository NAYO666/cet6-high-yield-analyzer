from __future__ import annotations

import re
from typing import Any

from utils import ensure_dirs, ensure_sample_only, normalize_space, path_from_root, read_text, write_json


QUESTION_PUNCT = r"[\.\uff0e,\uff0c\u3002]"
ITEM = "\u9879"
MATCHES = "\u76f8\u7b26"
CORRECT = "\u6b63\u786e"
SELECT = "\u9009"
LOCATE = "\u5b9a\u4f4d\u5230"
PARA = "\u6bb5"
ANSWER_DETAIL = "\u7b54\u6848\u8be6\u89e3"
REFERENCE_TRANSLATION = "\u53c2\u8003\u8bd1\u6587"
TRANSLATION_ANALYSIS = "\u8bd1\u70b9\u7cbe\u6790"


def dense_text(text: str) -> str:
    return re.sub(r"\s+", "", text)


def between(text: str, start: str, end: str | None) -> str:
    start_index = text.find(start)
    if start_index < 0:
        return ""
    end_index = text.find(end, start_index) if end else -1
    if end_index < 0:
        end_index = len(text)
    return text[start_index:end_index]


def parse_highlighted_vocabulary(text: str) -> list[dict[str, str | None]]:
    block = between(text, "\u4eae\u70b9\u8bcd\u6c47", "\u5199\u4f5c\u53e5\u578b")
    pairs = [
        ("proactive", "\u79ef\u6781\u4e3b\u52a8\u7684"),
        ("strive", "\u52aa\u529b"),
        ("hands-on", "\u4eb2\u81ea\u52a8\u624b\u5b9e\u8df5\u7684"),
        ("matter a lot", "\u975e\u5e38\u91cd\u8981"),
        ("indispensable", "\u5fc5\u4e0d\u53ef\u5c11\u7684"),
        ("sought-after", "\u5907\u53d7\u8ffd\u6367\u7684"),
    ]
    return [{"word": word, "meaning_zh": meaning, "context": None} for word, meaning in pairs if word in block]


def parse_writing_patterns(text: str) -> list[dict[str, str | None]]:
    block = between(text, "\u5199\u4f5c\u53e5\u578b", "P art II")
    patterns = []
    if "It is indispensable to" in block:
        patterns.append({
            "pattern": "It is indispensable to...",
            "meaning_zh": "\u2026\u2026\u662f\u5fc5\u4e0d\u53ef\u5c11\u7684",
            "usage_zh": "\u7528\u4e8e\u5f3a\u8c03\u67d0\u79cd\u505a\u6cd5\u7684\u91cd\u8981\u6027",
        })
    if "By doing" in block:
        patterns.append({
            "pattern": "By doing..., they can...",
            "meaning_zh": "\u901a\u8fc7\u505a\u2026\u2026\uff0c\u4ed6\u4eec\u53ef\u4ee5\u2026\u2026",
            "usage_zh": "\u7528\u4e8e\u8bf4\u660e\u901a\u8fc7\u67d0\u79cd\u505a\u6cd5\u53ef\u4ee5\u83b7\u5f97\u7ed3\u679c",
        })
    return patterns


def parse_reference_essay(text: str) -> str | None:
    block = between(text, "\u53c2\u8003\u8303\u6587", "\u8303\u6587\u8bd1\u6587")
    lines = [line for line in block.splitlines() if re.search(r"[A-Za-z]", line)]
    return normalize_space("\n".join(lines))


def parse_essay_translation(text: str) -> str | None:
    block = between(text, "\u8303\u6587\u8bd1\u6587", "\u8001\u5e08\u8bf4")
    lines = [line for line in block.splitlines() if re.search(r"[\u4e00-\u9fff]", line)]
    return normalize_space("\n".join(lines))


def find_markers(dense: str, q_num: int) -> list[int]:
    markers: list[int] = []
    for match in re.finditer(rf"(?<!\d){q_num}{QUESTION_PUNCT}", dense):
        markers.append(match.start())
    if q_num == 1:
        for match in re.finditer(r"(?<!\d)[lI]" + QUESTION_PUNCT + r"Whatdidthewomando", dense):
            markers.append(match.start())
    if q_num == 11:
        for match in re.finditer(r"(?<!\d)II" + QUESTION_PUNCT + r"Whatdoesevidence", dense):
            markers.append(match.start())
    return sorted(set(markers))


def choose_marker(dense: str, q_num: int, previous: int, section_end: int | None = None) -> int | None:
    cues = [
        "What", "Why", "How", "Where", "Which", "Who",
        "\u7537\u58eb", "\u5973\u58eb", "\u7814\u7a76", "\u4f5c\u8005", "\u7f8e\u56fd", "\u516c\u5171\u56fe\u4e66\u9986",
        "\u8fd1\u5341\u5e74", "\u5bf9\u4e8e", "\u5c06", "\u5f53",
    ]
    candidates = []
    for marker in find_markers(dense, q_num):
        if marker <= previous:
            continue
        if section_end is not None and marker >= section_end:
            continue
        window = dense[marker:marker + 180]
        if any(cue in window for cue in cues):
            candidates.append(marker)
    return candidates[0] if candidates else None


def question_blocks(dense: str, start_q: int, end_q: int, start_at: int = 0, section_end: int | None = None) -> dict[int, str]:
    starts: dict[int, int] = {}
    previous = start_at
    for q_num in range(start_q, end_q + 1):
        marker = choose_marker(dense, q_num, previous, section_end)
        if marker is not None:
            starts[q_num] = marker
            previous = marker
    result: dict[int, str] = {}
    ordered = sorted(starts.items())
    for index, (q_num, start) in enumerate(ordered):
        end = ordered[index + 1][1] if index + 1 < len(ordered) else (section_end or min(len(dense), start + 1800))
        result[q_num] = dense[start:end]
    return result


def normalize_letter(value: str, allowed: str) -> str | None:
    letter = value.upper()
    if letter == "0" and set(allowed) <= set("ABCD"):
        letter = "C"
    elif letter == "0" and "O" in allowed:
        letter = "O"
    if letter == "1" and "I" in allowed:
        letter = "I"
    return letter if letter in allowed else None


def answer_from_block(block: str, allowed: str) -> str | None:
    patterns = [
        rf"([A-O01]){ITEM}.{{0,45}}(?:{MATCHES}|{CORRECT})",
        rf"{SELECT}{ITEM}([A-O01]).{{0,8}}{CORRECT}",
        rf"([A-O01])\){ITEM}.{{0,45}}(?:{MATCHES}|{CORRECT})",
        rf"{LOCATE}([A-O01]){PARA}",
        rf"(?:\u6545|\u5e94|{CORRECT}\u7b54\u6848).{{0,8}}{SELECT}([A-O01])",
        rf"\u672c\u9898\u5e94{SELECT}([A-O01])",
    ]
    for pattern in patterns:
        match = re.search(pattern, block)
        if not match:
            continue
        for group in reversed(match.groups()):
            if group:
                return normalize_letter(group, allowed)
    return None


def parse_key_sentences(dense: str) -> dict[int, str]:
    sentences: dict[int, str] = {}
    for match in re.finditer(r"[\[\u3010\u535c]\s*(\d{1,2})\s*[\]\u3011]([^\[\u3010\u535c]{20,260})", dense):
        q_num = int(match.group(1))
        if not 1 <= q_num <= 25 or q_num in sentences:
            continue
        sentence = re.split(r"(?=M:|W:|0\u00b7|0\u8def|" + ANSWER_DETAIL + r"|[A-D0]\))", match.group(2))[0]
        if re.search(r"[A-Za-z]", sentence):
            sentences[q_num] = normalize_space(sentence) or sentence
    return sentences


def parse_listening_answers(dense: str) -> dict[int, dict[str, Any]]:
    section_end = dense.find("PartIII")
    if section_end < 0:
        section_end = dense.find("ReadingComprehension")
    blocks = question_blocks(dense, 1, 25, 0, section_end if section_end > 0 else None)
    key_sentences = parse_key_sentences(dense[:section_end] if section_end > 0 else dense)
    result: dict[int, dict[str, Any]] = {}
    for q_num, block in blocks.items():
        answer = answer_from_block(block, "ABCD")
        if not answer:
            continue
        result[q_num] = {
            "correct_answer_from_explanation": answer,
            "key_sentence": key_sentences.get(q_num),
            "source_marker": f"[{q_num}]" if q_num in key_sentences else None,
            "explanation": normalize_space(block),
        }
    return result


def parse_reading_answers(dense: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    # Section A headings usually carry the answer directly, e.g. 26. J) intrigued.
    for q_num in range(26, 36):
        for marker in find_markers(dense, q_num):
            block = dense[marker:marker + 1000]
            direct = re.match(rf"{q_num}{QUESTION_PUNCT}([A-O01])\)", block)
            answer = normalize_letter(direct.group(1), "ABCDEFGHIJKLMNO") if direct else None
            if answer:
                result[q_num] = {"correct_answer_from_explanation": answer, "explanation": normalize_space(block)}
                break

    reading_start = dense.find("PartIII")
    blocks = question_blocks(dense, 36, 55, reading_start if reading_start > 0 else 0, None)
    for q_num, block in blocks.items():
        if q_num <= 45:
            early = re.search(r"([A-O01])(?:[A-Za-z0])?\u7531.{0,8}(?:\u9898|\u5e72)", block[:220])
            locate = re.search(rf"{LOCATE}([A-O01]){PARA}", block)
            answer = normalize_letter(early.group(1), "ABCDEFGHIJKLMNO") if early else None
            if answer is None and locate:
                answer = normalize_letter(locate.group(1), "ABCDEFGHIJKLMNO")
        else:
            answer = answer_from_block(block, "ABCD")
        if answer:
            result[q_num] = {"correct_answer_from_explanation": answer, "explanation": normalize_space(block)}
    return result


def parse_translation_reference(text: str) -> str | None:
    compact = re.sub(r"[ \t\r\f\v]+", " ", text)
    start = compact.find("The Tiangong Space Station")
    if start < 0:
        return None
    end_candidates = [
        compact.find(TRANSLATION_ANALYSIS, start),
        compact.find("0 \u00b7 " + TRANSLATION_ANALYSIS, start),
        compact.find("\n===== PAGE 20", start),
    ]
    end_candidates = [item for item in end_candidates if item > start]
    end = min(end_candidates) if end_candidates else start + 1400
    return normalize_space(compact[start:end])


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    text = read_text(path_from_root("data", "extracted_text", "2025_06_set1_answer.txt"))
    dense = dense_text(text)
    parsed = {
        "writing": {
            "reference_essay": parse_reference_essay(text),
            "essay_translation_zh": parse_essay_translation(text),
            "highlighted_vocabulary": parse_highlighted_vocabulary(text),
            "writing_patterns": parse_writing_patterns(text),
        },
        "listening_answers": parse_listening_answers(dense),
        "reading_answers": parse_reading_answers(dense),
        "translation": {
            "reference_en": parse_translation_reference(text),
            "difficult_terms": [],
            "sentence_analyses": [],
        },
        "extraction_note": (
            "Answer PDF pages 3-20 are image-only pages and were parsed from Windows OCR output. "
            "Fields are populated only when an answer marker or reference translation was explicit in the extracted text."
        ),
    }
    write_json(path_from_root("data", "structured", "2025_06_set1_answer_parsed.json"), parsed)
    print("parsed=data/structured/2025_06_set1_answer_parsed.json")


if __name__ == "__main__":
    main()
