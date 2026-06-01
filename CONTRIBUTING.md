# Contributing

Thanks for considering a contribution. This project is intentionally early-stage, so careful scope control matters more than adding many features quickly.

## Good Contributions

- Improve public documentation and examples.
- Add mock analysis examples that do not copy real exam text.
- Improve JSON schemas or validation rules.
- Add tests for sample files and schema compatibility.
- Fix encoding problems in documentation without changing source meaning.
- Make CLI behavior clearer or safer without expanding support claims.

## Copyright Boundary

Do not contribute:

- full exam papers
- answer PDFs
- extracted full-text exam files
- long passages copied from copyrighted materials
- commercial question-bank content

Public examples should be fictional, synthetic, shortened, or clearly user-owned.

## Scope Boundary

Please do not describe planned work as finished. In particular, avoid claims that the project:

- fully supports CET-6
- is finished for production use
- automatically finalizes every answer
- guarantees score improvement
- includes an official dataset
- has broad adoption

## Analysis Quality

When adding analysis output, keep the workflow human-reviewable:

- preserve source evidence
- separate candidate output from approved output
- record review status
- explain paraphrases and distractor traps concretely
- avoid inventing evidence that is not present in the user-provided text

## Development Notes

- Do not modify core parsing or analysis logic as part of documentation-only changes.
- Do not introduce dependencies unless the change clearly requires them.
- Keep mock examples small.
- Prefer narrow, reviewable pull requests.
