import argparse
import json
import sys
from pathlib import Path


FORBIDDEN_Q_NUMS = {52, 55}
DEFAULT_CONTEXT_NOTE = "无额外上下文证据"
DEFAULT_PARAPHRASE_NOTE = "无已确认同义替换"


class ExportError(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export Reading Section C display JSON to Markdown."
    )
    parser.add_argument("--input", required=True, help="Path to display JSON input file.")
    parser.add_argument("--output", required=True, help="Path to Markdown output file.")
    return parser.parse_args()


def load_display_json(input_path):
    if not input_path.exists():
        raise ExportError(f"Input file does not exist: {input_path}")

    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(
            f"Failed to parse JSON in {input_path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def require_display_blocks(question):
    q_num = question.get("q_num", "unknown")
    blocks = question.get("display_blocks")
    if blocks is None:
        raise ExportError(f"Question Q{q_num} is missing display_blocks.")
    if not isinstance(blocks, list):
        raise ExportError(f"Question Q{q_num} display_blocks must be a list.")
    return {block.get("type"): block for block in blocks if isinstance(block, dict)}


def require_block(blocks_by_type, block_type, q_num):
    block = blocks_by_type.get(block_type)
    if block is None:
        raise ExportError(f"Question Q{q_num} is missing required display block: {block_type}.")
    return block


def render_list_items(lines, items):
    for item in items:
        lines.append(f"- {item}")


def render_question(question):
    q_num = question.get("q_num")
    blocks = require_display_blocks(question)

    answer = require_block(blocks, "answer", q_num)
    explanation = require_block(blocks, "explanation", q_num)
    evidence = require_block(blocks, "evidence", q_num)
    location_method = require_block(blocks, "location_method", q_num)
    paraphrase = require_block(blocks, "paraphrase", q_num)
    low_vocab_tip = require_block(blocks, "low_vocab_tip", q_num)

    options = question.get("options", {})
    option_order = question.get("option_order", [])

    lines = [
        f"## Q{q_num}",
        "",
        "### 题目",
        str(question.get("question", "")),
        "",
        "### 选项",
    ]

    for option_key in option_order:
        lines.append(f"- {option_key}. {options.get(option_key, '')}")

    lines.extend(
        [
            "",
            "### 正确答案",
            str(answer.get("content", question.get("correct_answer", ""))),
            "",
            "### 答案解析",
            str(explanation.get("content", "")),
            "",
            "### 原文出处",
        ]
    )
    render_list_items(lines, evidence.get("items", []))

    lines.extend(["", "### 上下文证据"])
    context_items = evidence.get("context_items", [])
    if context_items:
        render_list_items(lines, context_items)
    else:
        lines.append(f"上下文证据：{DEFAULT_CONTEXT_NOTE}")

    lines.extend(["", "### 做题时怎么定位"])
    render_list_items(lines, location_method.get("items", []))

    lines.extend(["", "### 同义替换"])
    paraphrase_items = paraphrase.get("items", [])
    if paraphrase_items:
        for item in paraphrase_items:
            if isinstance(item, dict):
                evidence_phrase = item.get("evidence_phrase", "")
                option_key = item.get("option_key", "")
                option_phrase = item.get("option_phrase", "")
                note = item.get("confirmed_note_zh", "")
                lines.append(f"- {evidence_phrase} -> {option_key}. {option_phrase}：{note}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append(f"同义替换：{DEFAULT_PARAPHRASE_NOTE}")

    lines.extend(
        [
            "",
            "### 低词汇量提示",
            str(low_vocab_tip.get("content", "")),
            "",
        ]
    )
    return "\n".join(lines)


def render_markdown(data):
    questions = data.get("questions", [])
    if not isinstance(questions, list):
        raise ExportError("Input JSON field 'questions' must be a list.")

    rendered = ["# Reading Section C Display Export", ""]
    for question in questions:
        q_num = question.get("q_num")
        if q_num in FORBIDDEN_Q_NUMS:
            continue
        rendered.append(render_question(question))

    return "\n".join(rendered).rstrip() + "\n"


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        data = load_display_json(input_path)
        markdown = render_markdown(data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8", newline="\n")
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
