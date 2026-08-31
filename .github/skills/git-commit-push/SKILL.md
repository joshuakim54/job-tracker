---
name: git-commit-push
description: 'Commit staged changes to GitHub and push to remote. Use when you want to save your work, create a commit message, and push to your repository.'
argument-hint: 'Commit message describing your changes'
user-invocable: true
---

# Git Commit & Push

Streamline committing changes and pushing them to your GitHub repository.

## When to Use

- After making code changes you want to save
- When you have specific files ready to commit
- To push commits to GitHub after staging changes
- When you want to maintain a clean commit history

## Procedure

### 1. Stage Your Changes
Before using this skill, stage the files you want to commit using one of these methods:

- **Stage specific files:**
  ```bash
  git add path/to/file1 path/to/file2
  ```

- **Stage all modified files:**
  ```bash
  git add -A
  ```

- **Interactive staging (choose which changes to stage):**
  ```bash
  git add -p
  ```

### 2. Run the Commit & Push Skill
When you have files staged and ready, ask me to commit and push. Provide a clear commit message describing your changes.

**Example requests:**
- "Commit these changes with message 'Optimize regex patterns for better performance'"
- "Push changes: 'Add git commit-push skill'"
- "Commit and push my updates"

### 3. Verify the Push
The skill will:
1. ✅ Create a commit with your message
2. ✅ Display the commit hash and details
3. ✅ Push the commit to your default branch
4. ✅ Confirm successful push or show any errors

## Commit Message Tips

Write clear, concise commit messages that explain **what** changed and **why**:

- ✅ Good: "Add pre-compiled regex patterns for 20% performance boost"
- ✅ Good: "Fix location filtering logic in job_monitor.py"
- ❌ Poor: "fix stuff"
- ❌ Poor: "update"

## Common Scenarios

### Scenario: New feature with multiple files
```bash
git add src/feature.py tests/test_feature.py
# Then request: "Commit: 'Implement feature X with tests'"
```

### Scenario: Bug fix in single file
```bash
git add src/bugfix.py
# Then request: "Commit: 'Fix bug in X function'"
```

### Scenario: All changes ready
```bash
git add -A
# Then request: "Commit and push: 'Version 1.0 release'"
```

## Troubleshooting

**"Nothing to commit"** → Stage changes first with `git add`

**"Push rejected"** → Your local branch differs from remote. Use `git pull` first, resolve conflicts, then commit & push again

**"Authentication failed"** → Configure GitHub authentication (SSH key or personal access token)

## References

- [Git basics](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository)
- [GitHub docs](https://docs.github.com/en/get-started)
