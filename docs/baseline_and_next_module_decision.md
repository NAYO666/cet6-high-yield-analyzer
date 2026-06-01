# Baseline and Next Module Decision

## 1. Current Stable Baseline

- paper_id: `2025_06_set1`
- section: `reading_section_c`
- primary path: `papers/2025_06_set1/reading/section_c/`
- current final/display/export questions: Q46, Q47, Q48, Q49, Q50, Q51, Q53, Q54
- manual-review-only: Q52, Q55

The current stable baseline is frozen around the verified `2025_06_set1` / `reading_section_c` sample. Its primary artifacts live under the paper-first path above.

## 2. Current CLI Safety Chain

The current CLI safety chain for the stable sample is:

- `doctor`
- `validate-config`
- `list-supported-papers`
- `check-source-integrity`
- `validate-reading-display`
- `export-reading-display`

`doctor` is the current quick health-check entry point. The other commands remain available for targeted checks or explicit export workflows.

## 3. Next Module Decision

- selected next module: `reading_section_b`
- reason: 同一套题优先补完整阅读板块，再扩展其他年份。这样可以先把 2025_06_set1 的阅读板块框架打稳，再迁移到其他年份，风险更低，也更符合阅读为核心模块的项目定位。

Not selected now:

- 扩展 2024/2023
- Listening transcript
- legacy cleanup

## 4. Next Recommended Milestone

- Milestone 5A: Reading Section B 样板设计

## 5. Boundaries

- 不处理新年份
- 不处理新数据
- 不生成 Section B final explanation
- 不修改 Section C 稳定产物
- 不更新 `configs/papers.json`，直到 Section B 样板通过
