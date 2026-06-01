from __future__ import annotations

import re
from typing import Any

from utils import (
    ensure_dirs,
    ensure_sample_only,
    normalize_space,
    path_from_root,
    read_text,
    split_options,
    write_json,
)


def section_between(text: str, start: str, end: str | None) -> str:
    start_index = text.find(start)
    if start_index < 0:
        return ""
    end_index = text.find(end, start_index) if end else -1
    if end_index < 0:
        end_index = len(text)
    return text[start_index:end_index]


POLLUTION_PATTERN = re.compile(
    r"===== PAGE \d+ =====|"
    r"\bSection Directions\b|"
    r"^\s*Directions:\s*.*$|"
    r"^\s*Questions\s+\d+\s+to\s+\d+\s+are based on\b.*$|"
    r"^\s*Section\s+[A-C]\b.*$|"
    r"^\s*Passage\s+(?:One|Two)\b.*$|"
    r"^\s*Part\s+[IVX]+\b.*$",
    re.M,
)


def clean_field(value: str | None) -> str | None:
    if value is None:
        return None
    value = POLLUTION_PATTERN.sub(" ", value)
    return normalize_space(value.replace("\n", " "))


def parse_writing(text: str) -> dict[str, Any]:
    block = section_between(text, "Part I", "Part II")
    directions = None
    prompt = None
    word_count_min = None
    word_count_max = None
    directions_match = re.search(r"Directions:\s*(.*?)(?:Part II|$)", block, re.S)
    if directions_match:
        directions = normalize_space(directions_match.group(1).replace("\n", " "))
    prompt_match = re.search(r"begins with the sentence [“\"](.*?)[”\"]", block, re.S)
    if prompt_match:
        prompt = normalize_space(prompt_match.group(1).replace("\n", " "))
    count_match = re.search(r"at least\s+(\d+)\s+words but no more than\s+(\d+)\s+words", block, re.I)
    if count_match:
        word_count_min = int(count_match.group(1))
        word_count_max = int(count_match.group(2))
    return {
        "directions": directions,
        "prompt": prompt,
        "word_count_min": word_count_min,
        "word_count_max": word_count_max,
    }


def parse_keys(text: str) -> dict[int, str]:
    keys_block = section_between(text, "KEYS", None)
    keys: dict[int, str] = {}
    pattern = re.compile(r"((?:\d+\s+)+)\n([A-O](?:\s+[A-O])*)", re.M)
    for numbers_line, answers_line in pattern.findall(keys_block):
        numbers = [int(n) for n in re.findall(r"\d+", numbers_line)]
        answers = re.findall(r"[A-O]", answers_line)
        for number, answer in zip(numbers, answers):
            keys[number] = answer
    return keys


def parse_question_blocks(text: str, start_q: int, end_q: int) -> list[dict[str, Any]]:
    starts: list[tuple[int, int]] = []
    for match in re.finditer(r"(?m)^\s*(\d{1,2})\.\s*", text):
        q_num = int(match.group(1))
        if start_q <= q_num <= end_q:
            starts.append((q_num, match.start()))
    result: list[dict[str, Any]] = []
    for index, (q_num, start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(text)
        block = text[start:end]
        option_match = re.search(r"(?<![A-Za-z0-9])A\)\s*", block)
        header_match = re.match(r"(?s)\s*\d{1,2}\.\s*(.*?)$", block[:option_match.start()] if option_match else block)
        question = clean_field(header_match.group(1)) if header_match else None
        options = {letter: clean_field(value) for letter, value in split_options(block).items()}
        result.append({"q_num": q_num, "question": question, "options": options})
    return result


def parse_numbered_text_blocks(text: str, start_q: int, end_q: int) -> list[dict[str, Any]]:
    starts: list[tuple[int, int]] = []
    for match in re.finditer(r"(?m)^\s*(\d{1,2})\.\s*", text):
        q_num = int(match.group(1))
        if start_q <= q_num <= end_q:
            starts.append((q_num, match.start()))

    result: list[dict[str, Any]] = []
    for index, (q_num, start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(text)
        block = re.sub(r"(?s)^\s*\d{1,2}\.\s*", "", text[start:end], count=1)
        statement = clean_field(block)
        result.append({"q_num": q_num, "statement": statement})
    return result


def parse_listening(text: str, keys: dict[int, str]) -> dict[str, Any]:
    block = section_between(text, "Part II", "Part III")
    questions = parse_question_blocks(block, 1, 25)
    for item in questions:
        item["correct_answer_from_keys"] = keys.get(item["q_num"])
        item["correct_answer_from_explanation"] = None
        item["answer_conflict"] = False
        item["transcript"] = None
        item["key_sentence"] = None
        item["source_marker"] = None
        item["explanation"] = None
    return {
        "has_listening": bool(questions),
        "sections": [{"section": "Part II Listening Comprehension", "questions": questions}],
        "signal_words": [],
        "option_prediction": [],
        "strategy_note": [],
    }


def parse_reading(text: str, keys: dict[int, str]) -> dict[str, Any]:
    block = section_between(text, "Part III", "Part IV")
    section_a = section_between(block, "Section A", "Section B")
    section_b = section_between(block, "Section B", "Section C")
    section_c = section_between(block, "Section C", None)
    cloze_questions = [
        {"q_num": q, "correct_answer_from_keys": keys.get(q)}
        for q in range(26, 36)
    ]
    matching_questions = parse_numbered_text_blocks(section_b, 36, 45)
    for item in matching_questions:
        item["correct_answer_from_keys"] = keys.get(item["q_num"])
    reading_questions = parse_question_blocks(section_c, 46, 55)
    for item in reading_questions:
        item["correct_answer_from_keys"] = keys.get(item["q_num"])
        item["correct_answer_from_explanation"] = None
        item["answer_conflict"] = False
    word_bank = {}
    for letter, word in re.findall(r"\b([A-O])\)\s+([A-Za-z-]+)", section_a):
        word_bank[letter] = word
    return {
        "section_a": {
            "raw_text": normalize_space(section_a),
            "word_bank": word_bank,
            "questions": cloze_questions,
        },
        "section_b": {
            "raw_text": normalize_space(section_b),
            "questions": matching_questions,
        },
        "section_c": [{"raw_text": normalize_space(section_c), "questions": reading_questions}],
        "question_type": [],
        "synonym_mappings": [],
    }


def parse_translation(text: str) -> dict[str, Any]:
    block = section_between(text, "Part IV", "KEYS")
    chinese_lines = [line.strip() for line in block.splitlines() if re.search(r"[\u4e00-\u9fff]", line)]
    source_zh = normalize_space("\n".join(chinese_lines))
    return {
        "source_zh": source_zh,
        "reference_en": None,
        "difficult_terms": [],
        "topic_category": [],
        "sentence_analyses": [],
    }


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    text = read_text(path_from_root("data", "extracted_text", "2025_06_set1_paper.txt"))
    keys = parse_keys(text)
    parsed = {
        "writing": parse_writing(text),
        "listening": parse_listening(text, keys),
        "reading": parse_reading(text, keys),
        "translation": parse_translation(text),
        "keys": {str(k): v for k, v in sorted(keys.items())},
    }
    write_json(path_from_root("data", "structured", "2025_06_set1_paper_parsed.json"), parsed)
    print("parsed=data/structured/2025_06_set1_paper_parsed.json")


if __name__ == "__main__":
    main()
