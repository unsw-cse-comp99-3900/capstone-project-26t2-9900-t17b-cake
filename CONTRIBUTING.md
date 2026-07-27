# Contributing

## Branch workflow

1. Update local `development`.
2. Create a branch named `<JIRA-KEY>-<short-kebab-description>`.
3. Make focused commits whose subjects start with the same Jira key.
4. Push the branch and open a pull request into `development`.
5. Request review from at least one teammate who is not the author.
6. Address comments, keep CI green, and obtain one approval before merging.
7. Merge `development` into `main` only through a release pull request.

Example:

```powershell
git switch development
git pull --ff-only
git switch -c T17B-123-improve-session-import
git commit -m "T17B-123 validate session metadata fields"
git push -u origin T17B-123-improve-session-import
```

Use the Jira key assigned to the work. Do not invent historical tickets or
backdate commits.

## Commit scope

- Keep source, tests, documentation, generated evidence, and references in
  separate commits when they can be reviewed independently.
- Use imperative, descriptive commit subjects.
- Do not commit caches, environments, raw client data, recordings, credentials,
  or machine-specific paths.
- Regenerate derived reports with the documented commands rather than editing
  generated values manually.

## Pull requests

Use `.github/pull_request_template.md`. A pull request must explain:

- the linked Jira work and acceptance criteria;
- what changed and why;
- user, developer, and data-handling impact;
- the commands and evidence used for validation;
- any limitations, follow-up work, or hardware-validation boundary.

Reviewers should leave an approval, request changes, or a substantive comment.
All conversations must be resolved before merge. Authors must not approve their
own pull requests.

## Required validation

Run the focused checks before requesting review:

```powershell
python -m pytest -q -p no:cacheprovider
python references/client_delay_comparison/rebuild_figures.py
```

The protected branches also require the the `test` job from `offline-validation` GitHub
Actions check.
