# Directory Structure Plan

## A. Purpose

Milestone 3A designs a future directory structure and naming convention for paper, section, and stage management.

This is a design-only milestone. It does not move files, modify JSON data, change CLI behavior, refresh manifests, or regenerate Markdown exports.

The goal is to prepare the project for later expansion across:

- additional years, such as 2024 and 2023
- additional paper sets
- Listening
- Reading Section A, Section B, and Section C
- Translation
- Writing

## B. Current Problem

The current project layout is organized mostly by horizontal technical layers:

- `data/`
- `reports/`
- `exports/`
- `scripts/`
- `docs/`
- `manifests/`

This works for the current narrow sample, because the stable workflow mainly covers 2025 June Set 1 Reading Section C.

As more years, paper sets, sections, and processing stages are added, files will become increasingly scattered across these top-level folders. Related files for one paper and one section will be separated into multiple directories, and the project will depend more heavily on long filenames to identify what each file belongs to.

Current identification is mostly encoded in filenames, such as:

- paper: `2025_06_set1`
- section: `reading_section_c`
- stage: `review_sheet`, `final_explanations`, `display`, `report`, or `manifest`

This is acceptable for a small sample, but long-term maintenance will become harder because paper, section, and stage information is not represented by the directory structure itself.

## C. Future Recommended Structure

The recommended future structure is paper-first, then section-first, then stage-first.

Example target layout:

```text
papers/
  2025_06_set1/
    raw_pdfs/
    extracted_text/
    structured/
    reading/
      section_a/
      section_b/
      section_c/
        analysis/
        final/
        display/
        exports/
        reports/
    listening/
      analysis/
      final/
      display/
      exports/
      reports/
    translation_writing/
      translation/
        analysis/
        final/
        display/
        exports/
        reports/
      writing/
        analysis/
        final/
        display/
        exports/
        reports/
    manifests/
```

Design notes:

- `papers/` groups all paper-specific material.
- `2025_06_set1/` is the paper root and should contain all files for that paper.
- `raw_pdfs/`, `extracted_text/`, and `structured/` represent paper-level source stages.
- `reading/section_a/`, `reading/section_b/`, and `reading/section_c/` separate reading tasks by subtype.
- Each section may then contain stage directories such as `analysis/`, `final/`, `display/`, `exports/`, and `reports/`.
- `listening/` is section-level, because it is not naturally split into Reading A/B/C.
- `translation_writing/` may contain `translation/` and `writing/` subdirectories so those two output types can share a broader exam section while still keeping their own stages.
- `manifests/` under each paper keeps integrity records close to the files they describe.

## D. Naming Convention

### paper_id

Use a stable, lowercase, underscore-separated identifier:

```text
2025_06_set1
```

Pattern:

```text
YYYY_MM_setN
```

Examples:

- `2025_06_set1`
- `2024_12_set2`
- `2023_06_set1`

### section

Use a stable section key that can be used in CLI arguments, config files, and filenames:

```text
reading_section_c
reading_section_b
reading_section_a
listening
translation
writing
```

Recommended mapping to future folders:

| section | future folder |
| --- | --- |
| `reading_section_a` | `papers/<paper_id>/reading/section_a/` |
| `reading_section_b` | `papers/<paper_id>/reading/section_b/` |
| `reading_section_c` | `papers/<paper_id>/reading/section_c/` |
| `listening` | `papers/<paper_id>/listening/` |
| `translation` | `papers/<paper_id>/translation_writing/translation/` |
| `writing` | `papers/<paper_id>/translation_writing/writing/` |

### stage

Use a small controlled stage vocabulary:

```text
raw
extracted
structured
analysis
final
display
export
report
```

Recommended meaning:

| stage | meaning |
| --- | --- |
| `raw` | original source files, such as PDFs |
| `extracted` | extracted text or OCR output |
| `structured` | normalized structured source data |
| `analysis` | intermediate analysis, candidates, review support, or review sheets |
| `final` | final explanations or final reviewed content |
| `display` | display-layer JSON for learner-facing review |
| `export` | generated external formats, such as Markdown |
| `report` | milestone reports, validation reports, and completion reports |

## E. Current-to-Future Mapping

This table is a planning reference only. No file should be moved during Milestone 3A.

| current file | future proposed file |
| --- | --- |
| `data/analysis/reading_section_c_2025_06_set1_review_sheet.json` | `papers/2025_06_set1/reading/section_c/analysis/review_sheet.json` |
| `data/final/reading_section_c_2025_06_set1_final_explanations.json` | `papers/2025_06_set1/reading/section_c/final/final_explanations.json` |
| `data/display/reading_section_c_2025_06_set1_display.json` | `papers/2025_06_set1/reading/section_c/display/display.json` |
| `exports/reading_section_c_2025_06_set1_display.md` | `papers/2025_06_set1/reading/section_c/exports/display.md` |
| `reports/reading_section_c_2l_completion_report.md` | `papers/2025_06_set1/reading/section_c/reports/2l_completion_report.md` |
| `manifests/source_integrity_2025_06_set1.json` | `papers/2025_06_set1/manifests/source_integrity.json` |

Alternative future naming is possible, but the recommended structure intentionally removes repeated `reading_section_c_2025_06_set1` prefixes after the paper and section are already encoded in folders.

## F. Migration Principles

Migration should happen in a later milestone, not in Milestone 3A.

Recommended migration principles:

- Copy files into the new structure first.
- Do not delete old files during the first migration pass.
- After copying, run `validate-reading-display` against the migrated display data.
- Then run `export-reading-display` from the migrated display data.
- Finally refresh the `source_integrity` manifest only after the migrated paths and outputs have been verified.
- Keep all old paths until the new paths pass validation and export checks.
- Consider cleanup only after old-path and new-path behavior is proven equivalent.

## G. CLI and Config Direction

Future CLI support should make paper, section, and stage explicit instead of requiring every path to be passed manually or inferred from filenames.

Possible future options:

```text
--paper-id 2025_06_set1
--section reading_section_c
--stage display
```

Another acceptable direction is a small config file that maps:

- `paper_id`
- `section`
- `stage`
- source path
- output path
- manifest path

Milestone 3A does not choose the final CLI implementation. It only defines the naming vocabulary that later CLI or config work should use.

## H. Later Milestones

### Milestone 3B: Copy Current Sample to New Directory Structure

Copy the current 2025 June Set 1 Reading Section C sample files into the proposed `papers/2025_06_set1/reading/section_c/` layout.

Do not delete old files.

### Milestone 3C: Add CLI Support for Paper, Section, and Stage

Update CLI support for explicit `--paper-id`, `--section`, and `--stage` options, or introduce a configuration file that provides the same information.

Existing CLI behavior should remain available until the new path workflow is validated.

### Milestone 3D: Refresh Manifest and Verify Path Consistency

Refresh the source-integrity manifest after migrated files have been validated.

Compare old-path and new-path behavior to confirm that validation, export, and manifest checks remain consistent.

