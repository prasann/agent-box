---
name: agb-pr-desc
description: Generate a GitHub-ready PR description from the current branch changes and save it as PR_DESCRIPTION.md. Use when asked to draft or write a pull request description.
---

# Draft a PR description

1. Inspect the current branch and its changes relative to the intended PR base. If the base is ambiguous, ask the user.
2. Describe meaningful changes and their impact using H2 category headings and bullet points. Group related changes with nested bullets.
3. Exclude test-only updates, documentation, formatting, comments, and import cleanup from the description.
4. Write only the GitHub-ready Markdown to `PR_DESCRIPTION.md` in the target project's root. Do not write into the toolkit repository unless it is the target project.
5. If that file already exists, ask before overwriting it. If there are no qualifying changes, report that rather than inventing a description.
6. Confirm the file was created. Do not create a commit or publish a pull request.
