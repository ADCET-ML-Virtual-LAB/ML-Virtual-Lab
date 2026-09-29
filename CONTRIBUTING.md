# Contributing

## 1. Never commit directly to `main`
`main` should always be something that actually runs. Every change goes
through a branch + a Pull Request, even small ones.

```bash
git checkout main
git pull
git checkout -b feat/short-description   # see naming below
```

## 2. Before opening a PR
- [ ] Pull latest `main` and merge(Do not rebase) it into your branch, fix any
      conflicts yourself before asking someone else to review.
- [ ] Actually run the app and test what you built (each issue has a
      "How to test" / "Acceptance criteria" section — go through it).
- [ ] If you touched the backend: `pre-commit run --all-files` (installed
      once via `pip install -r backend/requirements-dev.txt && pre-commit
      install` — see README).
- [ ] Don't commit `.env`, `node_modules/`, `__pycache__/`, or anything
      with real passwords/keys in it. `.gitignore` already covers the
      usual ones — if you add a new kind of secret file, add it there too.

## 3. Opening the PR
- Title: short, describes the change (`Add login + change-password
  endpoints`, not `updates`).
- Link the issue it closes, e.g. `Closes #4`.
- One-line description of what you did if it's not obvious from the title.

## 4. Review before merge
- At least one other teammate approves before merging — even a quick
  "looks good" in the PR comments counts.
- If you're reviewing: pull the branch and actually click through it
  where you can, don't just read the diff.
- Whoever opened the PR merges it (after approval), so they know it's
  really their change going in.

## 5. Commit messages
Doesn't need to be fancy, just clear enough that `git log` is useful:
```
Add student upload endpoint
Fix 500 on duplicate batch name
```
Not:
```
update
fix stuff
wip
```
(Squash your "wip"/"fix typo" commits into one clean commit when you
merge the PR — GitHub's "Squash and merge" button does this for you.)

## 6. If something breaks on `main`
Tell the group immediately. Whoever caused it (or whoever's free) reverts
the merge commit or pushes a quick fix — don't leave `main` broken
overnight.

## 7. Questions / unsure about scope
If an issue is unclear or you think it should be split further, say so
before you start, not after you've built the wrong thing. Better a 2-minute
question in chat than a re-do.
