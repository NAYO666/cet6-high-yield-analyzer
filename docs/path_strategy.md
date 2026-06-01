# CET-6 Path Strategy

## A. Current Decision

The project now officially adopts the paper-first directory structure as the default working path strategy.

Recommended primary path:

```text
papers/2025_06_set1/reading/section_c/
```

Future years, paper sets, sections, and workflow stages should default to the `papers/` structure.

## B. Recommended Working Paths

Current recommended paths:

- review sheet:
  `papers/2025_06_set1/reading/section_c/analysis/review_sheet.json`
- final explanations:
  `papers/2025_06_set1/reading/section_c/final/final_explanations.json`
- display JSON:
  `papers/2025_06_set1/reading/section_c/display/display.json`
- Markdown export:
  `papers/2025_06_set1/reading/section_c/exports/display.md`
- source integrity manifest:
  `papers/2025_06_set1/manifests/source_integrity.json`

## C. Legacy Paths

The old paths are retained, but they are now legacy / compatibility fallback paths only. They should not be treated as the recommended primary working locations.

Legacy paths:

- `data/analysis/reading_section_c_2025_06_set1_review_sheet.json`
- `data/final/reading_section_c_2025_06_set1_final_explanations.json`
- `data/display/reading_section_c_2025_06_set1_display.json`
- `exports/reading_section_c_2025_06_set1_display.md`
- `reports/...` old milestone reports
- `manifests/source_integrity_2025_06_set1.json`

## D. Manifest Strategy

Current recommended source integrity manifest:

```text
papers/2025_06_set1/manifests/source_integrity.json
```

This new-path manifest is the current recommended integrity check file.

Legacy manifest:

```text
manifests/source_integrity_2025_06_set1.json
```

The legacy manifest is stale. It is retained as historical record and should no longer be treated as the current recommended integrity check target.

The old manifest is not automatically refreshed. If the project later decides to clean up old paths or retire legacy compatibility files, that cleanup must be reviewed in a separate milestone.

## E. CLI Usage Strategy

Recommended CLI usage uses paper/section path mode:

```bash
python scripts/cet6_tool.py validate-reading-display --paper-id 2025_06_set1 --section reading_section_c
```

```bash
python scripts/cet6_tool.py export-reading-display --paper-id 2025_06_set1 --section reading_section_c
```

```bash
python scripts/cet6_tool.py check-source-integrity --manifest papers/2025_06_set1/manifests/source_integrity.json
```

Paper/section path mode is resolved through the config file:

```text
configs/papers.json
```

The default config currently registers only the verified sample:

- paper_id: `2025_06_set1`
- section: `reading_section_c`

The older `--input` / `--output` explicit path mode remains supported as a compatibility mode.

Do not mix explicit path arguments with paper/section arguments in the same command.

## F. Future Rule

Future development, new years, and new sections should write primary artifacts into `papers/` by default.

Unless the change is explicitly for compatibility, do not add new primary artifacts of the same kind under `data/display/`, `data/final/`, or `exports/`.

Adding a new `paper_id` or `section` to `configs/papers.json` is not enough to declare support. The corresponding source data, review sheet, final explanations, display JSON, Markdown export target, manifest, and validation rules must be prepared and reviewed first.

Path resolution is now configurable, but `validate-reading-display` still uses the current Reading Section C sample rules.

Legacy path cleanup must be handled as its own milestone. Do not delete old paths as a side effect of another milestone.

## G. 自动候选生成规则约束（新增）

Milestone 5C 及以后所有候选生成模块必须遵守以下约束，目标是让题目导入后的分析流程保持自动化、可复用，并避免逐题人工提示进入生成逻辑。

通用规则：

- 自动候选生成规则可以写入脚本或 Codex 指令。
- 自动候选生成规则必须能复用到其他年份、其他套题和其他样板。
- 自动候选生成规则应描述通用抽取、匹配、定位、改写识别和候选排序方法，不应绑定某一道具体题目的人工判断。

当前样板结果：

- 当前样板的具体分析结果只能出现在输出 JSON 中，包括 `analysis`、`review`、`final` 和 `display`。
- 当前样板的具体题目结果不允许写死在自动生成逻辑里。
- 当前样板的具体题目结果不允许作为硬编码提示写入 Codex 指令。

人工审核意见：

- 人工审核意见只能作为 review sheet 字段保存。
- 人工审核意见不允许写死进自动候选生成逻辑。
- 人工审核意见不允许写死进 Codex 指令。

报告验证字段：

- Milestone 5C 及以后候选生成相关报告模板或后续报告必须增加验证字段：`hardcoded_question_hints_used: false`。
- 如果发现自动候选生成逻辑使用了逐题人工提示，相关 milestone 不得标记为通过。
