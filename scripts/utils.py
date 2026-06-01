from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ID = "2025_06_set1"
PAPER_PAGE_URL = "https://www.wehuster.com/cet6/cet6_2025_06_1"
ANSWER_PAGE_URL = "https://www.wehuster.com/cet6/cet6_2025_06_1_ans"
PAPER_PDF_NAME = "cet6_2025_06_1.pdf"
ANSWER_PDF_NAME = "cet6_2025_06_1_ans.pdf"


def ensure_sample_only(exam_id: str = SAMPLE_ID) -> None:
    if exam_id != SAMPLE_ID:
        raise ValueError(f"Milestone 1 only permits {SAMPLE_ID}, got {exam_id}")


def path_from_root(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def ensure_dirs() -> None:
    for rel in [
        "data/raw_pdfs",
        "data/extracted_text",
        "data/structured",
        "reports",
        "schemas",
        "scripts",
    ]:
        path_from_root(rel).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_error(step: str, file_name: str, error_type: str, message: str, affects_output: bool = True) -> None:
    ensure_dirs()
    log_path = path_from_root("reports", "parsing_errors.log")
    timestamp = datetime.now(timezone.utc).isoformat()
    line = (
        f"{timestamp}\tstep={step}\tfile={file_name}\ttype={error_type}"
        f"\taffects_output={affects_output}\tmessage={message}\n"
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_space(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[ \t\r\f\v]+", " ", value)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    return cleaned or None


def split_options(block: str) -> dict[str, str]:
    options: dict[str, str] = {}
    marker_pattern = re.compile(r"(?<![A-Za-z0-9])([A-D])\)\s*")
    markers: list[re.Match[str]] = []
    seen_letters: set[str] = set()
    for match in marker_pattern.finditer(block):
        letter = match.group(1)
        if letter in seen_letters:
            continue
        markers.append(match)
        seen_letters.add(letter)
        if seen_letters == {"A", "B", "C", "D"}:
            break
    boundary_pattern = re.compile(
        r"(?m)^\s*(?:"
        r"\d{1,2}\.\s*|"
        r"Questions\s+\d+\s+to\s+\d+\s+are based on\b.*|"
        r"Section\s+[A-C]\b.*|"
        r"Passage\s+(?:One|Two)\b.*|"
        r"Part\s+[IVX]+\b.*|"
        r"Directions:\s*.*|"
        r"KEYS\b.*|"
        r"===== PAGE \d+ ====="
        r")"
    )
    for index, match in enumerate(markers):
        letter = match.group(1)
        end = markers[index + 1].start() if index + 1 < len(markers) else len(block)
        if index + 1 >= len(markers):
            boundary_match = boundary_pattern.search(block, match.end())
            if boundary_match:
                end = min(end, boundary_match.start())
        text = normalize_space(block[match.end():end].replace("\n", " "))
        if text:
            options[letter] = text
    return options


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
