# Privacy And Local Storage

This project is designed around local-first study workflows, but local-first does not automatically mean encrypted, backed up, or risk-free.

## Current Repository State

The current repository does not include a completed wrong-question review PWA.

Existing PWA-related descriptions are roadmap direction only. They describe a future companion tool for saving:

- wrong questions
- mistake causes
- review notes
- high-yield vocabulary
- paraphrase pairs
- spaced-review schedules

## Future PWA Storage Boundary

If a PWA module is added later and uses browser storage such as `localStorage` or `IndexedDB`, the documentation should clearly say:

- review data is stored in the user's browser by default
- clearing browser/site data may delete saved review data
- browser storage is not the same as a secure backup
- browser storage is not encrypted by default unless the app explicitly implements encryption
- private wrong-question records should not be committed to the repository
- exports should be reviewed by the user before sharing

## What Not To Upload

Do not upload personal review data, including:

- real wrong-question logs
- mistake notes
- personal review schedules
- browser local storage dumps
- IndexedDB exports
- screenshots containing private study records
- API keys or service credentials

## Public Examples

Public examples should use mock data only. The examples in `examples/` are fictional and safe to share.

