# CET-6 CLI Usage

## Tool Scope

This is a CET-6 past-paper review helper. In the current milestone, it supports validating the verified Reading Section C display JSON and exporting it into a Markdown review file.

No new analysis is performed by this CLI. It reads the existing display JSON and formats the already-approved display content.

## Available Command

### doctor

Runs a read-only health check for one configured paper/section sample. It checks the config, confirms the paper/section is registered, checks source integrity through the configured manifest, and validates the configured display JSON structure.

Default config:

```bash
python scripts/cet6_tool.py doctor \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

Explicit config:

```bash
python scripts/cet6_tool.py doctor \
  --paper-id 2025_06_set1 \
  --section reading_section_c \
  --config configs/papers.json
```

This command is read-only. It does not export Markdown, refresh the manifest, regenerate analysis, or modify any JSON files.

Current doctor scope is intentionally limited to:

```text
2025_06_set1 / reading_section_c
```

### validate-config

Validates `configs/papers.json` structure and path references. This command is read-only: it does not run `validate-reading-display`, does not export Markdown, does not check source integrity hashes, and does not modify any JSON files.

Default config:

```bash
python scripts/cet6_tool.py validate-config
```

Explicit config:

```bash
python scripts/cet6_tool.py validate-config \
  --config configs/papers.json
```

Current validation scope is intentionally narrow:

```text
allowed paper_id: 2025_06_set1
allowed section: reading_section_c
```

The command checks that required config fields exist, labels and path fields are non-empty strings, configured paths stay inside the expected `papers/2025_06_set1/...` layout, required referenced files exist, and the export directory exists.

It does not read or validate display JSON content, does not check final explanation content, does not check question numbers, and does not calculate sha256 hashes. Future paper or section expansion must update both `configs/papers.json` and the config validation rules.

### list-supported-papers

Lists the paper and section entries currently registered in `configs/papers.json`. This command is read-only: it does not validate data, export Markdown, check source integrity, or modify any JSON files.

Default config:

```bash
python scripts/cet6_tool.py list-supported-papers
```

Explicit config:

```bash
python scripts/cet6_tool.py list-supported-papers \
  --config configs/papers.json
```

The output includes the config file path, paper id, paper label, section key, section label, section root, display JSON path, export Markdown path, and manifest path.

Important: this command lists configured samples only. It does not prove that data quality, manifests, display JSON, or validation rules are ready for a broader workflow.

Current registered sample:

```text
2025_06_set1 / reading_section_c
```

### validate-reading-display

Validates a Reading Section C display JSON file before export. It only reads the display JSON and does not modify files.

Paper/section path mode, recommended:

```bash
python scripts/cet6_tool.py validate-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

Paper/section path mode is resolved through:

```text
configs/papers.json
```

The same command can use an explicit config file:

```bash
python scripts/cet6_tool.py validate-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c \
  --config configs/papers.json
```

In paper/section path mode, the CLI resolves the input display JSON from config to:

```text
papers/2025_06_set1/reading/section_c/display/display.json
```

Explicit path mode, legacy-compatible and still supported:

```bash
python scripts/cet6_tool.py validate-reading-display \
  --input data/display/reading_section_c_2025_06_set1_display.json
```

The explicit path example above points to the retained legacy fallback file:

```text
data/display/reading_section_c_2025_06_set1_display.json
```

Current validation is limited to the `2025_06_set1` Reading Section C display sample. The expected question list is `[46, 47, 48, 49, 50, 51, 53, 54]`.

### check-source-integrity

Checks stable source files against a manifest of recorded sha256 hashes. The command reads only the manifest and the files listed in that manifest. It does not modify source JSON files and does not update hashes automatically.

```bash
python scripts/cet6_tool.py check-source-integrity \
  --manifest papers/2025_06_set1/manifests/source_integrity.json
```

Recommended current manifest:

```text
papers/2025_06_set1/manifests/source_integrity.json
```

The command can still read the old-path manifest as a legacy-compatible check:

```bash
python scripts/cet6_tool.py check-source-integrity \
  --manifest manifests/source_integrity_2025_06_set1.json
```

The old manifest at `manifests/source_integrity_2025_06_set1.json` is stale. It is retained as historical record and is not the current recommended manifest.

The manifests lock only stable core data for `2025_06_set1` Reading Section C: the review sheet JSON, final explanations JSON, and display JSON.

It intentionally does not lock generated Markdown exports, ordinary report Markdown files, caches, logs, temporary files, `__pycache__`, or `.pyc` files.

### export-reading-display

Exports a Reading Section C display JSON file to Markdown.

Paper/section path mode, recommended:

```bash
python scripts/cet6_tool.py export-reading-display \
  --paper-id 2025_06_set1 \
  --section reading_section_c
```

Paper/section path mode reads `configs/papers.json` by default. Use `--config configs/papers.json` to pass the config file explicitly.

In paper/section path mode, the CLI resolves paths from config as:

```text
input:  papers/2025_06_set1/reading/section_c/display/display.json
output: papers/2025_06_set1/reading/section_c/exports/display.md
```

Explicit path mode, legacy-compatible and still supported:

```bash
python scripts/cet6_tool.py export-reading-display \
  --input data/display/reading_section_c_2025_06_set1_display.json \
  --output exports/reading_section_c_2025_06_set1_display.md
```

The explicit path example above points to retained legacy fallback files:

```text
input:  data/display/reading_section_c_2025_06_set1_display.json
output: exports/reading_section_c_2025_06_set1_display.md
```

Do not mix explicit path arguments with paper/section arguments. For `validate-reading-display`, use either `--input` or both `--paper-id` and `--section`. For `export-reading-display`, use either both `--input` and `--output`, or both `--paper-id` and `--section`.

The current paper/section config registers only the verified sample: `paper_id = 2025_06_set1` and `section = reading_section_c`.

## Input File

The input file must be a display JSON file with a top-level `questions` list. Each validated or exported question must include `display_blocks`, options, answer content, evidence, location method, paraphrase notes, and low-vocabulary tips.

Current verified input:

```text
papers/2025_06_set1/reading/section_c/display/display.json
data/display/reading_section_c_2025_06_set1_display.json
```

## Output File

The `validate-reading-display` command does not write an output file.

The `export-reading-display` command writes a Markdown file for Reading Section C display review. If the output directory does not exist, the CLI creates it automatically.

Current verified output:

```text
papers/2025_06_set1/reading/section_c/exports/display.md
exports/reading_section_c_2025_06_set1_display.md
```

## Current Limits

Only the `2025_06_set1` Reading Section C display sample has been verified.

The CLI does not fill skipped questions, does not process Listening, does not process other years or sets, and does not regenerate final explanations.

Paper/section path resolution is configurable through `configs/papers.json`, but the `validate-reading-display` rules still validate only the current Section C sample. Future paper or section entries must not be added until the corresponding data and validation rules are prepared.

The `check-source-integrity` command currently checks only the `2025_06_set1` Reading Section C core data listed in a provided manifest. The recommended current manifest is `papers/2025_06_set1/manifests/source_integrity.json`; the old manifest at `manifests/source_integrity_2025_06_set1.json` is stale and retained only as historical legacy fallback.

## Planned Commands

The following commands are planned but not implemented:

- `export-reading-review-sheet`
