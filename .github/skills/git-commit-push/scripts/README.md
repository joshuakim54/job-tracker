# Git Commit & Push Scripts

Quick command-line helpers for committing and pushing changes.

## Usage

### PowerShell (Windows)
```powershell
.\commit-push.ps1 "Your commit message"
```

### Bash (Linux/macOS)
```bash
chmod +x commit-push.sh
./commit-push.sh "Your commit message"
```

## Before Running

Make sure you have staged your changes:
```bash
# Stage specific files
git add file1 file2

# Or stage all changes
git add -A
```

## What the Script Does

1. ✅ Checks for staged changes
2. ✅ Creates a commit with your message
3. ✅ Shows the commit hash
4. ✅ Pushes to your current branch on origin
5. ✅ Reports success or errors

## Examples

```powershell
.\commit-push.ps1 "Optimize regex patterns"
.\commit-push.ps1 "Fix bug in location filtering"
.\commit-push.ps1 "Release version 2.0"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No staged changes" | Run `git add <files>` first |
| "Push failed" | Check your GitHub authentication or pull latest changes |
| Permission denied (bash) | Run `chmod +x commit-push.sh` |
