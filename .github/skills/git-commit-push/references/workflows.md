# Git Workflow Quick Reference

Common workflows for staging, committing, and pushing changes.

## Workflow 1: Commit Specific Files

```bash
# Stage only the files you want
git add src/file1.py src/file2.py

# Commit with Copilot
# "Stage these changes: 'Update file1 and file2'"

# Or use the script
.\commit-push.ps1 "Update file1 and file2"
```

## Workflow 2: Commit All Changes

```bash
# Stage everything that's modified or deleted
git add -A

# Commit with Copilot
# "Commit all changes: 'Optimize performance'"

# Or use the script
.\commit-push.ps1 "Optimize performance"
```

## Workflow 3: Interactive Staging (Cherry-pick changes)

```bash
# Choose which changes to stage
git add -p

# Review prompts and select (y/n/s/e)
# Then commit

.\commit-push.ps1 "Selective changes message"
```

## Workflow 4: Commit with Multiple Files

```bash
# See what files have changes
git status

# Stage specific ones
git add -u  # Updates tracked files
# or
git add new_file.py tracked_file.py

# Commit
.\commit-push.ps1 "Mixed changes"
```

## Useful Commands

| Command | Purpose |
|---------|---------|
| `git status` | See which files are modified/staged |
| `git diff` | See unstaged changes |
| `git diff --cached` | See staged changes |
| `git add <file>` | Stage a specific file |
| `git add -A` | Stage all changes |
| `git add -p` | Interactive staging |
| `git reset <file>` | Unstage a file |
| `git log --oneline -5` | See last 5 commits |
| `git branch` | See current branch |

## Tips

- **Atomic commits**: Each commit should do one thing (one fix, one feature)
- **Meaningful messages**: Help your future self understand why changes were made
- **Frequent commits**: Push regularly to backup your work
- **Before pushing**: Run tests or linters to catch issues early

## Fixing Mistakes

```bash
# Oops, committed to wrong branch?
git reset HEAD~1          # Undo last commit, keep changes staged
git checkout -b new-branch
.\commit-push.ps1 "Fixed message"

# Oops, forgot to add a file?
git add forgotten-file
git commit --amend --no-edit  # Add to previous commit
git push --force-with-lease   # Update remote

# Wrong commit message?
git commit --amend -m "Correct message"
git push --force-with-lease
```
