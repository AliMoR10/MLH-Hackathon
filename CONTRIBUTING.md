# Contributing to First PR Buddy

Thanks for helping! These rules keep the project tidy and avoid merge conflicts.

## Workflow

1. **Pick or create an issue** and assign it to yourself.
2. **Update `main`** before starting:
   ```bash
   git checkout main
   git pull
   ```
3. **Create a branch** named after the type of work:
   | Prefix | Use for | Example |
   |---|---|---|
   | `feat/` | new feature | `feat/issue-screenshot` |
   | `fix/` | bug fix | `fix/rate-limit-error` |
   | `docs/` | documentation | `docs/readme-screenshots` |
   | `chore/` | setup, CI, config | `chore/deploy-config` |
   ```bash
   git checkout -b feat/issue-screenshot
   ```
4. **Commit** small, clear changes using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add difficulty filter to issues tab
   fix: handle repos with no README
   docs: add demo GIF to README
   ```
5. **Push and open a Pull Request** into `main`. Fill in the PR template and link the issue (`Closes #12`).
6. **Get one review.** A teammate approves, then the PR is merged with **Squash and merge**.

## Rules

- Never push directly to `main`.
- Work in the file you own where possible (see the Team table in the README).
- Never commit secrets. API keys go in `.env`, which is ignored by Git.
- Make sure `ruff check .` and `pytest` pass before opening a PR (CI checks this too).

## Running locally

See [Getting started](README.md#-getting-started) in the README.
