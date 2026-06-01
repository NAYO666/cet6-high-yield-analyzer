import argparse
import hashlib
import json
import sys
from pathlib import Path

from export_reading_display import ExportError, load_display_json, render_markdown


EXPECTED_READING_DISPLAY_Q_NUMS = [46, 47, 48, 49, 50, 51, 53, 54]
FORBIDDEN_READING_DISPLAY_Q_NUMS = [52, 55]
DEFAULT_PAPERS_CONFIG_PATH = Path("configs") / "papers.json"
ALLOWED_CONFIG_PAPER_IDS = ["2025_06_set1"]
ALLOWED_CONFIG_SECTIONS = ["reading_section_c"]
REQUIRED_SECTION_CONFIG_KEYS = [
    "section_root",
    "review_sheet",
    "final_explanations",
    "display_json",
    "export_markdown",
    "manifest",
]
EXPECTED_OPTION_ORDER = ["A", "B", "C", "D"]
REQUIRED_QUESTION_FIELDS = [
    "q_num",
    "question",
    "options",
    "option_order",
    "correct_answer",
    "display_blocks",
]
REQUIRED_DISPLAY_BLOCK_TYPES = [
    "answer",
    "explanation",
    "evidence",
    "location_method",
    "paraphrase",
    "low_vocab_tip",
]
POLLUTION_TERMS = ["草稿", "候选", "仍需人工复核", "????"]
NO_EXTRA_CONTEXT_EVIDENCE = "无额外上下文证据"
VALIDATION_RULE_IDS = [
    "input_exists",
    "json_parseable",
    "top_level_questions_exists",
    "top_level_questions_is_list",
    "questions_not_empty",
    "q_nums_allowed",
    "forbidden_q_nums_absent",
    "q_nums_exact_match",
    "q_num_required",
    "question_required",
    "options_required",
    "option_order_required",
    "correct_answer_required",
    "display_blocks_required",
    "option_order_exact",
    "options_contains_a",
    "options_contains_b",
    "options_contains_c",
    "options_contains_d",
    "option_texts_non_empty",
    "required_display_block_types",
    "answer_content_matches_correct_answer",
    "explanation_content_non_empty",
    "explanation_content_no_pollution",
    "evidence_items_is_list",
    "evidence_context_items_is_list",
    "evidence_context_note_exists",
    "evidence_items_no_context_note",
    "empty_context_items_note_exact",
    "non_empty_context_items_note_may_be_empty",
    "evidence_items_non_empty",
    "location_method_items_is_list",
    "location_method_items_non_empty",
    "location_method_items_no_pollution",
    "paraphrase_items_is_list",
    "paraphrase_item_evidence_phrase",
    "paraphrase_item_option_key",
    "paraphrase_item_option_phrase",
    "paraphrase_item_confirmed_note_zh",
    "low_vocab_tip_content_non_empty",
    "low_vocab_tip_content_no_pollution",
]


def validate_display_json(data):
    if not isinstance(data, dict):
        raise ExportError("Input JSON must be an object with required field: questions.")

    if "questions" not in data:
        raise ExportError("Input JSON is missing required field: questions.")

    questions = data["questions"]
    if not isinstance(questions, list):
        raise ExportError("Input JSON field 'questions' must be a list.")

    for question in questions:
        if not isinstance(question, dict):
            raise ExportError("Each item in 'questions' must be an object.")

        q_num = question.get("q_num", "unknown")
        if "display_blocks" not in question:
            raise ExportError(f"Question Q{q_num} is missing required field: display_blocks.")
        if not isinstance(question["display_blocks"], list):
            raise ExportError(f"Question Q{q_num} field 'display_blocks' must be a list.")


def has_text(value):
    return isinstance(value, str) and value.strip() != ""


def contains_pollution(value):
    if isinstance(value, str):
        return [term for term in POLLUTION_TERMS if term in value]
    return []


def block_map(question):
    blocks = question.get("display_blocks", [])
    mapped = {}
    duplicates = []
    if not isinstance(blocks, list):
        return mapped, duplicates

    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type in mapped:
            duplicates.append(block_type)
        mapped[block_type] = block
    return mapped, duplicates


def add_error(errors, message):
    errors.append(message)


def validate_reading_display_data(data):
    errors = []
    warnings = []
    validated_q_nums = []

    if not isinstance(data, dict):
        add_error(errors, "Top-level JSON value must be an object.")
        return errors, warnings, validated_q_nums

    if "questions" not in data:
        add_error(errors, "Top-level field 'questions' is missing.")
        return errors, warnings, validated_q_nums

    questions = data["questions"]
    if not isinstance(questions, list):
        add_error(errors, "Top-level field 'questions' must be a list.")
        return errors, warnings, validated_q_nums

    if not questions:
        add_error(errors, "Top-level field 'questions' must not be empty.")
        return errors, warnings, validated_q_nums

    actual_q_nums = []
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            add_error(errors, f"questions[{index}] must be an object.")
            continue
        actual_q_nums.append(question.get("q_num"))

    validated_q_nums = [q_num for q_num in actual_q_nums if isinstance(q_num, int)]
    if actual_q_nums != EXPECTED_READING_DISPLAY_Q_NUMS:
        add_error(
            errors,
            "Actual q_num list must equal "
            f"{EXPECTED_READING_DISPLAY_Q_NUMS}; got {actual_q_nums}.",
        )

    for q_num in actual_q_nums:
        if q_num in FORBIDDEN_READING_DISPLAY_Q_NUMS:
            add_error(errors, f"Forbidden question Q{q_num} appears in questions.")
        if q_num not in EXPECTED_READING_DISPLAY_Q_NUMS:
            add_error(
                errors,
                f"Question q_num {q_num!r} is outside the allowed current sample range.",
            )

    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            continue

        q_label = f"Q{question.get('q_num', f'index {index}')}"
        for field in REQUIRED_QUESTION_FIELDS:
            if field not in question:
                add_error(errors, f"{q_label} is missing required field '{field}'.")

        q_num = question.get("q_num")
        if not isinstance(q_num, int):
            add_error(errors, f"{q_label} field 'q_num' must be an integer.")

        if not has_text(question.get("question")):
            add_error(errors, f"{q_label} field 'question' must be non-empty text.")

        correct_answer = question.get("correct_answer")
        if correct_answer not in EXPECTED_OPTION_ORDER:
            add_error(errors, f"{q_label} field 'correct_answer' must be A, B, C, or D.")

        option_order = question.get("option_order")
        if option_order != EXPECTED_OPTION_ORDER:
            add_error(
                errors,
                f"{q_label} field 'option_order' must equal {EXPECTED_OPTION_ORDER}.",
            )

        options = question.get("options")
        if not isinstance(options, dict):
            add_error(errors, f"{q_label} field 'options' must be an object.")
        else:
            for option_key in EXPECTED_OPTION_ORDER:
                if option_key not in options:
                    add_error(errors, f"{q_label} options is missing key '{option_key}'.")
                elif not has_text(options.get(option_key)):
                    add_error(errors, f"{q_label} option '{option_key}' must be non-empty.")

        display_blocks = question.get("display_blocks")
        if not isinstance(display_blocks, list):
            add_error(errors, f"{q_label} field 'display_blocks' must be a list.")
            continue

        blocks_by_type, duplicate_types = block_map(question)
        for duplicate_type in duplicate_types:
            add_error(errors, f"{q_label} has duplicate display block type '{duplicate_type}'.")
        for block_type in REQUIRED_DISPLAY_BLOCK_TYPES:
            if block_type not in blocks_by_type:
                add_error(errors, f"{q_label} is missing display block type '{block_type}'.")

        answer = blocks_by_type.get("answer", {})
        if answer.get("content") != correct_answer:
            add_error(errors, f"{q_label} answer.content must equal correct_answer.")

        explanation = blocks_by_type.get("explanation", {})
        explanation_content = explanation.get("content")
        if not has_text(explanation_content):
            add_error(errors, f"{q_label} explanation.content must be non-empty.")
        for term in contains_pollution(explanation_content):
            add_error(errors, f"{q_label} explanation.content contains forbidden term '{term}'.")

        evidence = blocks_by_type.get("evidence", {})
        evidence_items = evidence.get("items")
        context_items = evidence.get("context_items")
        if not isinstance(evidence_items, list):
            add_error(errors, f"{q_label} evidence.items must be a list.")
        elif not evidence_items:
            add_error(errors, f"{q_label} evidence.items must not be empty.")
        else:
            for item_index, item in enumerate(evidence_items):
                if NO_EXTRA_CONTEXT_EVIDENCE in str(item):
                    add_error(
                        errors,
                        f"{q_label} evidence.items[{item_index}] must not contain '{NO_EXTRA_CONTEXT_EVIDENCE}'.",
                    )

        if not isinstance(context_items, list):
            add_error(errors, f"{q_label} evidence.context_items must be a list.")

        if "context_note" not in evidence:
            add_error(errors, f"{q_label} evidence.context_note must exist.")
        elif isinstance(context_items, list):
            context_note = evidence.get("context_note")
            if not context_items and context_note != NO_EXTRA_CONTEXT_EVIDENCE:
                add_error(
                    errors,
                    f"{q_label} evidence.context_note must be '{NO_EXTRA_CONTEXT_EVIDENCE}' when context_items is empty.",
                )
            if context_items and not isinstance(context_note, str):
                add_error(errors, f"{q_label} evidence.context_note must be a string.")

        location_method = blocks_by_type.get("location_method", {})
        location_items = location_method.get("items")
        if not isinstance(location_items, list):
            add_error(errors, f"{q_label} location_method.items must be a list.")
        elif not location_items:
            add_error(errors, f"{q_label} location_method.items must not be empty.")
        else:
            for item_index, item in enumerate(location_items):
                for term in contains_pollution(str(item)):
                    add_error(
                        errors,
                        f"{q_label} location_method.items[{item_index}] contains forbidden term '{term}'.",
                    )

        paraphrase = blocks_by_type.get("paraphrase", {})
        paraphrase_items = paraphrase.get("items")
        if not isinstance(paraphrase_items, list):
            add_error(errors, f"{q_label} paraphrase.items must be a list.")
        else:
            for item_index, item in enumerate(paraphrase_items):
                if not isinstance(item, dict):
                    add_error(errors, f"{q_label} paraphrase.items[{item_index}] must be an object.")
                    continue
                for field in [
                    "evidence_phrase",
                    "option_key",
                    "option_phrase",
                    "confirmed_note_zh",
                ]:
                    if field not in item:
                        add_error(
                            errors,
                            f"{q_label} paraphrase.items[{item_index}] is missing '{field}'.",
                        )

        low_vocab_tip = blocks_by_type.get("low_vocab_tip", {})
        low_vocab_content = low_vocab_tip.get("content")
        if not has_text(low_vocab_content):
            add_error(errors, f"{q_label} low_vocab_tip.content must be non-empty.")
        for term in contains_pollution(low_vocab_content):
            add_error(errors, f"{q_label} low_vocab_tip.content contains forbidden term '{term}'.")

    return errors, warnings, validated_q_nums


def format_available_ids(values):
    available = sorted(values)
    if not available:
        return "(none)"
    return ", ".join(available)


def load_papers_config(config_path):
    if not config_path.exists():
        raise ExportError(f"Config file does not exist: {config_path}")

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(
            f"Config JSON parse failed at {config_path} "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(config, dict):
        raise ExportError(f"Config file must contain a JSON object: {config_path}")

    if "papers" not in config:
        raise ExportError(f"Config file is missing required field 'papers': {config_path}")

    papers = config["papers"]
    if not isinstance(papers, dict):
        raise ExportError(f"Config field 'papers' must be an object: {config_path}")

    return config


def config_text(value, default="(missing)"):
    if isinstance(value, str) and value.strip():
        return value
    return default


def path_is_under(path, parent):
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
    except ValueError:
        return False
    return path.resolve(strict=False) != parent.resolve(strict=False)


def paths_equal(left, right):
    return left.resolve(strict=False) == right.resolve(strict=False)


def load_config_for_validation(config_path):
    errors = []
    if not config_path.exists():
        return None, [f"Config file does not exist: {config_path}"]

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [
            f"Config JSON parse failed at {config_path} "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ]

    if not isinstance(config, dict):
        errors.append(f"Config file must contain a JSON object: {config_path}")

    return config, errors


def validate_papers_config(config_path):
    errors = []
    warnings = []
    validated_papers_count = 0
    validated_sections_count = 0
    checked_path_fields = [
        "section_root",
        "review_sheet",
        "final_explanations",
        "display_json",
        "export_markdown",
        "manifest",
    ]

    config, load_errors = load_config_for_validation(config_path)
    errors.extend(load_errors)
    if errors:
        return errors, warnings, validated_papers_count, validated_sections_count, checked_path_fields

    if "version" not in config:
        errors.append("Top-level field 'version' is missing.")

    if "papers" not in config:
        errors.append("Top-level field 'papers' is missing.")
        return errors, warnings, validated_papers_count, validated_sections_count, checked_path_fields

    papers = config["papers"]
    if not isinstance(papers, dict):
        errors.append("Top-level field 'papers' must be an object.")
        return errors, warnings, validated_papers_count, validated_sections_count, checked_path_fields

    if not papers:
        errors.append("Top-level field 'papers' must not be empty.")
        return errors, warnings, validated_papers_count, validated_sections_count, checked_path_fields

    for paper_id in sorted(papers):
        if paper_id not in ALLOWED_CONFIG_PAPER_IDS:
            errors.append(
                f"Unsupported paper_id in current config validation scope: {paper_id}. "
                f"Allowed paper_id: {format_available_ids(ALLOWED_CONFIG_PAPER_IDS)}"
            )

        paper_config = papers[paper_id]
        if not isinstance(paper_config, dict):
            errors.append(f"Paper {paper_id} must be an object.")
            continue

        validated_papers_count += 1

        if not isinstance(paper_config.get("label"), str) or not paper_config.get("label").strip():
            errors.append(f"Paper {paper_id} field 'label' must be a non-empty string.")

        if "sections" not in paper_config:
            errors.append(f"Paper {paper_id} field 'sections' is missing.")
            continue

        sections = paper_config["sections"]
        if not isinstance(sections, dict):
            errors.append(f"Paper {paper_id} field 'sections' must be an object.")
            continue

        if not sections:
            errors.append(f"Paper {paper_id} field 'sections' must not be empty.")
            continue

        for section_key in sorted(sections):
            if section_key not in ALLOWED_CONFIG_SECTIONS:
                errors.append(
                    f"Unsupported section in current config validation scope: {paper_id} / {section_key}. "
                    f"Allowed section: {format_available_ids(ALLOWED_CONFIG_SECTIONS)}"
                )

            section_config = sections[section_key]
            if not isinstance(section_config, dict):
                errors.append(f"Section {paper_id} / {section_key} must be an object.")
                continue

            validated_sections_count += 1

            required_fields = ["label", *REQUIRED_SECTION_CONFIG_KEYS]
            for field in required_fields:
                if not isinstance(section_config.get(field), str) or not section_config.get(field).strip():
                    errors.append(
                        f"Section {paper_id} / {section_key} field '{field}' must be a non-empty string."
                    )

            if any(
                not isinstance(section_config.get(field), str) or not section_config.get(field).strip()
                for field in REQUIRED_SECTION_CONFIG_KEYS
            ):
                continue

            paper_root = Path("papers") / paper_id
            section_root = Path(section_config["section_root"])
            if not path_is_under(section_root, paper_root):
                errors.append(
                    f"Section {paper_id} / {section_key} section_root must be under {paper_root}: "
                    f"{section_root}"
                )

            for field in ["review_sheet", "final_explanations", "display_json", "export_markdown"]:
                field_path = Path(section_config[field])
                if not path_is_under(field_path, section_root):
                    errors.append(
                        f"Section {paper_id} / {section_key} field '{field}' must be under section_root "
                        f"{section_root}: {field_path}"
                    )

            expected_manifest = Path("papers") / paper_id / "manifests" / "source_integrity.json"
            manifest_path = Path(section_config["manifest"])
            if not paths_equal(manifest_path, expected_manifest):
                errors.append(
                    f"Section {paper_id} / {section_key} field 'manifest' must equal "
                    f"{expected_manifest}: {manifest_path}"
                )

            for field in ["review_sheet", "final_explanations", "display_json", "manifest"]:
                field_path = Path(section_config[field])
                if not field_path.exists():
                    errors.append(
                        f"Section {paper_id} / {section_key} field '{field}' path does not exist: "
                        f"{field_path}"
                    )

            export_parent = Path(section_config["export_markdown"]).parent
            if not export_parent.exists():
                errors.append(
                    f"Section {paper_id} / {section_key} field 'export_markdown' parent directory "
                    f"does not exist: {export_parent}"
                )

    return errors, warnings, validated_papers_count, validated_sections_count, checked_path_fields


def validate_config(args):
    config_path = Path(args.config)
    (
        errors,
        warnings,
        validated_papers_count,
        validated_sections_count,
        checked_path_fields,
    ) = validate_papers_config(config_path)

    if errors:
        print("ERRORS:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        if warnings:
            print("WARNINGS:", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)
        return 1

    print("OK: paper/section config validation passed.")
    print(f"config_file: {config_path}")
    print(f"validated_papers_count: {validated_papers_count}")
    print(f"validated_sections_count: {validated_sections_count}")
    print(f"allowed_papers: [{', '.join(ALLOWED_CONFIG_PAPER_IDS)}]")
    print(f"allowed_sections: [{', '.join(ALLOWED_CONFIG_SECTIONS)}]")
    print(f"checked_path_fields: {', '.join(checked_path_fields)}")
    print(f"errors_count: {len(errors)}")
    print(f"warnings_count: {len(warnings)}")
    print(
        "Note: validate-config checks config structure and path references only. "
        "It does not validate display JSON content or source integrity hashes."
    )
    return 0


def list_supported_papers(args):
    config_path = Path(args.config)
    config = load_papers_config(config_path)
    papers = config["papers"]
    warnings = []

    print(f"Config: {config_path}")
    print()
    print("Supported papers:")

    if not papers:
        print("(none)")
    else:
        for paper_id in sorted(papers):
            paper_config = papers[paper_id]
            if not isinstance(paper_config, dict):
                warnings.append(f"paper {paper_id}: config entry must be an object.")
                print(f"- {paper_id}: (invalid paper config)")
                continue

            paper_label = config_text(paper_config.get("label"), "(no label)")
            print(f"- {paper_id}: {paper_label}")

            sections = paper_config.get("sections")
            if not isinstance(sections, dict):
                warnings.append(f"paper {paper_id}: missing or invalid sections object.")
                print("  sections: (missing or invalid)")
                continue

            if not sections:
                warnings.append(f"paper {paper_id}: sections object is empty.")
                print("  sections: (none)")
                continue

            print("  sections:")
            for section_key in sorted(sections):
                section_config = sections[section_key]
                if not isinstance(section_config, dict):
                    warnings.append(
                        f"paper {paper_id}, section {section_key}: config entry must be an object."
                    )
                    print(f"  - {section_key}: (invalid section config)")
                    continue

                section_label = config_text(section_config.get("label"), "(no label)")
                print(f"  - {section_key}: {section_label}")
                print(f"    section_root: {config_text(section_config.get('section_root'))}")
                print(f"    display_json: {config_text(section_config.get('display_json'))}")
                print(f"    export_markdown: {config_text(section_config.get('export_markdown'))}")
                print(f"    manifest: {config_text(section_config.get('manifest'))}")

                missing_keys = [
                    key for key in ["display_json", "export_markdown", "manifest"]
                    if not isinstance(section_config.get(key), str)
                    or not section_config.get(key).strip()
                ]
                if missing_keys:
                    warnings.append(
                        f"paper {paper_id}, section {section_key}: missing required display/list path key(s): "
                        f"{', '.join(missing_keys)}."
                    )

    print()
    print(
        "Note: listed entries are configured samples. Validation rules and data readiness "
        "still determine actual workflow support."
    )

    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    return 0


def resolve_section_paths(paper_id, section, config_path=None):
    config_path = Path(config_path or DEFAULT_PAPERS_CONFIG_PATH)
    config = load_papers_config(config_path)
    papers = config["papers"]

    if paper_id not in papers:
        raise ExportError(
            f"Unknown paper_id in config: {paper_id}. "
            f"Available paper_id: {format_available_ids(papers.keys())}"
        )

    paper_config = papers[paper_id]
    if not isinstance(paper_config, dict):
        raise ExportError(f"Config entry for paper_id {paper_id} must be an object.")

    sections = paper_config.get("sections")
    if not isinstance(sections, dict):
        raise ExportError(f"Config entry for paper_id {paper_id} must contain a 'sections' object.")

    if section not in sections:
        raise ExportError(
            f"Unknown section in config for paper_id {paper_id}: {section}. "
            f"Available section: {format_available_ids(sections.keys())}"
        )

    section_config = sections[section]
    if not isinstance(section_config, dict):
        raise ExportError(
            f"Config entry for paper_id {paper_id}, section {section} must be an object."
        )

    missing_keys = [
        key for key in REQUIRED_SECTION_CONFIG_KEYS
        if key not in section_config or not isinstance(section_config[key], str) or not section_config[key].strip()
    ]
    if missing_keys:
        raise ExportError(
            f"Config entry for paper_id {paper_id}, section {section} is missing required path key(s): "
            f"{', '.join(missing_keys)}"
        )

    return {
        "section_root": Path(section_config["section_root"]),
        "review_sheet_path": Path(section_config["review_sheet"]),
        "final_explanations_path": Path(section_config["final_explanations"]),
        "display_json_path": Path(section_config["display_json"]),
        "export_markdown_path": Path(section_config["export_markdown"]),
        "manifest_path": Path(section_config["manifest"]),
    }


def resolve_paper_section_args(args, command_name):
    if args.paper_id and not args.section:
        raise ExportError(f"{command_name} requires --section when --paper-id is provided.")
    if args.section and not args.paper_id:
        raise ExportError(f"{command_name} requires --paper-id when --section is provided.")
    if not args.paper_id and not args.section:
        raise ExportError(
            f"{command_name} requires either explicit path arguments, "
            "or both --paper-id and --section."
        )

    return resolve_section_paths(args.paper_id, args.section, args.config)


def resolve_validate_input_path(args):
    has_input = args.input is not None
    has_paper_section = args.paper_id is not None or args.section is not None

    if has_input and has_paper_section:
        raise ExportError(
            "Do not mix --input with --paper-id/--section for validate-reading-display."
        )

    if has_input:
        return Path(args.input)

    paths = resolve_paper_section_args(args, "validate-reading-display")
    return paths["display_json_path"]


def resolve_export_paths(args):
    has_input = args.input is not None
    has_output = args.output is not None
    has_explicit_path = has_input or has_output
    has_paper_section = args.paper_id is not None or args.section is not None

    if has_explicit_path and has_paper_section:
        raise ExportError(
            "Do not mix --input/--output with --paper-id/--section for export-reading-display."
        )

    if has_explicit_path:
        if not has_input:
            raise ExportError(
                "export-reading-display requires --input when --output is provided."
            )
        if not has_output:
            raise ExportError(
                "export-reading-display requires --output when --input is provided."
            )
        return Path(args.input), Path(args.output)

    paths = resolve_paper_section_args(args, "export-reading-display")
    return paths["display_json_path"], paths["export_markdown_path"]


def export_reading_display(args):
    input_path, output_path = resolve_export_paths(args)

    data = load_display_json(input_path)
    validate_display_json(data)
    markdown = render_markdown(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8", newline="\n")

    print(f"OK: exported Reading Section C display Markdown to {output_path}")
    return 0


def validate_reading_display(args):
    input_path = resolve_validate_input_path(args)

    try:
        data = load_display_json(input_path)
    except ExportError as exc:
        print("ERRORS:", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    errors, warnings, validated_q_nums = validate_reading_display_data(data)
    if errors:
        print("ERRORS:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        if warnings:
            print("WARNINGS:", file=sys.stderr)
            for warning in warnings:
                print(f"- {warning}", file=sys.stderr)
        return 1

    print(
        "OK: Reading Section C display JSON validation passed "
        f"for q_nums {validated_q_nums}. "
        f"rules={len(VALIDATION_RULE_IDS)}, warnings={len(warnings)}"
    )
    return 0


def load_source_integrity_manifest(manifest_path):
    if not manifest_path.exists():
        raise ExportError(f"Manifest file does not exist: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(
            f"Manifest JSON parse failed at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(manifest, dict):
        raise ExportError("Manifest must be a JSON object.")

    files = manifest.get("files")
    if not isinstance(files, list):
        raise ExportError("Manifest must contain a 'files' list.")

    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise ExportError(f"Manifest entry files[{index}] must be an object.")
        if "path" not in entry:
            raise ExportError(f"Manifest entry files[{index}] is missing required field: path.")
        if "sha256" not in entry:
            raise ExportError(f"Manifest entry files[{index}] is missing required field: sha256.")
        if not isinstance(entry["path"], str) or not entry["path"].strip():
            raise ExportError(f"Manifest entry files[{index}].path must be non-empty text.")
        if not isinstance(entry["sha256"], str) or not entry["sha256"].strip():
            raise ExportError(f"Manifest entry files[{index}].sha256 must be non-empty text.")

    return manifest


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_source_integrity_errors(manifest_path):
    try:
        manifest = load_source_integrity_manifest(manifest_path)
    except ExportError as exc:
        return [str(exc)]

    errors = []
    for entry in manifest["files"]:
        source_path = Path(entry["path"])
        expected_sha256 = entry["sha256"].lower()

        if not source_path.exists():
            errors.append(f"{entry['path']}: missing file")
            continue

        actual_sha256 = file_sha256(source_path)
        if actual_sha256 != expected_sha256:
            errors.append(
                f"{entry['path']}: hash mismatch expected={expected_sha256} actual={actual_sha256}"
            )

    return errors


def validate_reading_display_path_errors(display_json_path):
    try:
        data = load_display_json(display_json_path)
    except ExportError as exc:
        return [str(exc)]

    errors, warnings, validated_q_nums = validate_reading_display_data(data)
    return errors


def check_source_integrity(args):
    manifest_path = Path(args.manifest)
    manifest = load_source_integrity_manifest(manifest_path)
    failures = []
    missing_count = 0
    passed_count = 0

    for entry in manifest["files"]:
        source_path = Path(entry["path"])
        expected_sha256 = entry["sha256"].lower()

        if not source_path.exists():
            missing_count += 1
            failures.append((entry["path"], "missing file"))
            continue

        actual_sha256 = file_sha256(source_path)
        if actual_sha256 != expected_sha256:
            failures.append(
                (
                    entry["path"],
                    f"hash mismatch expected={expected_sha256} actual={actual_sha256}",
                )
            )
            continue

        passed_count += 1

    failed_count = len(failures) - missing_count
    checked_files = len(manifest["files"])
    integrity_status = "passed" if not failures else "failed"

    print(f"integrity_status: {integrity_status}")
    print(f"manifest_file: {manifest_path}")
    print(f"checked_files: {checked_files}")
    print(f"passed_count: {passed_count}")
    print(f"failed_count: {failed_count}")
    print(f"missing_count: {missing_count}")

    if failures:
        print("ERRORS:", file=sys.stderr)
        for path, reason in failures:
            print(f"- {path}: {reason}", file=sys.stderr)
        return 1

    return 0


def doctor(args):
    config_path = Path(args.config)
    print(f"Doctor check for {args.paper_id} / {args.section}")

    overall_errors = []
    statuses = {
        "validate-config": "pending",
        "list-supported-papers": "pending",
        "check-source-integrity": "pending",
        "validate-reading-display": "pending",
    }

    config_errors, config_warnings, _, _, _ = validate_papers_config(config_path)
    if config_errors:
        statuses["validate-config"] = "failed"
        overall_errors.extend(f"validate-config: {error}" for error in config_errors)
    else:
        statuses["validate-config"] = "passed"

    paths = None
    if statuses["validate-config"] == "passed":
        try:
            paths = resolve_section_paths(args.paper_id, args.section, config_path)
        except ExportError as exc:
            statuses["list-supported-papers"] = "failed"
            overall_errors.append(f"list-supported-papers: {exc}")
        else:
            statuses["list-supported-papers"] = "passed"
    else:
        statuses["list-supported-papers"] = "skipped"

    if paths is not None:
        source_errors = check_source_integrity_errors(paths["manifest_path"])
        if source_errors:
            statuses["check-source-integrity"] = "failed"
            overall_errors.extend(f"check-source-integrity: {error}" for error in source_errors)
        else:
            statuses["check-source-integrity"] = "passed"
    else:
        statuses["check-source-integrity"] = "skipped"

    if paths is not None and statuses["check-source-integrity"] == "passed":
        display_errors = validate_reading_display_path_errors(paths["display_json_path"])
        if display_errors:
            statuses["validate-reading-display"] = "failed"
            overall_errors.extend(f"validate-reading-display: {error}" for error in display_errors)
        else:
            statuses["validate-reading-display"] = "passed"
    else:
        statuses["validate-reading-display"] = "skipped"

    for step in [
        "validate-config",
        "list-supported-papers",
        "check-source-integrity",
        "validate-reading-display",
    ]:
        print(f"- {step}: {statuses[step]}")

    overall_status = "failed" if overall_errors else "passed"
    print(f"overall_status: {overall_status}")

    if config_warnings:
        print("WARNINGS:", file=sys.stderr)
        for warning in config_warnings:
            print(f"- {warning}", file=sys.stderr)

    if overall_errors:
        print("ERRORS:", file=sys.stderr)
        for error in overall_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="CET-6 review helper CLI for Reading Section C display workflows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "export-reading-display",
        description="Export Reading Section C display JSON to Markdown.",
        help="Export Reading Section C display JSON to Markdown.",
    )
    export_parser.add_argument(
        "--input",
        required=False,
        help="Path to Reading Section C display JSON input file.",
    )
    export_parser.add_argument(
        "--output",
        required=False,
        help="Path to Markdown output file.",
    )
    export_parser.add_argument(
        "--paper-id",
        required=False,
        help="Paper id for configured paper/section path resolution.",
    )
    export_parser.add_argument(
        "--section",
        required=False,
        help="Section id for configured paper/section path resolution.",
    )
    export_parser.add_argument(
        "--config",
        required=False,
        default=str(DEFAULT_PAPERS_CONFIG_PATH),
        help="Path to paper/section path configuration JSON.",
    )
    export_parser.set_defaults(func=export_reading_display)

    validate_parser = subparsers.add_parser(
        "validate-reading-display",
        description="Validate Reading Section C display JSON without writing files.",
        help="Validate Reading Section C display JSON without writing files.",
    )
    validate_parser.add_argument(
        "--input",
        required=False,
        help="Path to Reading Section C display JSON input file.",
    )
    validate_parser.add_argument(
        "--paper-id",
        required=False,
        help="Paper id for configured paper/section path resolution.",
    )
    validate_parser.add_argument(
        "--section",
        required=False,
        help="Section id for configured paper/section path resolution.",
    )
    validate_parser.add_argument(
        "--config",
        required=False,
        default=str(DEFAULT_PAPERS_CONFIG_PATH),
        help="Path to paper/section path configuration JSON.",
    )
    validate_parser.set_defaults(func=validate_reading_display)

    integrity_parser = subparsers.add_parser(
        "check-source-integrity",
        description="Check stable source files against a sha256 manifest.",
        help="Check stable source files against a sha256 manifest.",
    )
    integrity_parser.add_argument(
        "--manifest",
        required=True,
        help="Path to source integrity manifest JSON.",
    )
    integrity_parser.set_defaults(func=check_source_integrity)

    list_parser = subparsers.add_parser(
        "list-supported-papers",
        description="List paper/section entries configured in configs/papers.json.",
        help="List configured paper/section entries.",
    )
    list_parser.add_argument(
        "--config",
        required=False,
        default=str(DEFAULT_PAPERS_CONFIG_PATH),
        help="Path to paper/section path configuration JSON.",
    )
    list_parser.set_defaults(func=list_supported_papers)

    config_parser = subparsers.add_parser(
        "validate-config",
        description="Validate paper/section config structure and path references.",
        help="Validate paper/section config structure.",
    )
    config_parser.add_argument(
        "--config",
        required=False,
        default=str(DEFAULT_PAPERS_CONFIG_PATH),
        help="Path to paper/section path configuration JSON.",
    )
    config_parser.set_defaults(func=validate_config)

    doctor_parser = subparsers.add_parser(
        "doctor",
        description="Run read-only health checks for a configured paper/section sample.",
        help="Run read-only paper/section health checks.",
    )
    doctor_parser.add_argument(
        "--paper-id",
        required=True,
        help="Paper id for configured paper/section health checks.",
    )
    doctor_parser.add_argument(
        "--section",
        required=True,
        help="Section id for configured paper/section health checks.",
    )
    doctor_parser.add_argument(
        "--config",
        required=False,
        default=str(DEFAULT_PAPERS_CONFIG_PATH),
        help="Path to paper/section path configuration JSON.",
    )
    doctor_parser.set_defaults(func=doctor)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
