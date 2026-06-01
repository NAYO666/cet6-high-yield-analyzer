# Copyright Notes

This repository is intended to explore a learning workflow, not to redistribute exam materials.

## Intended Use

The intended use is:

- a learner legally obtains CET-6 or practice material
- the learner imports text locally
- the tool analyzes that user-provided text
- the learner reviews the generated material privately

## What Should Not Be Published

Do not publish or contribute:

- full exam papers
- answer PDFs
- extracted full-text papers
- long answer explanations copied from copyrighted sources
- commercial question-bank content
- large passage collections from third-party materials

## Public Examples

Public examples should be:

- fictional
- synthetic
- heavily shortened
- user-owned
- or otherwise safe to redistribute

Examples in `examples/` are intentionally mock examples. They are designed to show the analysis shape without copying real CET-6 content.

## Repository Hygiene Before Public Release

Before publishing the repository publicly, review whether these directories contain copyrighted or sensitive material:

- `data/raw_pdfs/`
- `data/extracted_text/`
- `data/structured/`
- `papers/*/reading/*/display/`
- `papers/*/reading/*/exports/`
- generated reports that quote long source passages

Depending on the release goal, those files may need to be removed, replaced with mock data, or kept out of the public repository.

## Language To Use

Recommended wording:

- user-provided text
- local-first analysis
- experimental workflow
- public-safe mock examples
- no bundled question bank

Avoid wording that suggests the repository contains an official dataset or complete CET-6 content.
