# Analysis Method

This document describes the analysis method behind the current CET-6 reading workflow. It is a project method note, not a claim that all CET-6 modules are supported.

## Pipeline

The current workflow can be summarized as:

```text
source text
  -> structured source JSON
  -> evidence candidates
  -> human review sheet
  -> final explanations
  -> display JSON
  -> Markdown or app-facing review material
```

## Stage 1: Structured Source Data

The project first turns source material into structured JSON. Existing scripts and schemas focus on a sample paper and preserve missing or uncertain fields instead of silently filling them.

Important practices:

- keep raw extraction separate from reviewed output
- record OCR quality where relevant
- use `null` or empty arrays for unavailable fields
- write data-quality reports for missing or unstable fields

## Stage 2: Evidence Candidates

Candidate generation tries to find useful answer evidence, keyword overlap, paraphrase candidates, and possible distractors.

Candidate output is not final. It exists to support review.

For multiple-choice reading questions, useful candidates include:

- answer evidence
- option-to-evidence phrase matches
- question type hints
- distractor reasons
- low-vocabulary location hints

For paragraph-matching questions, useful candidates include:

- statement keywords
- matched paragraph expressions
- paraphrase pairs
- paragraph-level evidence
- distractor paragraph candidates

## Stage 3: Human Review

The review layer is central to the project. A candidate may look plausible but still be wrong, incomplete, or too weak for learner-facing output.

The review sheet should answer:

- Is the evidence enough?
- Is the answer path understandable?
- Are the paraphrases real and useful?
- Are distractor warnings tied to the text?
- Is the item ready for final explanation?

## Stage 4: Final Explanation

Final explanations should use reviewed material only. They should avoid inventing evidence or turning uncertain candidates into polished claims.

A good final explanation should show:

- the correct answer
- the supporting evidence
- the location method
- the key paraphrase or logic signal
- why tempting alternatives fail
- a low-vocabulary path when possible

## Stage 5: Display And Review

Display JSON and Markdown exports are meant for learner-facing review. They should hide raw candidate uncertainty and present a clean answer path.

Future PWA integration can use the same structure to save:

- wrong questions
- mistake causes
- high-yield vocabulary
- paraphrase pairs
- review schedule
- spaced repetition state

## Current Limitations

- Current work is reading-focused.
- Existing config validation is intentionally narrow.
- Some artifacts are sample-specific.
- Some historical generated text may contain encoding noise.
- The PWA workflow is planned, not complete in this repository.

