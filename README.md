# CET-6 High-Yield Analyzer

An experimental, early-stage toolkit for turning user-provided CET-6 practice text into evidence-based review material.

> Learn fewer words, but learn the words that matter most.

## Why This Project Exists

Many CET-6 learners do not need another long vocabulary list. They need a way to notice which words, phrases, and logic signals actually help them choose the right answer in real exam-style questions.

This project explores a learning workflow for that problem:

- locate answer evidence in a passage
- connect question wording with source wording
- identify high-yield vocabulary by its role in solving the question
- record paraphrases and distractor traps
- turn approved analysis into review material
- eventually connect those review items to a spaced-review PWA

The project is not meant to replace human judgment. The current workflow is deliberately human-reviewable: candidate evidence and draft explanations should be checked before they are treated as learner-facing output.

## Learning Hypothesis

The core hypothesis is simple:

> A learner with limited vocabulary can improve their exam workflow by studying fewer items, if those items are selected because they help locate evidence, recognize paraphrases, avoid distractors, or recover from repeated mistakes.

In this project, a "high-yield" word is not just a frequent word. It may be high-yield because it:

- appears in a question stem as a locator
- links an option to source evidence
- signals contrast, cause, concession, or inference
- appears in a common paraphrase pair
- makes a wrong option look tempting
- explains why a learner missed a question

## Core Ideas

- **Evidence before explanation**: answer explanations should point back to concrete source evidence.
- **Paraphrase tracking**: many CET-6 reading answers depend on recognizing rewritten meaning, not exact word matching.
- **Low-vocabulary strategy**: the output should help learners solve with partial understanding, not shame them for missing words.
- **Human-reviewable pipeline**: generated candidates are not final until reviewed.
- **Local-first study material**: users should be able to import legally obtained text and keep their own review data.
- **No bundled question bank**: this repository is not intended to distribute complete CET-6 papers or answer PDFs.

## Current Status

This is an **experimental / early-stage** repository.

Current stable work is centered on a small sample workflow for CET-6 reading analysis:

- Reading Section C sample workflow with reviewed final/display output for selected questions.
- Reading Section B sample workflow with statement-to-paragraph analysis, review, final output, and display/export artifacts.
- A paper-first directory structure under `papers/`.
- CLI commands for config checks, source integrity checks, display validation, and Markdown export.
- Existing documentation of project status, path strategy, CLI usage, and Section B design.

Important boundaries:

- The CLI config currently registers only `2025_06_set1 / reading_section_c`.
- Existing Section B artifacts are present, but broader CLI registration/validation is still future work.
- Reading Section A, Listening, Translation, Writing, and full multi-paper support are not complete.
- The wrong-question review PWA is a planned integration direction, not a complete module in this repository.
- Some historical artifacts may contain encoding noise from earlier extraction/export stages.

## Current Features

- Parse and structure a limited CET-6 sample into JSON.
- Track OCR quality and missing fields for answer-derived content.
- Generate reading evidence candidates for review.
- Maintain human review sheets before final learner-facing output.
- Store final explanations and display JSON.
- Export display-ready reading analysis to Markdown.
- Check source integrity for selected stable artifacts.
- Document sample scope and stop conditions for each milestone.

## Planned Features

- Public-safe sample package using only fictional or user-provided text.
- Cleaner schema for question-level analysis output.
- Reading Section B registration in config and validation commands.
- Reading Section A sample design.
- Aggregated reading review output across Section B and Section C.
- A local-first wrong-question review PWA for mistakes, causes, review schedule, and spaced repetition.
- Better encoding cleanup and public-release hygiene.
- CI checks for schema validation and public examples.

## Example Output

The real project artifacts may contain copyrighted exam text and should not be copied into public examples. The example below is fictional and shortened:

```json
{
  "question_id": "sample-q1",
  "answer": "B",
  "evidence": [
    {
      "source_span": "the city reduced waste by reusing materials",
      "supports": "B"
    }
  ],
  "high_yield_items": [
    {
      "text": "reduced",
      "role": "evidence_word",
      "why_it_matters": "Links the option phrase 'cut down' to the passage."
    }
  ],
  "paraphrases": [
    {
      "source": "reduced waste",
      "question_or_option": "cut down waste"
    }
  ],
  "distractor_traps": [
    {
      "option": "C",
      "trap": "Mentions recycling, but not the specific result asked by the question."
    }
  ],
  "low_vocab_path": [
    "Find the repeated topic word: waste.",
    "Match reduced with cut down.",
    "Reject options that mention the topic but not the result."
  ]
}
```

More mock examples are available in `examples/`.

## How It Works

The current workflow is organized around review stages:

```text
user-provided text
  -> structured source data
  -> evidence candidates
  -> human review sheet
  -> final explanation
  -> display JSON / Markdown export
  -> review material for future PWA use
```

The main CLI entry point is:

```bash
python scripts/cet6_tool.py doctor --paper-id 2025_06_set1 --section reading_section_c
```

Other useful commands are documented in `docs/cli_usage.md`.

## Copyright Notes

This project should not be used to publish or redistribute complete CET-6 papers, answer PDFs, extracted full-text papers, or long copyrighted passages.

The intended use is:

- users legally obtain their own exam/practice material
- users import text locally
- the tool analyzes that user-provided text
- public examples use mock, fictional, or heavily shortened material

See `docs/copyright-notes.md` for the public-release boundary.

For privacy and future PWA storage boundaries, see `docs/privacy-and-local-storage.md`.

## Who This Is For

This project may be useful for:

- CET-6 learners who want a more targeted review workflow
- teachers who want human-checkable evidence and paraphrase notes
- developers exploring learning tools for exam-oriented language study
- contributors interested in local-first review tools and schema design

It is probably not useful if you need a full exam-content database, a finished production app, or a promise of score gains.

## Roadmap

See `ROADMAP.md` for current priorities. The short version:

- stabilize public documentation and mock examples
- keep copyrighted materials out of public examples
- cleanly define question-level analysis schema
- expand reading support one small reviewed sample at a time
- connect analysis output to a wrong-question review PWA

## Contributing

Contributions are welcome if they keep the project honest about scope and copyright boundaries. Good first contributions include documentation cleanup, schema improvements, mock examples, tests for public examples, and small validation improvements.

Please read `CONTRIBUTING.md` before contributing.

## License

This project uses the MIT License. See `LICENSE`.

The license applies to original project code, documentation, schemas, and mock examples. It does not grant rights to redistribute third-party exam papers, answer PDFs, extracted full-text materials, or other copyrighted content used locally with the project.
