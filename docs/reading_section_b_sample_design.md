# Reading Section B Sample Design

## 1. Scope

- milestone: Milestone 5A
- paper_id: `2025_06_set1`
- target section: `reading_section_b`
- current stable baseline: `reading_section_c`
- primary baseline path: `papers/2025_06_set1/reading/section_c/`
- recommended new section path: `papers/2025_06_set1/reading/section_b/`

This milestone is design-only. It defines the recommended analysis, review, final, and display structure for Reading Section B. It does not generate final explanations, process batches, change configs, modify manifests, regenerate Markdown, or alter any existing Reading Section C artifacts.

## 2. Difference from Reading Section C

Reading Section C is a multiple-choice question workflow. Its core unit is one question with options and a correct answer:

- `question`
- `options`
- `correct_answer`
- `evidence`
- explanation for why one option is correct and others are not

Reading Section B is a paragraph-matching workflow. Its core unit is one statement matched to one article paragraph:

- `statement`
- `matched_paragraph`
- `paragraph evidence`
- `paraphrase`
- explanation for how the statement maps to the paragraph

Important Section B differences:

- Evidence often comes from the whole paragraph, not always from one direct sentence.
- The central reasoning is statement-to-paragraph alignment, not option elimination.
- The workflow needs to record how statement keywords correspond to paragraph expressions.
- The workflow needs stronger paraphrase tracking because the statement usually rewrites the paragraph meaning.
- Distractors are paragraph candidates, not answer options.
- A useful student-facing explanation should teach location method: first identify statement keywords, then scan paragraph-level expressions and paraphrases.

## 3. Recommended Directory Structure

```text
papers/2025_06_set1/reading/section_b/
  analysis/
  final/
  display/
  exports/
  reports/
```

Recommended responsibilities:

- `analysis/`: machine-generated or manually prepared statement-to-paragraph evidence candidates.
- `final/`: approved final explanations after human review.
- `display/`: app-facing or student-facing JSON.
- `exports/`: generated Markdown or other export formats, added only after validation support exists.
- `reports/`: section-specific reports for each later milestone.

No directories are created in this milestone unless a later implementation step explicitly requires them.

## 4. Analysis Layer Fields

The analysis layer should preserve raw source context and candidate reasoning. It is not student-facing and may contain uncertain or competing evidence.

Recommended fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `q_num` | integer | Question number from the paper. |
| `statement` | string | The Section B statement to be matched. |
| `correct_paragraph` | string | Canonical paragraph answer, such as `A`, `B`, `C`. |
| `paragraph_label` | string | Paragraph label from the article. Usually same as `correct_paragraph`, but kept explicit for source consistency. |
| `paragraph_text` | string | Full paragraph text for the matched paragraph. |
| `evidence_sentence_candidates` | array of strings | Candidate sentence-level evidence inside the paragraph, if available. |
| `evidence_context_note` | string | Explanation of paragraph-level evidence when no single sentence is enough. |
| `keyword_candidates` | array of objects | Candidate statement keywords and related paragraph expressions. |
| `paraphrase_candidates` | array of objects | Candidate paraphrase pairs between statement wording and paragraph wording. |
| `distractor_paragraph_candidates` | array of objects | Paragraphs that look plausible but should be rejected, with brief reasons. |
| `review_status` | string | Suggested values: `pending`, `needs_manual_review`, `approved_for_review_sheet`. |
| `manual_review_note` | string | Free-form reviewer note. |

Suggested `keyword_candidates` object:

```json
{
  "statement_keyword": "",
  "paragraph_expression": "",
  "match_type": "direct | paraphrase | concept",
  "confidence": "low | medium | high"
}
```

Suggested `paraphrase_candidates` object:

```json
{
  "statement_phrase": "",
  "paragraph_phrase": "",
  "paraphrase_type": "synonym | explanation | implication | compression",
  "note": ""
}
```

Suggested `distractor_paragraph_candidates` object:

```json
{
  "paragraph_label": "",
  "reason_it_looks_related": "",
  "reason_rejected": ""
}
```

### 自动候选生成规则约束

- 所有 `evidence_sentence_candidates` 必须通过通用自动生成规则产生。
- 所有 `keyword_candidates` 必须通过通用自动生成规则产生。
- 所有 `paraphrase_candidates` 必须通过通用自动生成规则产生。
- 自动候选生成规则可以写入脚本或 Codex 指令，但必须能复用到其他年份、其他套题和其他样板。
- 不允许针对每道题写死人工提示。
- 当前样板的具体候选结果只能出现在输出 JSON 中，包括 `analysis`、`review`、`final` 和 `display`。
- 人工审核意见只能记录在 review sheet 中。
- 人工审核意见不允许写死进自动候选生成逻辑或 Codex 指令。
- Milestone 5C 及以后候选生成相关报告模板或后续报告必须增加验证字段：`hardcoded_question_hints_used: false`。

## 5. Human Review Layer Fields

The review sheet should convert raw candidates into a human-verifiable checklist. It should make the reviewer decide whether the paragraph match is supported, how the statement is located, and whether the explanation is ready for final generation.

Recommended review sheet fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `q_num` | integer | Question number. |
| `statement` | string | Original statement. |
| `correct_paragraph` | string | Expected matched paragraph. |
| `paragraph_text` | string | Full text of the matched paragraph. |
| `direct_evidence` | string | Best direct evidence sentence, if one exists. |
| `context_evidence` | string | Paragraph-level evidence summary when evidence is distributed. |
| `keyword_review` | string | Confirmed keyword-to-expression mapping. |
| `paraphrase_review` | string | Confirmed paraphrase mapping. |
| `distractor_review` | string | Notes on likely distractor paragraphs and why they fail. |
| `student_location_method_zh` | string | Chinese note explaining how a student should locate the paragraph. |
| `low_vocab_location_tip_zh` | string | Chinese tip for students with weaker vocabulary. |
| `review_status` | string | Suggested values: `pending`, `needs_revision`, `approved`, `rejected`. |
| `ready_for_final_explanation` | boolean | Whether this item may enter final explanation generation. |
| `manual_review_note` | string | Reviewer note for corrections or concerns. |

Review rules:

- `ready_for_final_explanation` should be `true` only when the correct paragraph, evidence, keyword mapping, and paraphrase mapping are all reviewed.
- If evidence is paragraph-level rather than sentence-level, `context_evidence` must explain the paragraph logic clearly.
- If a distractor is likely, `distractor_review` should name the paragraph and explain the false match.
- The review layer should not polish the final explanation. It should approve the evidence and reasoning inputs.

## 6. Final Explanation Fields

The final layer should contain only approved, student-facing explanation material. It should not include uncertain candidates.

Recommended final fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `q_num` | integer | Question number. |
| `statement` | string | Original statement. |
| `correct_paragraph` | string | Confirmed paragraph answer. |
| `final_explanation_zh` | string | Student-facing Chinese explanation. |
| `final_location_tip_zh` | string | Chinese paragraph-location strategy. |
| `paragraph_evidence` | string or array | Confirmed direct or paragraph-level evidence. |
| `confirmed_keywords` | array | Confirmed keywords and paragraph expressions. |
| `confirmed_paraphrases` | array | Confirmed paraphrase mappings. |
| `distractor_warning_zh` | string | Chinese warning about likely misleading paragraph(s). |
| `final_status` | string | Suggested values: `draft`, `approved`, `blocked`. |

Final generation rules:

- Generate final explanations only from approved review rows.
- Preserve paragraph labels exactly as source answers use them.
- Do not invent evidence outside the matched paragraph.
- Prefer explaining the location path before explaining the meaning.
- Keep distractor warnings concise and tied to concrete paragraph differences.

## 7. Display JSON Fields and Order

The display JSON should be optimized for student reading and app rendering. It should hide raw candidate uncertainty and present the approved answer path.

Recommended display order:

1. `q_num`: 题号
2. `statement`: statement
3. `correct_paragraph`: 正确匹配段落
4. `answer_explanation_zh`: 答案解析
5. `paragraph_source_text`: 段落原文出处
6. `location_method_zh`: 做题时怎么定位
7. `keywords`: 关键词
8. `paraphrases`: 同义替换
9. `distractor_warning_zh`: 干扰段落提醒
10. `low_vocab_tip_zh`: 低词汇量提示

Suggested display object:

```json
{
  "q_num": 0,
  "statement": "",
  "correct_paragraph": "",
  "answer_explanation_zh": "",
  "paragraph_source_text": "",
  "location_method_zh": "",
  "keywords": [],
  "paraphrases": [],
  "distractor_warning_zh": "",
  "low_vocab_tip_zh": ""
}
```

Display rules:

- Display JSON should be generated only after final explanations are approved.
- Display JSON should not include `review_status`, `manual_review_note`, or low-confidence candidates.
- If `direct_evidence` does not exist, the display should use a clear paragraph-level evidence summary.
- Student-facing Chinese should focus on locating and matching, not summarizing general reading rules.

## 8. Recommended Milestone Plan

- Milestone 5B: Extract Reading Section B article paragraphs, statements, and answers from the existing structured JSON for `2025_06_set1`.
- Milestone 5C: Generate statement-to-paragraph evidence candidates.
- Milestone 5D: Create and complete the human review sheet.
- Milestone 5E: Generate approved final explanations only from reviewed rows.
- Milestone 5F: Generate display JSON from approved final explanations.
- Milestone 5G: Add CLI validation/export support for `reading_section_b`.
- Milestone 5H: Add `reading_section_b` to `configs/papers.json` only after the Section B sample passes validation.

## 9. Explicit Non-Goals for Milestone 5A

This milestone does not execute:

- no new PDF parsing
- no new year processing
- no other paper set processing
- no Reading Section A processing
- no Listening, Translation, or Writing processing
- no Section B final explanation generation
- no batch processing
- no Section C file modification
- no `configs/papers.json` update
- no manifest update
- no Markdown export regeneration
- no legacy file deletion
- no general reading-rule summary

## 10. Stop Point

After this design document and the paired report are created, the process should stop and wait for human review before Milestone 5B begins.
