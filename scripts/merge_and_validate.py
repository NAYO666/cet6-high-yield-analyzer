from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from utils import (
    ANSWER_PAGE_URL,
    ANSWER_PDF_NAME,
    PAPER_PAGE_URL,
    PAPER_PDF_NAME,
    ensure_dirs,
    ensure_sample_only,
    path_from_root,
    utc_now,
    write_json,
    write_text,
)


REQUIRED_TOP_LEVEL = ["meta", "writing", "listening", "reading", "translation", "validation"]
OPTION_LETTERS = {"A", "B", "C", "D"}
POLLUTION_RE = re.compile(
    r"===== PAGE|"
    r"\bSection Directions\b|"
    r"\bQuestions\s+\d+\s+to\s+\d+\s+are based on\b|"
    r"\bDirections:\b|"
    r"^\s*Section\s+[A-C]\b|"
    r"^\s*Passage\s+(?:One|Two)\b|"
    r"^\s*Part\s+[IVX]+\b",
    re.I | re.M,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lightweight_validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")
    meta = data.get("meta", {})
    expected = {
        "exam_id": "2025_06_set1",
        "year": 2025,
        "month": 6,
        "set_number": 1,
        "exam_type": "CET-6",
    }
    for key, value in expected.items():
        if meta.get(key) != value:
            errors.append(f"meta.{key} expected {value!r}, got {meta.get(key)!r}")
    return errors


def json_schema_validate(data: dict[str, Any]) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []

    schema = load_json(path_from_root("schemas", "exam_schema.json"))
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "$"
        errors.append(f"{path}: {error.message}")
    return errors


def all_structured_questions(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    questions: list[tuple[str, dict[str, Any]]] = []
    for item in data["listening"]["sections"][0]["questions"]:
        questions.append(("listening", item))
    for item in data["reading"]["section_a"]["questions"]:
        questions.append(("reading.section_a", item))
    for item in data["reading"]["section_b"]["questions"]:
        questions.append(("reading.section_b", item))
    for passage in data["reading"]["section_c"]:
        for item in passage["questions"]:
            questions.append(("reading.section_c", item))
    return questions


def validate_structure(data: dict[str, Any]) -> dict[str, Any]:
    listening = data["listening"]["sections"][0]["questions"]
    section_a = data["reading"]["section_a"]["questions"]
    section_b = data["reading"]["section_b"]["questions"]
    section_c = data["reading"]["section_c"][0]["questions"] if data["reading"]["section_c"] else []

    expected_sequences = {
        "listening": list(range(1, 26)),
        "reading.section_a": list(range(26, 36)),
        "reading.section_b": list(range(36, 46)),
        "reading.section_c": list(range(46, 56)),
    }
    actual_sequences = {
        "listening": [item.get("q_num") for item in listening],
        "reading.section_a": [item.get("q_num") for item in section_a],
        "reading.section_b": [item.get("q_num") for item in section_b],
        "reading.section_c": [item.get("q_num") for item in section_c],
    }
    sequence_errors = [
        {"section": section, "expected": expected, "actual": actual_sequences[section]}
        for section, expected in expected_sequences.items()
        if actual_sequences[section] != expected
    ]

    option_errors: list[dict[str, Any]] = []
    for section, items in [("listening", listening), ("reading.section_c", section_c)]:
        for item in items:
            option_keys = set((item.get("options") or {}).keys())
            if option_keys != OPTION_LETTERS:
                option_errors.append({
                    "section": section,
                    "q_num": item.get("q_num"),
                    "expected": sorted(OPTION_LETTERS),
                    "actual": sorted(option_keys),
                })

    statement_errors = [
        {"section": "reading.section_b", "q_num": item.get("q_num")}
        for item in section_b
        if not item.get("statement")
    ]

    pollution_hits: list[dict[str, Any]] = []
    for section, item in all_structured_questions(data):
        fields = []
        if "question" in item:
            fields.append(("question", item.get("question")))
        if "statement" in item:
            fields.append(("statement", item.get("statement")))
        for letter, option_text in (item.get("options") or {}).items():
            fields.append((f"options.{letter}", option_text))
        for field, value in fields:
            if isinstance(value, str) and POLLUTION_RE.search(value):
                pollution_hits.append({"section": section, "q_num": item.get("q_num"), "field": field})

    counts = {
        "listening": len(listening),
        "reading_section_a": len(section_a),
        "reading_section_b": len(section_b),
        "reading_section_c": len(section_c),
        "structured_question_count": len(all_structured_questions(data)),
    }
    expected_counts = {
        "listening": 25,
        "reading_section_a": 10,
        "reading_section_b": 10,
        "reading_section_c": 10,
        "structured_question_count": 55,
    }
    count_errors = [
        {"field": key, "expected": expected, "actual": counts[key]}
        for key, expected in expected_counts.items()
        if counts[key] != expected
    ]

    errors = sequence_errors + option_errors + statement_errors + pollution_hits + count_errors
    return {
        "passed": not errors,
        "counts": counts,
        "question_number_sequence_errors": sequence_errors,
        "option_completeness_errors": option_errors,
        "section_b_statement_errors": statement_errors,
        "pollution_text_hits": pollution_hits,
        "count_errors": count_errors,
    }


def collect_missing(data: dict[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []

    def add(path: str, reason: str) -> None:
        missing.append({"field": path, "reason": reason})

    writing = data["writing"]
    for key in ["reference_essay", "essay_translation_zh"]:
        if not writing.get(key):
            add(f"writing.{key}", "Not present in extracted answer text or not stably parsed.")
    if not writing.get("highlighted_vocabulary"):
        add("writing.highlighted_vocabulary", "No explicit highlighted vocabulary parsed from answer text.")
    if not writing.get("writing_patterns"):
        add("writing.writing_patterns", "No explicit writing patterns parsed from answer text.")

    listening_questions = data["listening"]["sections"][0]["questions"]
    for item in listening_questions:
        q = item["q_num"]
        if item.get("question") is None:
            add(
                f"listening.questions.{q}.question",
                "Paper text contains printed choices only; spoken question text is unavailable in the question PDF.",
            )
        if item.get("correct_answer_from_explanation") is None:
            add(f"listening.questions.{q}.correct_answer_from_explanation", "Answer explanation text unavailable or not stably parsed.")
        if item.get("transcript") is None:
            add(f"listening.questions.{q}.transcript", "Full transcript not stably mapped per question in Milestone 1 output.")
        if item.get("key_sentence") is None:
            add(f"listening.questions.{q}.key_sentence", "No stable [N] mapping parsed from answer text.")

    reading = data["reading"]
    for item in reading["section_a"]["questions"]:
        q = item["q_num"]
        if item.get("correct_answer_from_explanation") is None:
            add(f"reading.section_a.questions.{q}.correct_answer_from_explanation", "Answer explanation OCR did not expose a stable answer marker.")
    for item in reading["section_b"]["questions"]:
        q = item["q_num"]
        if item.get("correct_answer_from_explanation") is None:
            add(f"reading.section_b.questions.{q}.correct_answer_from_explanation", "Answer explanation OCR did not expose a stable paragraph marker.")
    for passage in reading["section_c"]:
        for item in passage["questions"]:
            q = item["q_num"]
            if item.get("correct_answer_from_explanation") is None:
                add(f"reading.section_c.questions.{q}.correct_answer_from_explanation", "Answer explanation OCR did not expose a stable answer marker.")
    if not reading["question_type"]:
        add("reading.question_type", "Allowed empty in Milestone 1.")
    if not reading["synonym_mappings"]:
        add("reading.synonym_mappings", "Allowed empty unless explicitly parsed from answer explanation.")

    translation = data["translation"]
    if translation.get("reference_en") is None:
        add("translation.reference_en", "Answer PDF extraction did not expose translation reference text.")
    if not translation["topic_category"]:
        add("translation.topic_category", "Allowed empty in Milestone 1.")
    if not translation["sentence_analyses"]:
        add("translation.sentence_analyses", "No explicit sentence-by-sentence analysis parsed from extracted answer text.")

    return missing


def merge_answers(paper: dict[str, Any], answer: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    conflicts: list[dict[str, Any]] = []
    answer_listening = {int(k): v for k, v in answer.get("listening_answers", {}).items()}
    answer_reading = {int(k): v for k, v in answer.get("reading_answers", {}).items()}

    def merge_item(item: dict[str, Any], parsed_answer: dict[str, Any], source: str) -> None:
        q_num = item["q_num"]
        explanation_answer = parsed_answer.get("correct_answer_from_explanation")
        item["correct_answer_from_explanation"] = explanation_answer
        if parsed_answer.get("explanation"):
            item["explanation"] = parsed_answer.get("explanation")
        key_answer = item.get("correct_answer_from_keys")
        conflict = bool(key_answer and explanation_answer and key_answer != explanation_answer)
        item["answer_conflict"] = conflict
        if conflict:
            conflicts.append({
                "q_num": q_num,
                "from_keys": key_answer,
                "from_explanation": explanation_answer,
                "source": source,
            })

    for section in paper["listening"]["sections"]:
        for item in section["questions"]:
            q_num = item["q_num"]
            parsed_answer = answer_listening.get(q_num, {})
            item["key_sentence"] = parsed_answer.get("key_sentence")
            item["source_marker"] = parsed_answer.get("source_marker")
            merge_item(item, parsed_answer, "listening")

    for item in paper["reading"]["section_a"]["questions"]:
        merge_item(item, answer_reading.get(item["q_num"], {}), "reading.section_a")
    for item in paper["reading"]["section_b"]["questions"]:
        merge_item(item, answer_reading.get(item["q_num"], {}), "reading.section_b")
    for passage in paper["reading"]["section_c"]:
        for item in passage["questions"]:
            merge_item(item, answer_reading.get(item["q_num"], {}), "reading.section_c")

    return paper, conflicts


def build_report(data: dict[str, Any], validation_errors: list[str]) -> str:
    meta = data["meta"]
    validation = data["validation"]
    structure = validation["structure_checks"]
    files = [
        path_from_root("data", "raw_pdfs", PAPER_PDF_NAME),
        path_from_root("data", "raw_pdfs", ANSWER_PDF_NAME),
        path_from_root("data", "extracted_text", "2025_06_set1_paper.txt"),
        path_from_root("data", "extracted_text", "2025_06_set1_answer.txt"),
        path_from_root("data", "structured", "2025_06_set1.json"),
        path_from_root("schemas", "exam_schema.json"),
    ]
    answer_text_path = path_from_root("data", "extracted_text", "2025_06_set1_answer.txt")
    answer_text = answer_text_path.read_text(encoding="utf-8") if answer_text_path.exists() else ""
    ocr_pages = sorted(int(page) for page in re.findall(r"===== PAGE (\d+) \[ocr:", answer_text))
    text_layer_pages = sorted(int(page) for page in re.findall(r"===== PAGE (\d+) \[text-layer\]", answer_text))
    lines = [
        "# CET-6 2025-06 Set 1 Data Quality Report",
        "",
        "## Sample Scope",
        "",
        f"- exam_id: `{meta['exam_id']}`",
        f"- year/month/set: `{meta['year']}-{meta['month']:02d}-set{meta['set_number']}`",
        "- scope: Milestone 1 sample only",
        "",
        "## Input and Output Files",
        "",
    ]
    for file in files:
        status = "exists" if file.exists() else "missing"
        size = file.stat().st_size if file.exists() else 0
        lines.append(f"- `{file.relative_to(path_from_root())}`: {status}, {size} bytes")

    lines.extend([
        "",
        "## Raw Text Extraction",
        "",
        "- Paper PDF text was extracted to `data/extracted_text/2025_06_set1_paper.txt`.",
        "- Answer PDF text was extracted to `data/extracted_text/2025_06_set1_answer.txt`.",
        "- Answer PDF diagnosis: pages 3-20 contain no extractable text layer or font resources; each page is a full-page JPEG image, so text-layer extraction returns blank.",
        f"- Answer PDF extraction method: text layer pages `{text_layer_pages}`; Windows OCR fallback pages `{ocr_pages}`.",
        "- OCR output is treated as extracted source text, not corrected source content. Fields are populated only when explicit answer markers were parsed; unstable OCR mappings remain `null` or are flagged as conflicts.",
        "",
        "## JSON, Schema, and Structure Validation",
        "",
        f"- JSON generated: `data/structured/2025_06_set1.json`",
        f"- Schema validation: {'passed' if not validation_errors else 'failed'}",
        f"- Structure checks: {'passed' if structure['passed'] else 'failed'}",
        f"- Structured question count: {structure['counts']['structured_question_count']}",
        f"- Listening questions: {structure['counts']['listening']}",
        f"- Reading Section A questions: {structure['counts']['reading_section_a']}",
        f"- Reading Section B questions: {structure['counts']['reading_section_b']}",
        f"- Reading Section C questions: {structure['counts']['reading_section_c']}",
        f"- Question number sequence errors: {len(structure['question_number_sequence_errors'])}",
        f"- Option completeness errors: {len(structure['option_completeness_errors'])}",
        f"- Section B statement errors: {len(structure['section_b_statement_errors'])}",
        f"- Pollution text hits in question/options/statement fields: {len(structure['pollution_text_hits'])}",
    ])
    if validation_errors:
        for error in validation_errors:
            lines.append(f"- {error}")

    lines.extend([
        "",
        "## Answer Cross-Check",
        "",
        f"- KEYS answer count: {validation['keys_answer_count']}",
        f"- Explanation answer count parsed: {validation['explanation_answer_count']}",
        f"- Listening explanation answers parsed: {validation['listening_explanation_answer_count']}",
        f"- Reading explanation answers parsed: {validation['reading_explanation_answer_count']}",
        f"- Objective answers checked: {validation['objective_answers_checked']}",
        f"- Answer conflicts: {len(validation['answer_conflicts'])}",
    ])
    if validation["answer_conflicts"]:
        for conflict in validation["answer_conflicts"]:
            lines.append(f"- Q{conflict['q_num']}: KEYS={conflict['from_keys']}, explanation={conflict['from_explanation']}")
    else:
        lines.append("- No conflicts found among answers that were available from both sources.")

    lines.extend([
        "",
        "## Missing or Intentionally Empty Fields",
        "",
        f"- Missing or intentionally empty fields recorded: {len(validation['missing_required_fields'])}",
    ])
    for item in validation["missing_required_fields"]:
        lines.append(f"- `{item['field']}`: {item['reason']}")

    lines.extend([
        "",
        "## Manual Review Required",
        "",
    ])
    for item in validation["manual_review_required"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Stop Condition",
        "",
        "Milestone 1 repair is complete for the sample only. Stop here and wait for manual review before Milestone 2 or 3.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    paper = load_json(path_from_root("data", "structured", "2025_06_set1_paper_parsed.json"))
    answer = load_json(path_from_root("data", "structured", "2025_06_set1_answer_parsed.json"))
    paper, conflicts = merge_answers(paper, answer)

    keys = paper.pop("keys")
    listening_explanation_answer_count = sum(
        1
        for section in paper["listening"]["sections"]
        for item in section["questions"]
        if item.get("correct_answer_from_explanation")
    )
    reading_items = (
        paper["reading"]["section_a"]["questions"]
        + paper["reading"]["section_b"]["questions"]
        + [item for passage in paper["reading"]["section_c"] for item in passage["questions"]]
    )
    reading_explanation_answer_count = sum(1 for item in reading_items if item.get("correct_answer_from_explanation"))
    explanation_answer_count = listening_explanation_answer_count + reading_explanation_answer_count

    data = {
        "meta": {
            "exam_id": "2025_06_set1",
            "year": 2025,
            "month": 6,
            "set_number": 1,
            "exam_type": "CET-6",
            "source_page_paper": PAPER_PAGE_URL,
            "source_page_answer": ANSWER_PAGE_URL,
            "source_pdf_paper": f"data/raw_pdfs/{PAPER_PDF_NAME}",
            "source_pdf_answer": f"data/raw_pdfs/{ANSWER_PDF_NAME}",
            "source_text_paper": "data/extracted_text/2025_06_set1_paper.txt",
            "source_text_answer": "data/extracted_text/2025_06_set1_answer.txt",
            "parsed_at": utc_now(),
            "parser_version": "0.1.1",
        },
        "writing": {
            **paper["writing"],
            "reference_essay": answer["writing"].get("reference_essay"),
            "essay_translation_zh": answer["writing"].get("essay_translation_zh"),
            "highlighted_vocabulary": answer["writing"].get("highlighted_vocabulary", []),
            "writing_patterns": answer["writing"].get("writing_patterns", []),
        },
        "listening": paper["listening"],
        "reading": paper["reading"],
        "translation": {
            **paper["translation"],
            "reference_en": answer["translation"].get("reference_en"),
            "difficult_terms": answer["translation"].get("difficult_terms", []),
            "sentence_analyses": answer["translation"].get("sentence_analyses", []),
        },
        "validation": {
            "objective_answers_checked": explanation_answer_count > 0,
            "keys_answer_count": len(keys),
            "explanation_answer_count": explanation_answer_count,
            "listening_explanation_answer_count": listening_explanation_answer_count,
            "reading_explanation_answer_count": reading_explanation_answer_count,
            "answer_conflicts": conflicts,
            "missing_required_fields": [],
            "manual_review_required": [
                "Review OCR-derived answer text on pages 3-20 before treating parsed explanation fields as final.",
                "Review listening printed-question fields: the paper PDF exposes choices, while the spoken question text is not printed.",
                "Review listening [N] marker mapping where populated from OCR.",
                "Review OCR answer conflicts, if any, before accepting explanation-derived answers.",
                "Review fields left as null or [] before any batch plan.",
            ],
        },
    }
    data["validation"]["missing_required_fields"] = collect_missing(data)
    data["validation"]["structure_checks"] = validate_structure(data)

    validation_errors = lightweight_validate(data) + json_schema_validate(data)
    data["validation"]["schema_validation"] = {
        "method": "jsonschema Draft 2020-12 when available plus internal top-level checks",
        "passed": not validation_errors,
        "errors": validation_errors,
    }

    write_json(path_from_root("data", "structured", "2025_06_set1.json"), data)
    write_text(path_from_root("reports", "data_quality_report.md"), build_report(data, validation_errors))
    parsing_errors = path_from_root("reports", "parsing_errors.log")
    if not parsing_errors.exists():
        parsing_errors.write_text("", encoding="utf-8")
    print("generated=data/structured/2025_06_set1.json")
    print("generated=reports/data_quality_report.md")


if __name__ == "__main__":
    main()
