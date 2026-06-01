# CET-6 Project Status and Roadmap

## A. Project Positioning

This project is a CET-6 past-paper assisted review tool for personal exam preparation.

The goal is not to imagine that AI can directly raise a score by itself. The practical goal is to turn selected real-paper materials into review assets that help with locating evidence, checking reasoning, reviewing vocabulary, and preparing more consistently.

Reading and Listening are the main long-term focus areas. The current stable samples cover the 2025 June Set 1 Reading Section C sample and the completed Reading Section B display-ready sample.

Current sample scope:

- paper: 2025 June Set 1
- section: Reading Section C
- status: sample workflow only
- included final/display/export questions: Q46, Q47, Q48, Q49, Q50, Q51, Q53, Q54
- excluded from final/display/export for now: Q52, Q55
- section: Reading Section B
- q_nums: Q36-Q45
- completion_status: completed_display_ready
- latest_completed_milestone: Milestone 5H
- registration_milestone: Milestone 5I

## B. Completed Milestones

### Milestone 1: Data Preprocessing

Completed.

Structured source data was prepared from the raw CET-6 materials so later Reading Section C analysis could work from stable JSON inputs instead of repeatedly parsing source files.

### Milestone 1.5: Answer PDF OCR Fallback

Completed.

An OCR fallback path was introduced for answer PDF content where direct text extraction was not reliable enough.

### Milestone 1.6: OCR Field Quality Labels

Completed.

OCR-related fields were given quality labels so uncertain extracted content could be identified instead of silently treated as equally reliable source text.

### Milestone 2A / 2A-Repair: Reading Section C Evidence Candidates

Completed for the current sample.

Evidence candidates were generated and repaired for 2025 June Set 1 Reading Section C. These candidates supported later review but were not treated as final approval by themselves.

### Milestone 2B: Evidence Human Review Support Layer

Completed for the current sample.

A human-review support layer was built around evidence candidates so items could be inspected and separated into approved, pending, and manual-review-only states.

### Milestone 2C / 2C-Repair: Chinese Explanation Drafts

Completed as draft material for the current sample.

Chinese explanation drafts were generated and repaired as intermediate review material. These drafts are not the same as the final explanations.

### Milestone 2D / 2D-Display-Repair: Human Review Sheet

Completed for the current sample.

The review sheet was prepared and repaired to support manual checking before final explanation and display JSON work.

### Milestone 2E / Batch 2: Final Explanation

Completed for the approved items available at that milestone.

Final explanations were created for approved questions: Q47, Q48, Q50, Q51, Q53, and Q54.

Q46 and Q49 were completed later in Milestone 2L. Q52 and Q55 remain manual-review-only and are not part of the final explanation set.

### Milestone 2F / 2F-Display-Repair: Display Layer Sample

Completed for the approved items available at that milestone.

The display JSON sample was created and repaired for Q47, Q48, Q50, Q51, Q53, and Q54.

Q46 and Q49 were added later in Milestone 2L. Q52 and Q55 remain manual-review-only and are intentionally not included in the display JSON.

### Milestone 2G: CLI Markdown Export

Completed for the current display sample.

The CLI can export the verified Reading Section C display JSON into Markdown for review.

### Milestone 2H: CLI Arguments and Directory Convention

Completed.

The CLI commands were organized around explicit input/output arguments and stable project directories such as `data/`, `exports/`, `manifests/`, `reports/`, and `docs/`.

### Milestone 2I: validate-reading-display

Completed for the current sample.

The command validates the 2025 June Set 1 Reading Section C display JSON and checks the approved display question set.

Current validation target is limited to this sample. It is not a general validator for all years, sets, or reading sections.

### Milestone 2J: check-source-integrity

Completed for the current stable files.

The command checks recorded source-integrity hashes for the current stable core files:

- review sheet JSON
- final explanations JSON
- display JSON

### Milestone 2L: Complete Q46/Q49 Human Review and Final Explanation

Completed for the current sample.

Q46 and Q49 were approved and added to final explanations, display JSON, and Markdown export. The current final/display/export question set is Q46, Q47, Q48, Q49, Q50, Q51, Q53, and Q54.

Q52 and Q55 remain manual-review-only.

### Milestone 4A: Configurable Paper/Section Path Resolution

Completed for the current sample.

The CLI paper/section path mode now resolves paths through `configs/papers.json` instead of hard-coded path construction. The config registers only the verified `2025_06_set1` / `reading_section_c` sample.

This milestone did not add support for new years, new sets, Reading Section A/B, Listening, Translation, or Writing. The validation rules remain the current Reading Section C sample rules.

### Milestone 4B: list-supported-papers CLI Command

Completed for the current sample.

The CLI now includes `list-supported-papers`, a read-only command that prints the paper and section entries currently registered in `configs/papers.json`. It helps confirm which samples are configured without running validation, export, source integrity checks, analysis, or data generation.

This milestone did not process new data and did not expand years or sections. The current config still registers only `2025_06_set1` / `reading_section_c`.

### Milestone 4C: validate-config CLI Command

Completed for the current sample.

The CLI now includes `validate-config`, a read-only command that checks `configs/papers.json` structure, current allowed paper/section scope, and key path references. It confirms that the configured sample stays within the expected `papers/2025_06_set1/...` layout and that required referenced files or export directories exist.

This milestone did not add paper or section entries, did not process new data, did not validate display JSON content, did not check source integrity hashes, and did not export Markdown. The validation scope remains limited to `2025_06_set1` / `reading_section_c`; future expansion must update the config validation rules deliberately.

### Milestone 4D: doctor CLI Command

Completed for the current sample.

The CLI now includes `doctor`, a read-only health check command for a configured paper/section sample. For `2025_06_set1` / `reading_section_c`, it runs the current config validation, confirms the paper/section is registered, checks source integrity through the configured manifest, and validates the configured Reading Section C display JSON.

This milestone did not add paper or section entries, did not process new data, did not export Markdown, did not refresh the manifest, and did not regenerate analysis.

### Milestone 5A-5I: Reading Section B Sample Completion

Completed for `2025_06_set1` Reading Section B Q36-Q45.

The Section B sample has completed the full content chain from source extraction through display/export:

```text
source_extract -> evidence_candidates -> candidate_cleanup -> review_sheet -> explanation_draft -> human_review_result -> final_explanations -> display/export
```

Completion registration:

- section: `reading_section_b`
- q_nums: Q36-Q45
- completion_status: `completed_display_ready`
- latest_completed_milestone: Milestone 5H
- registration_milestone: Milestone 5I
- display_json: `papers/2025_06_set1/reading/section_b/display/display.json`
- display_markdown: `papers/2025_06_set1/reading/section_b/exports/display.md`
- final_explanations: `papers/2025_06_set1/reading/section_b/final/final_explanations.json`

## C. Current Stable Outputs

Recommended paper-first stable files:

- `papers/2025_06_set1/reading/section_c/analysis/review_sheet.json`
- `papers/2025_06_set1/reading/section_c/final/final_explanations.json`
- `papers/2025_06_set1/reading/section_c/display/display.json`
- `papers/2025_06_set1/reading/section_c/exports/display.md`
- `papers/2025_06_set1/reading/section_b/analysis/source_extract.json`
- `papers/2025_06_set1/reading/section_b/analysis/evidence_candidates.json`
- `papers/2025_06_set1/reading/section_b/analysis/review_sheet.json`
- `papers/2025_06_set1/reading/section_b/final/human_review_result.json`
- `papers/2025_06_set1/reading/section_b/final/final_explanations.json`
- `papers/2025_06_set1/reading/section_b/display/display.json`
- `papers/2025_06_set1/reading/section_b/exports/display.md`
- `papers/2025_06_set1/manifests/source_integrity.json`

Legacy fallback files:

- `data/analysis/reading_section_c_2025_06_set1_review_sheet.json`
- `data/final/reading_section_c_2025_06_set1_final_explanations.json`
- `data/display/reading_section_c_2025_06_set1_display.json`
- `exports/reading_section_c_2025_06_set1_display.md`
- `manifests/source_integrity_2025_06_set1.json`

## D. Current Path Strategy

Milestone 3A-3D are complete, and the new paper-first path layout has been verified for the current `2025_06_set1` Reading Section C sample.

The default working structure is now:

```text
papers/2025_06_set1/reading/section_c/
```

Future workflow stages, sections, paper sets, and years should use the `papers/` structure by default.

Paper/section CLI path resolution now reads `configs/papers.json`. The current config intentionally lists only the verified sample and must not be expanded without matching data, output files, manifests, and validation rules.

The older `data/`, `exports/`, `reports/`, and old manifest paths are retained only as legacy fallback / compatibility paths. The old manifest at `manifests/source_integrity_2025_06_set1.json` is stale and is not the current recommended integrity manifest.

## E. Current CLI Commands

### doctor

Runs read-only health checks for the current configured sample.

Example:

```bash
python scripts/cet6_tool.py doctor \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

Optional explicit config:

```bash
python scripts/cet6_tool.py doctor \
  --paper-id 2025_06_set1 \
  --section reading_section_c \
  --config configs/papers.json
```

The command reports `validate-config`, `list-supported-papers`, `check-source-integrity`, `validate-reading-display`, and `overall_status`.

### validate-config

Checks `configs/papers.json` structure and configured path references for the current allowed sample.

Example:

```bash
python scripts/cet6_tool.py validate-config
```

Optional explicit config:

```bash
python scripts/cet6_tool.py validate-config \
  --config configs/papers.json
```

This command is read-only and does not validate display JSON content or source integrity hashes.

### list-supported-papers

Lists configured paper/section entries from `configs/papers.json`.

Example:

```bash
python scripts/cet6_tool.py list-supported-papers
```

Optional explicit config:

```bash
python scripts/cet6_tool.py list-supported-papers \
  --config configs/papers.json
```

This command is read-only and does not validate or prove data readiness.

### check-source-integrity

Checks stable source files against the recorded manifest hashes.

Example:

```bash
python scripts/cet6_tool.py check-source-integrity \
  --manifest papers/2025_06_set1/manifests/source_integrity.json
```

### validate-reading-display

Validates the current Reading Section C display JSON sample before export or review.

Example:

```bash
python scripts/cet6_tool.py validate-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

Optional explicit config:

```bash
python scripts/cet6_tool.py validate-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c \
  --config configs/papers.json
```

### export-reading-display

Exports the verified Reading Section C display JSON into a Markdown review file.

Example:

```bash
python scripts/cet6_tool.py export-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

## F. Current Approved / Pending Question Status

- approved_final: Q46, Q47, Q48, Q49, Q50, Q51, Q53, Q54
- pending_human_review: None
- manual-review-only: Q52, Q55

## G. Current Boundaries

Current boundaries are intentional and should be preserved until the next milestone is explicitly chosen:

- Other years and other sets have not been processed.
- Reading Section A has not been expanded.
- Reading Section B Q36-Q45 for `2025_06_set1` is completed and display-ready, but it is not yet registered in `configs/papers.json` or covered by CLI validation/export commands.
- Listening transcript analysis has not been done.
- Translation and writing material libraries have not been built.
- Reading-pattern summaries have not been created.
- Q52 and Q55 remain manual-review-only and are not included in final explanations, display JSON, or Markdown export.
- `validate-reading-display` currently targets only the 2025_06_set1 Section C sample.
- `configs/papers.json` currently registers only the verified 2025_06_set1 Reading Section C sample.
- `validate-config` currently allows only 2025_06_set1 / reading_section_c.
- New primary artifacts should default to `papers/`; legacy path cleanup requires its own milestone and should not be done as a side effect.

## H. Recommended Next Options

These are options only. They should not be executed without a separate milestone decision.

1. Continue configuring the workflow so it can support more `paper_id` and `section` combinations.
2. Start Milestone 6A: Reading Section A sample design.
3. Plan Reading full-section aggregation for Section B + Section C.
4. Plan legacy path cleanup as a separate milestone, while avoiding immediate deletion until compatibility risk is reviewed.

## I. Recommended Immediate Next Step

Three reasonable next milestone directions are available:

### Option 1: Continue Configurable Paper/Section Workflow

Pros:

- Extends the verified paper-first path strategy.
- Prepares the CLI and documentation for additional paper IDs and sections.
- Keeps future expansion auditable before adding more content.

Cons:

- Requires careful boundaries so configuration work does not accidentally process new years, sets, or sections.
- May need additional validation rules before broader reuse.

### Option 2: Design Reading Section A or Listening Transcript Sample

Pros:

- Continues testing whether the review workflow generalizes beyond the completed Reading Section B/C samples.
- Helps identify section-specific data and display requirements early.
- Can be kept as a small sample before any broad expansion.

Cons:

- Requires a new sample design and separate review criteria.
- Could expand project scope if not kept to a narrow prototype.

### Option 3: Legacy Path Cleanup Planning

Pros:

- Reduces future confusion between old paths and paper-first paths.
- Can define a clear retirement plan for legacy fallback files.
- Keeps cleanup separate from feature development.

Cons:

- Deleting or moving legacy files too early may break compatibility or historical checks.
- Should be planned and audited before any actual removal.

Recommended priority: choose either Milestone 6A Reading Section A sample design or Reading full-section aggregation for Section B + Section C, unless the next goal is to continue configurable `paper_id` / `section` workflow work first.
