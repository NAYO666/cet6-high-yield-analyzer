# Project Positioning

`CET-6 High-Yield Analyzer` is an early-stage learning experiment around exam-oriented language learning.

It starts from a practical question:

> If a learner has limited time and limited vocabulary, which words and reasoning patterns are worth reviewing first?

The project does not try to turn every word in a paper into a vocabulary list. It tries to identify words and phrases that actually affect answer selection.

## Core Idea

Learn fewer words, but learn the words that matter most.

In this project, "matter most" means that a word or expression has a job in the question-solving process:

- it helps locate the relevant sentence or paragraph
- it connects a question stem to source evidence
- it rewrites the same idea in a different form
- it marks contrast, cause, concession, or inference
- it makes a wrong option tempting
- it explains a repeated mistake in review

This is different from ordinary vocabulary memorization. A frequent word is not always high-yield. A rare phrase can be high-yield if it unlocks the answer path.

## What The Project Is

- A learning-oriented analysis workflow.
- A small, human-reviewable pipeline for CET-6 reading samples.
- A way to convert user-provided text into review assets.
- A place to explore evidence, paraphrase, distractor, and low-vocabulary strategies.
- A future foundation for a wrong-question review PWA.

## What The Project Is Not

- It is not a full exam-content database.
- It is not an official dataset.
- It is not a finished exam app.
- It is not a guarantee of score improvement.
- It is not intended to redistribute complete papers or answer explanations.

## Learning Workflow

The target workflow is:

```text
read a question
  -> locate evidence
  -> identify paraphrase
  -> reject distractors
  -> record the high-yield language items
  -> review mistakes over time
```

For low-vocabulary learners, this matters because the task is often not to understand every sentence perfectly. The more useful skill is to find enough reliable evidence to choose an answer and then review the exact language gap that caused difficulty.

## Current Real State

The repository currently contains sample workflows around CET-6 reading analysis. Section C and Section B have meaningful artifacts, but the project is still narrow:

- only a small number of sample paths are stable
- CLI registration is narrower than the files present in the repository
- historical artifacts may contain encoding issues
- PWA integration is still a future direction
- public-safe example data needs to remain fictional or user-provided

That early-stage status is part of the project identity. The goal is not to look finished; the goal is to make the learning question and method clear enough for others to inspect, reuse, and improve.
