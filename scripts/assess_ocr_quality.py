from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from merge_and_validate import json_schema_validate, lightweight_validate, validate_structure
from utils import ensure_dirs, ensure_sample_only, path_from_root, write_json, write_text


QUALITY_LABELS = {"text_layer_clean", "ocr_clean", "ocr_noisy", None}
TARGET_SECTION_TITLE = "## OCR Field Quality Assessment"
BOUNDARY_TERMS = [
    "===== PAGE",
    "ocr:",
    "答案详解",
    "听力原文",
    "Conversation Two",
    "Conversation Three",
    "Recording Two",
    "Recording Three",
    "参考译文",
    "译点精析",
    # Mojibake variants that appear in the current OCR-derived JSON.
    "绛旀",
    "鍚姏鍘熸枃",
    "璇?鐐?绮?",
    "ConversationTWO",
    "ConversationTHREE",
    "RecordingTWO",
    "RecordingTHREE",
]
NEXT_TITLE_TERMS = [
    "Conversation Two",
    "Conversation Three",
    "Recording Two",
    "Recording Three",
    "Passage Two",
    "Part III",
    "Part IV",
]
MOJIBAKE_RE = re.compile(r"[\ufffd\ue000-\uf8ff]|[鈥€锛宀宄宂侰侭俢灬]")
ALPHA_RUN_RE = re.compile(r"[A-Za-z]{35,}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def has_boundary_pollution(value: str) -> bool:
    dense = compact(value).lower()
    lowered = value.lower()
    for term in BOUNDARY_TERMS:
        if term.lower() in lowered or compact(term).lower() in dense:
            return True
    return False


def has_cross_question_contamination(value: str, q_num: int | None) -> bool:
    if q_num is None:
        return False

    next_q = q_num + 1
    patterns = [
        rf"(?<!\d){next_q}\s*[\.\uff0e,\uff0c\u3001:：]",
        rf"(?<!\d){next_q}(?:What|Why|How|Where|Which|Who)",
        rf"[\[\u3010\u535c]\s*{next_q}\s*[\]\u3011]",
    ]
    if any(re.search(pattern, value, re.I) for pattern in patterns):
        return True

    dense = compact(value)
    dense_patterns = [
        rf"(?<!\d){next_q}(?:What|Why|How|Where|Which|Who)",
        rf"(?<!\d){next_q}(?:锛|，|\.|．)",
    ]
    if any(re.search(pattern, dense, re.I) for pattern in dense_patterns):
        return True

    if any(term.lower() in value.lower() or compact(term).lower() in dense.lower() for term in NEXT_TITLE_TERMS):
        return True
    return False


def has_spacing_loss(value: str) -> bool:
    runs = ALPHA_RUN_RE.findall(value)
    if runs:
        return True

    alpha_chars = len(re.findall(r"[A-Za-z]", value))
    if alpha_chars < 45:
        return False
    spaced_words = len(re.findall(r"\b[A-Za-z]{2,}\b", value))
    return spaced_words <= 2 and alpha_chars >= 60


def has_garbled_chars(value: str) -> bool:
    mojibake_hits = len(MOJIBAKE_RE.findall(value))
    if mojibake_hits >= 6:
        return True
    if value.count("?") >= 8 and re.search(r"[\u4e00-\u9fff]", value):
        return True

    allowed = re.compile(
        r"[\w\s\u4e00-\u9fff.,;:!?'\"><()\[\]\-/%$&+"
        r"\uff0c\u3002\uff1b\uff1a\uff01\uff1f\u201c\u201d\u2018\u2019"
        r"\uff08\uff09\u3010\u3011\u3001\u00b7\u2014\u2026]"
    )
    unusual = sum(1 for char in value if not allowed.fullmatch(char))
    return unusual >= 10 and unusual / max(len(value), 1) > 0.03


def source_for(value: Any, default_source: str = "ocr") -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return default_source


def base_label(source: str | None, quality: str | None, usable: bool, review: bool, issues: list[str]) -> dict[str, Any]:
    assert quality in QUALITY_LABELS
    return {
        "source": source,
        "quality": quality,
        "usable_for_analysis": usable,
        "needs_manual_review": review,
        "issues": issues,
    }


def assess_field(
    value: Any,
    *,
    field_kind: str,
    q_num: int | None = None,
    default_source: str = "ocr",
) -> dict[str, Any]:
    source = source_for(value, default_source)
    if source is None:
        return base_label(None, None, False, False, [])

    text = str(value)
    issues: list[str] = []
    if has_boundary_pollution(text):
        issues.append("possible_boundary_pollution")
    if has_cross_question_contamination(text, q_num):
        issues.append("possible_cross_question_contamination")
    if has_spacing_loss(text):
        issues.append("ocr_spacing_loss")
    if has_garbled_chars(text):
        issues.append("ocr_garbled_chars")

    if field_kind == "key_sentence" and not 12 <= len(text.strip()) <= 320:
        issues.append("key_sentence_length_out_of_range")

    quality = f"{source}_clean" if not issues else "ocr_noisy"
    usable = quality != "ocr_noisy"

    if field_kind == "explanation" and (
        "possible_boundary_pollution" in issues or "possible_cross_question_contamination" in issues
    ):
        usable = False
    if field_kind == "key_sentence" and (
        "possible_boundary_pollution" in issues
        or "possible_cross_question_contamination" in issues
        or "key_sentence_length_out_of_range" in issues
    ):
        usable = False
    if quality == "ocr_noisy":
        usable = False

    return base_label(source, quality, usable, quality == "ocr_noisy", issues)


def add_assessment(
    labels: list[dict[str, Any]],
    holder: dict[str, Any],
    field: str,
    *,
    path: str,
    field_kind: str,
    q_num: int | None = None,
    default_source: str = "ocr",
) -> None:
    label = assess_field(holder.get(field), field_kind=field_kind, q_num=q_num, default_source=default_source)
    holder[f"{field}_quality"] = label
    labels.append({"path": path, **label})


def assess_data(data: dict[str, Any]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []

    for section in data["listening"]["sections"]:
        for item in section["questions"]:
            q_num = item["q_num"]
            base = f"listening.questions.{q_num}"
            add_assessment(labels, item, "explanation", path=f"{base}.explanation", field_kind="explanation", q_num=q_num)
            add_assessment(labels, item, "key_sentence", path=f"{base}.key_sentence", field_kind="key_sentence", q_num=q_num)
            add_assessment(
                labels,
                item,
                "correct_answer_from_explanation",
                path=f"{base}.correct_answer_from_explanation",
                field_kind="answer",
                q_num=q_num,
            )

    for item in data["reading"]["section_a"]["questions"]:
        q_num = item["q_num"]
        add_assessment(
            labels,
            item,
            "correct_answer_from_explanation",
            path=f"reading.section_a.questions.{q_num}.correct_answer_from_explanation",
            field_kind="answer",
            q_num=q_num,
        )

    for item in data["reading"]["section_b"]["questions"]:
        q_num = item["q_num"]
        add_assessment(
            labels,
            item,
            "correct_answer_from_explanation",
            path=f"reading.section_b.questions.{q_num}.correct_answer_from_explanation",
            field_kind="answer",
            q_num=q_num,
        )

    for passage in data["reading"]["section_c"]:
        for item in passage["questions"]:
            q_num = item["q_num"]
            base = f"reading.section_c.questions.{q_num}"
            add_assessment(
                labels,
                item,
                "correct_answer_from_explanation",
                path=f"{base}.correct_answer_from_explanation",
                field_kind="answer",
                q_num=q_num,
            )
            add_assessment(labels, item, "explanation", path=f"{base}.explanation", field_kind="explanation", q_num=q_num)

    add_assessment(
        labels,
        data["translation"],
        "reference_en",
        path="translation.reference_en",
        field_kind="reference",
    )
    return labels


def summarize(labels: list[dict[str, Any]]) -> dict[str, Any]:
    quality_counts = Counter(label["quality"] for label in labels)
    issue_counts: Counter[str] = Counter()
    for label in labels:
        issue_counts.update(label["issues"])
    return {
        "assessed_field_count": len(labels),
        "text_layer_clean_count": quality_counts["text_layer_clean"],
        "ocr_clean_count": quality_counts["ocr_clean"],
        "ocr_noisy_count": quality_counts["ocr_noisy"],
        "null_count": quality_counts[None],
        "usable_for_analysis_count": sum(1 for label in labels if label["usable_for_analysis"]),
        "needs_manual_review_count": sum(1 for label in labels if label["needs_manual_review"]),
        "issue_counts": dict(sorted(issue_counts.items())),
    }


def render_report_section(summary: dict[str, Any]) -> str:
    lines = [
        TARGET_SECTION_TITLE,
        "",
        "- Scope: specified answer-derived OCR fields for `2025_06_set1` only.",
        f"- Assessed field count: {summary['assessed_field_count']}",
        f"- text_layer_clean count: {summary['text_layer_clean_count']}",
        f"- ocr_clean count: {summary['ocr_clean_count']}",
        f"- ocr_noisy count: {summary['ocr_noisy_count']}",
        f"- null count: {summary['null_count']}",
        f"- usable_for_analysis count: {summary['usable_for_analysis_count']}",
        f"- needs_manual_review count: {summary['needs_manual_review_count']}",
    ]
    if summary["issue_counts"]:
        lines.append(f"- issue counts: {summary['issue_counts']}")
    return "\n".join(lines)


def update_report(summary: dict[str, Any]) -> None:
    report_path = path_from_root("reports", "data_quality_report.md")
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    section = render_report_section(summary)
    pattern = re.compile(rf"\n{re.escape(TARGET_SECTION_TITLE)}\n.*?(?=\n## |\Z)", re.S)
    if pattern.search(report):
        report = pattern.sub("\n" + section + "\n", report)
    elif "\n## Manual Review Required" in report:
        report = report.replace("\n## Manual Review Required", "\n" + section + "\n\n## Manual Review Required", 1)
    else:
        report = report.rstrip() + "\n\n" + section + "\n"
    write_text(report_path, report.rstrip() + "\n")


def update_validation(data: dict[str, Any], labels: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    validation = data.setdefault("validation", {})
    validation["ocr_field_quality_summary"] = summary
    validation["ocr_field_quality_fields"] = labels
    validation["structure_checks"] = validate_structure(data)
    errors = lightweight_validate(data) + json_schema_validate(data)
    validation["schema_validation"] = {
        "method": "jsonschema Draft 2020-12 when available plus internal top-level checks",
        "passed": not errors,
        "errors": errors,
    }


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    path = path_from_root("data", "structured", "2025_06_set1.json")
    data = load_json(path)
    ensure_sample_only(data.get("meta", {}).get("exam_id"))

    labels = assess_data(data)
    summary = summarize(labels)
    update_validation(data, labels, summary)
    write_json(path, data)
    update_report(summary)

    print(f"assessed_fields={summary['assessed_field_count']}")
    print(f"ocr_clean={summary['ocr_clean_count']}")
    print(f"ocr_noisy={summary['ocr_noisy_count']}")
    print(f"null={summary['null_count']}")
    print(f"schema_validation={'passed' if data['validation']['schema_validation']['passed'] else 'failed'}")
    print(f"structure_checks={'passed' if data['validation']['structure_checks']['passed'] else 'failed'}")


if __name__ == "__main__":
    main()
