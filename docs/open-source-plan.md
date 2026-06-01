# Open Source Plan

This document outlines what the project needs before it can be presented as a clean open-source learning project.

## Current Strengths

- The project has a clear learning question: how to identify high-yield language items from exam-style reading questions.
- Existing milestone reports document boundaries and stop conditions.
- The workflow separates candidates, review sheets, final explanations, and display output.
- Source integrity checks exist for selected stable artifacts.
- The current docs already avoid claiming broad support.

## Public-Release Checklist

- Add a clear `LICENSE` file.
- Remove or exclude complete copyrighted exam PDFs.
- Remove or exclude extracted full-text copyrighted material.
- Replace public examples with fictional or safe sample content.
- Add schema validation for `examples/sample_analysis.json`.
- Decide whether historical reports that quote source text should remain public.
- Add a short public demo that does not require copyrighted inputs.
- Add issue templates for bug reports, docs improvements, and data-boundary concerns.
- Add CI checks for formatting, schema validity, and CLI smoke tests.

## Documentation Goals

Public documentation should explain:

- the learning hypothesis
- the evidence-first workflow
- why high-yield vocabulary is role-based
- what is currently implemented
- what remains experimental
- how copyright boundaries are handled

## PWA Integration Direction

The wrong-question review PWA should be treated as a companion direction until code and data contracts are present in the repository.

Potential PWA data objects:

- question analysis
- mistake record
- mistake cause
- review item
- spaced-review schedule
- vocabulary/paraphrase card

The PWA should not require a bundled copyrighted question bank. It should store user-created or user-imported review data.

## Codex For Open Source Readiness

If the project is later considered for an open-source support program, it will need:

- a public repository with a clear license
- copyright-safe examples
- a reproducible setup path
- clear contribution guidelines
- scoped issues suitable for contributors
- tests or validation checks
- a README that distinguishes implemented features from future plans

