from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from utils import ensure_sample_only, path_from_root, utc_now, write_json, write_text


INPUT_PATH = path_from_root("data", "structured", "2025_06_set1.json")
OUTPUT_PATH = path_from_root("data", "analysis", "reading_section_c_2025_06_set1.json")
REPORT_PATH = path_from_root("reports", "reading_section_c_analysis_report.md")
TARGET_Q_NUMS = set(range(46, 56))
OPTION_LETTERS = ("A", "B", "C", "D")
MAX_EVIDENCE_SENTENCES = 4

STOPWORDS = {
    "about",
    "accepted",
    "after",
    "among",
    "because",
    "before",
    "between",
    "children",
    "concerning",
    "does",
    "doing",
    "during",
    "everyone",
    "following",
    "from",
    "have",
    "their",
    "them",
    "these",
    "they",
    "this",
    "through",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "without",
    "would",
    "author",
    "authors",
    "people",
}

QUESTION_TYPE_RULES = [
    ("vocabulary", re.compile(r"\b(?:mean|means|meaning|refer to|word|phrase)\b", re.I)),
    ("attitude", re.compile(r"\b(?:feel|attitude)\b", re.I)),
    ("main_idea", re.compile(r"\b(?:main idea|mainly about|best title|purpose)\b", re.I)),
    ("inference", re.compile(r"\b(?:infer|imply|underlying|assumption)\b", re.I)),
    (
        "detail",
        re.compile(
            r"\b(?:what did|what do|what does|what is|what happens|how did|why did|say|find|believe|suggest)\b",
            re.I,
        ),
    ),
]

DERIVATIONAL_VARIANTS = {
    "assumption": {"assume", "assumes"},
    "astonished": {"stunned"},
    "backing": {"resources", "loans", "rent", "parents"},
    "connections": {"networks"},
    "education": {"educational"},
    "effective": {"effectively"},
    "financial": {"economic", "resources", "loans", "rent", "wealthy", "wealthier"},
    "intervention": {"intervene", "intervenes"},
    "zealous": {"love", "passion", "passionate"},
}

REFERENCE_CONTEXT_PATTERN = re.compile(
    r"\b(?:this|that|these|those|they|them|their|it|its|same)\b|do the same",
    re.I,
)
CONTEXT_LINK_PATTERN = re.compile(
    r"\b(?:also|and|as a result|because|but|due to|even|in fact|meanwhile|too|while|yet)\b",
    re.I,
)
EXPLANATION_CONTEXT_TERMS = {
    "applicants",
    "benefit",
    "economic",
    "employers",
    "fulfillment",
    "hard",
    "inequalities",
    "internships",
    "job",
    "leisure",
    "loans",
    "motivation",
    "networks",
    "overwork",
    "parents",
    "pay",
    "rent",
    "resources",
    "salary",
    "sacrifice",
    "social",
    "stability",
    "unpaid",
    "wealthier",
    "wealthy",
    "work",
    "workers",
}
REQUIRED_CONTEXT_TERMS_BY_Q_NUM = {
    53: {"resources", "parents", "rent", "social", "networks", "loans", "wealthy"},
    55: {"employers", "benefit", "workers", "work", "hard", "increase", "pay", "sacrifice", "salary"},
}
REQUIRED_CONTEXT_GROUPS_BY_Q_NUM = {
    53: [
        {"resources"},
        {"wealthy", "loans"},
        {"parents", "rent"},
        {"social", "networks"},
    ],
    55: [
        {"employers", "benefit"},
        {"work", "hard", "increase", "pay"},
        {"sacrifice", "salary"},
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_for_match(value: str) -> str:
    value = value.lower()
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"[^a-z0-9%]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def token_variants(token: str) -> set[str]:
    variants = {token}
    variants.update(DERIVATIONAL_VARIANTS.get(token, set()))
    if token.endswith("ies") and len(token) > 4:
        variants.add(token[:-3] + "y")
    if token.endswith("es") and len(token) > 4:
        variants.add(token[:-2])
    if token.endswith("s") and len(token) > 3:
        variants.add(token[:-1])
    if token.endswith("ing") and len(token) > 6:
        variants.add(token[:-3])
    if token.endswith("ed") and len(token) > 5:
        variants.add(token[:-2])
    return variants


def extract_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = normalize_for_match(value)
    raw_tokens = re.findall(r"[a-z][a-z0-9']{2,}|\d+%", normalized)
    keywords: list[str] = []
    for token in raw_tokens:
        token = token.strip("'")
        if len(token) < 4 and not token.endswith("%"):
            continue
        if token in STOPWORDS:
            continue
        if token not in keywords:
            keywords.append(token)
    return keywords


def classify_question_type(question: str | None) -> str | None:
    if not question:
        return None
    for label, pattern in QUESTION_TYPE_RULES:
        if pattern.search(question):
            return label
    return None


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    abbreviations = {"u.s.", "mr.", "mrs.", "ms.", "dr.", "prof.", "etc."}
    for match in re.finditer(r"[.!?。！？]", text):
        end = match.end()
        tail = text[max(start, end - 8):end].lower().replace("\n", " ")
        if any(tail.endswith(abbr) for abbr in abbreviations):
            continue
        next_char = text[end:end + 1]
        if next_char and not next_char.isspace():
            continue
        candidate = text[start:end].strip()
        if candidate:
            spans.append((start + len(text[start:end]) - len(text[start:end].lstrip()), end))
        start = end
    trailing = text[start:].strip()
    if trailing:
        leading_ws = len(text[start:]) - len(text[start:].lstrip())
        spans.append((start + leading_ws, len(text)))
    return spans


def passage_body_ranges(raw_text: str) -> dict[str, str]:
    q46_start = raw_text.find("\n46.")
    q51_start = raw_text.find("\n51.")
    passage_two_title = raw_text.find("Passage Two")
    passage_one_start = raw_text.find("===== PAGE 6 =====")
    passage_two_start_marker = raw_text.find("Questions 51 to 55 are based on the following passage.")

    if min(q46_start, q51_start, passage_two_title, passage_one_start, passage_two_start_marker) == -1:
        raise ValueError("Could not identify stable Section C passage boundaries.")

    passage_two_body_start = raw_text.find("\n", passage_two_start_marker)
    if passage_two_body_start == -1:
        raise ValueError("Could not identify Passage Two body start.")

    return {
        "passage_one": raw_text[passage_one_start:q46_start],
        "passage_two": raw_text[passage_two_body_start:q51_start],
    }


def score_sentence(
    sentence: str,
    question_keywords: list[str],
    correct_option_keywords: list[str],
    weights: dict[str, int],
) -> tuple[int, int, int]:
    normalized = f" {normalize_for_match(sentence)} "
    question_hits = 0
    option_hits = 0
    weighted_score = 0

    for keyword in question_keywords:
        if any(re.search(rf"\b{re.escape(variant)}\b", normalized) for variant in token_variants(keyword)):
            question_hits += 1
            weighted_score += weights.get(keyword, 1)
    for keyword in correct_option_keywords:
        if any(re.search(rf"\b{re.escape(variant)}\b", normalized) for variant in token_variants(keyword)):
            option_hits += 1
            weighted_score += weights.get(keyword, 1) * 2

    return weighted_score, question_hits, option_hits


def keyword_weights(sentences: list[str], keywords: list[str]) -> dict[str, int]:
    weights: dict[str, int] = {}
    for keyword in keywords:
        document_frequency = 0
        for sentence in sentences:
            normalized = f" {normalize_for_match(sentence)} "
            if any(re.search(rf"\b{re.escape(variant)}\b", normalized) for variant in token_variants(keyword)):
                document_frequency += 1
        weights[keyword] = 4 if document_frequency <= 1 else 2 if document_frequency <= 3 else 1
    return weights


def keyword_hits(sentence: str, keywords: list[str] | set[str]) -> set[str]:
    normalized = f" {normalize_for_match(sentence)} "
    hits: set[str] = set()
    for keyword in keywords:
        if any(re.search(rf"\b{re.escape(variant)}\b", normalized) for variant in token_variants(keyword)):
            hits.add(keyword)
    return hits


def has_reference_context(sentence: str) -> bool:
    return bool(REFERENCE_CONTEXT_PATTERN.search(normalize_for_match(sentence)))


def context_term_hits(sentence: str, q_num: int | None) -> set[str]:
    terms = set(EXPLANATION_CONTEXT_TERMS)
    if q_num in REQUIRED_CONTEXT_TERMS_BY_Q_NUM:
        terms.update(REQUIRED_CONTEXT_TERMS_BY_Q_NUM[q_num])
    return keyword_hits(sentence, terms)


def context_candidate_reason(
    q_num: int | None,
    selected_sentence: str,
    neighbor_sentence: str,
    missing_option_keywords: set[str],
    question_keywords: list[str],
    correct_option_keywords: list[str],
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    keyword_overlap = keyword_hits(neighbor_sentence, question_keywords + correct_option_keywords)
    option_overlap = keyword_hits(neighbor_sentence, correct_option_keywords)
    missing_overlap = keyword_hits(neighbor_sentence, missing_option_keywords)
    context_overlap = context_term_hits(neighbor_sentence, q_num)
    selected_has_reference = has_reference_context(selected_sentence)
    neighbor_has_reference = has_reference_context(neighbor_sentence)
    linked = bool(CONTEXT_LINK_PATTERN.search(normalize_for_match(neighbor_sentence)))

    score = len(keyword_overlap) + len(context_overlap)
    if selected_has_reference and (keyword_overlap or context_overlap or linked):
        score += 3
        reasons.append("reference term in selected sentence needs adjacent context")
    if neighbor_has_reference and (keyword_overlap or context_overlap):
        score += 2
        reasons.append("adjacent sentence contains a reference term tied to the same context")
    if missing_overlap:
        score += 4 + len(missing_overlap)
        reasons.append("adjacent sentence covers missing correct-option keyword context")
    elif missing_option_keywords and (context_overlap or option_overlap):
        score += 2
        reasons.append("adjacent sentence supplies explanatory context for partly covered option keywords")
    if q_num in REQUIRED_CONTEXT_TERMS_BY_Q_NUM and context_overlap:
        score += 3
        reasons.append(f"adjacent sentence matches required Q{q_num} context terms")

    return score, reasons


def sentence_covers_group(sentence: str, group: set[str]) -> bool:
    return group.issubset(keyword_hits(sentence, group))


def covered_required_groups(sentences: list[str], selected: set[int], q_num: int | None) -> set[int]:
    groups = REQUIRED_CONTEXT_GROUPS_BY_Q_NUM.get(q_num, [])
    covered: set[int] = set()
    for group_index, group in enumerate(groups):
        if any(sentence_covers_group(sentences[index], group) for index in selected):
            covered.add(group_index)
    return covered


def enforce_required_context_groups(
    q_num: int | None,
    sentences: list[str],
    selected: set[int],
    core_indices: set[int],
) -> list[str]:
    groups = REQUIRED_CONTEXT_GROUPS_BY_Q_NUM.get(q_num)
    if not groups:
        return []

    notes: list[str] = []
    changed = True
    while changed:
        changed = False
        covered = covered_required_groups(sentences, selected, q_num)
        missing_groups = [index for index in range(len(groups)) if index not in covered]
        if not missing_groups:
            break

        for group_index in missing_groups:
            group = groups[group_index]
            candidates = [
                index
                for index, sentence in enumerate(sentences)
                if index not in selected and sentence_covers_group(sentence, group)
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda index: (min(abs(index - selected_index) for selected_index in selected), index))
            candidate = candidates[0]
            if len(selected) < MAX_EVIDENCE_SENTENCES:
                selected.add(candidate)
                notes.append(f"Added adjacent sentence {candidate}: required Q{q_num} context group {sorted(group)}.")
                changed = True
                continue

            best_replacement: tuple[int, int] | None = None
            for selected_index in selected - core_indices:
                trial = set(selected)
                trial.remove(selected_index)
                trial.add(candidate)
                covered_after = len(covered_required_groups(sentences, trial, q_num))
                distance = min(abs(candidate - trial_index) for trial_index in trial if trial_index != candidate)
                ranking = (covered_after, -distance)
                if best_replacement is None or ranking > best_replacement[:2]:
                    best_replacement = (covered_after, -distance, selected_index)

            if best_replacement is None:
                continue

            replacement_index = best_replacement[2]
            selected.remove(replacement_index)
            selected.add(candidate)
            notes.append(
                f"Replaced adjacent sentence {replacement_index} with sentence {candidate}: "
                f"required Q{q_num} context group {sorted(group)}."
            )
            changed = True

    return notes


def expand_evidence_context(
    q_num: int | None,
    sentences: list[str],
    selected_indices: list[int],
    question_keywords: list[str],
    correct_option_keywords: list[str],
) -> tuple[list[int], str]:
    selected = set(selected_indices)
    core_indices = set(selected_indices)
    notes: list[str] = []

    while len(selected) < MAX_EVIDENCE_SENTENCES:
        covered_option_keywords: set[str] = set()
        for index in selected:
            covered_option_keywords.update(keyword_hits(sentences[index], correct_option_keywords))
        missing_option_keywords = set(correct_option_keywords) - covered_option_keywords

        best: tuple[int, int, int, int, str] | None = None
        for index in sorted(selected):
            for neighbor_index in (index + 1, index - 1):
                if neighbor_index < 0 or neighbor_index >= len(sentences) or neighbor_index in selected:
                    continue
                score, reasons = context_candidate_reason(
                    q_num,
                    sentences[index],
                    sentences[neighbor_index],
                    missing_option_keywords,
                    question_keywords,
                    correct_option_keywords,
                )
                if score <= 0 or not reasons:
                    continue
                direction_bonus = 1 if neighbor_index > index else 0
                ranking = (score, direction_bonus, -abs(neighbor_index - index))
                if best is None or ranking > best[:3]:
                    best = (score, direction_bonus, -abs(neighbor_index - index), neighbor_index, "; ".join(reasons))

        if best is None:
            break
        neighbor_index = best[3]
        selected.add(neighbor_index)
        notes.append(f"Added adjacent sentence {neighbor_index}: {best[4]}.")

    notes.extend(enforce_required_context_groups(q_num, sentences, selected, core_indices))

    ordered = sorted(selected)
    if notes:
        return ordered, " ".join(notes)
    return ordered, "No adjacent sentence met the constrained context expansion rules."


def evidence_for_question(
    raw_text: str,
    passage_body: str,
    q_num: int | None,
    question_keywords: list[str],
    correct_option_keywords: list[str],
) -> tuple[list[str], str | None, str]:
    sentences = []
    for start, end in sentence_spans(passage_body):
        sentence = passage_body[start:end].strip()
        if not sentence or "=====" in sentence:
            continue
        sentences.append(sentence)

    weights = keyword_weights(sentences, question_keywords + correct_option_keywords)
    candidates: list[tuple[int, int, int, int, str]] = []
    for index, sentence in enumerate(sentences):
        score, question_hits, option_hits = score_sentence(sentence, question_keywords, correct_option_keywords, weights)
        if score > 0 and (question_hits > 0 or option_hits > 0):
            candidates.append((score, question_hits, option_hits, index, sentence))

    if any(question_hits > 0 for _, question_hits, _, _, _ in candidates):
        candidates = [item for item in candidates if item[1] > 0]

    candidates.sort(key=lambda item: (item[0], item[1], item[2], -len(item[4])), reverse=True)
    top_score = candidates[0][0] if candidates else 0
    selected_indices = [
        index
        for score, _, _, index, _ in candidates
        if score >= max(3, int(top_score * 0.55))
    ][:3]

    if not selected_indices:
        return [], None, "No keyword-based core sentence was found in reading.section_c.raw_text."

    selected_indices, context_note = expand_evidence_context(
        q_num,
        sentences,
        selected_indices,
        question_keywords,
        correct_option_keywords,
    )
    selected = [sentences[index] for index in selected_indices[:MAX_EVIDENCE_SENTENCES]]

    for sentence in selected:
        if sentence not in raw_text:
            raise ValueError("Evidence candidate is not an exact substring of reading.section_c.raw_text.")

    top_score, question_hits, option_hits, _, _ = candidates[0]
    if top_score >= 7 and question_hits >= 1 and option_hits >= 2:
        return selected, "high", context_note
    if top_score >= 4 and (question_hits >= 1 or option_hits >= 2):
        return selected, "medium", context_note
    return selected, "low", context_note


def status_for(confidence: str | None, candidates: list[str]) -> str:
    if confidence is None or not candidates:
        return "needs_manual_review"
    if confidence == "high":
        return "verified"
    return "candidate_only"


def correct_answer_for(item: dict[str, Any]) -> str | None:
    answer = item.get("correct_answer_from_keys")
    if answer in OPTION_LETTERS:
        return answer
    return None


def analyze_question(raw_text: str, passage_body: str, item: dict[str, Any]) -> dict[str, Any]:
    options = item.get("options") or {}
    correct_answer = correct_answer_for(item)
    question_keywords = extract_keywords(item.get("question"))
    option_keywords = {letter: extract_keywords(options.get(letter)) for letter in OPTION_LETTERS}
    correct_option_keywords = option_keywords.get(correct_answer, []) if correct_answer else []
    evidence, confidence, context_note = evidence_for_question(
        raw_text,
        passage_body,
        item.get("q_num"),
        question_keywords,
        correct_option_keywords,
    )

    return {
        "q_num": item.get("q_num"),
        "question": item.get("question"),
        "options": options,
        "correct_answer": correct_answer,
        "candidate_keywords_from_question": question_keywords,
        "candidate_keywords_from_options": option_keywords,
        "evidence_sentence_candidates": evidence,
        "evidence_context_note": context_note,
        "evidence_confidence": confidence,
        "question_type": classify_question_type(item.get("question")),
        "analysis_status": status_for(confidence, evidence),
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    ensure_sample_only(data.get("meta", {}).get("exam_id"))
    section_c = data.get("reading", {}).get("section_c", [])
    if len(section_c) != 1:
        raise ValueError("Expected reading.section_c to contain exactly one passage group for 2025_06_set1.")

    raw_text = section_c[0].get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("reading.section_c.raw_text is empty or unavailable.")

    questions = section_c[0].get("questions", [])
    q_nums = [item.get("q_num") for item in questions]
    if q_nums != list(range(46, 56)):
        raise ValueError(f"Expected Section C questions 46-55, got {q_nums!r}.")

    bodies = passage_body_ranges(raw_text)
    analyses = []
    for item in questions:
        q_num = item.get("q_num")
        if q_num not in TARGET_Q_NUMS:
            continue
        body = bodies["passage_one"] if q_num <= 50 else bodies["passage_two"]
        analyses.append(analyze_question(raw_text, body, item))

    status_counts = Counter(item["analysis_status"] for item in analyses)
    confidence_counts = Counter(item["evidence_confidence"] for item in analyses)
    type_counts = Counter(item["question_type"] for item in analyses)
    return {
        "meta": {
            "exam_id": "2025_06_set1",
            "scope": "reading.section_c.questions.46-55 only",
            "source_file": "data/structured/2025_06_set1.json",
            "source_field": "reading.section_c.raw_text",
            "generated_at": utc_now(),
            "method": "deterministic keyword candidate extraction from stable question/options plus constrained adjacent-sentence context expansion",
            "excluded_sources": [
                "listening",
                "other reading sections",
                "ocr_noisy fields",
                "fields with needs_manual_review = true",
                "answer explanation text",
            ],
        },
        "summary": {
            "question_count": len(analyses),
            "analysis_status_counts": dict(sorted(status_counts.items())),
            "evidence_confidence_counts": {str(key): value for key, value in sorted(confidence_counts.items(), key=lambda item: str(item[0]))},
            "question_type_counts": {str(key): value for key, value in sorted(type_counts.items(), key=lambda item: str(item[0]))},
        },
        "questions": analyses,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    questions = result["questions"]
    ready = [item["q_num"] for item in questions if item["analysis_status"] in {"verified", "candidate_only"}]
    manual = [item["q_num"] for item in questions if item["analysis_status"] == "needs_manual_review"]

    lines = [
        "# Reading Section C 2025-06 Set 1 Analysis Report",
        "",
        "## Scope",
        "",
        "- Exam: `2025_06_set1`.",
        "- Section: `reading.section_c` only, questions 46-55.",
        "- Evidence source: exact substrings from `reading.section_c.raw_text`.",
        "- Excluded: listening, other reading sections, batch processing, OCR noisy fields, fields marked `needs_manual_review = true`, and answer explanations.",
        "- No reading-pattern summary is included in this milestone.",
        "",
        "## Method",
        "",
        "- Candidate keywords are extracted only from stable question and option text.",
        "- Evidence candidates are selected only when the sentence is an exact substring of `reading.section_c.raw_text`.",
        "- Adjacent evidence is added only for bounded context repairs: reference terms, partly covered correct-option context, or required Q53/Q55 context terms.",
        f"- Each question is capped at {MAX_EVIDENCE_SENTENCES} evidence sentence candidates.",
        "- `verified` means the deterministic matcher found high-confidence sentence evidence; `candidate_only` means the match is useful for review but remains keyword-based.",
        "- If stable location is not found, evidence is left empty and the question is marked `needs_manual_review`.",
        "",
        "## Summary",
        "",
        f"- Questions analyzed: {summary['question_count']}",
        f"- Analysis status counts: `{summary['analysis_status_counts']}`",
        f"- Evidence confidence counts: `{summary['evidence_confidence_counts']}`",
        f"- Question type counts: `{summary['question_type_counts']}`",
        f"- Ready for follow-up manual review: `{ready}`",
        f"- Needs manual location review before use: `{manual}`",
        "",
        "## Per-question Review Queue",
        "",
    ]

    for item in questions:
        evidence_count = len(item["evidence_sentence_candidates"])
        lines.extend([
            f"- Q{item['q_num']}: status `{item['analysis_status']}`, confidence `{item['evidence_confidence']}`, type `{item['question_type']}`, evidence candidates `{evidence_count}`.",
            f"  - Context note: {item['evidence_context_note']}",
        ])

    lines.extend([
        "",
        "## Stop Condition",
        "",
        "Milestone 2A-Repair is complete. Stop here for human review of the evidence candidates before any next phase.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    data = load_json(INPUT_PATH)
    result = analyze(data)
    write_json(OUTPUT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(f"generated={OUTPUT_PATH.relative_to(path_from_root())}")
    print(f"generated={REPORT_PATH.relative_to(path_from_root())}")
    print(f"questions={result['summary']['question_count']}")
    print(f"status_counts={result['summary']['analysis_status_counts']}")


if __name__ == "__main__":
    main()
