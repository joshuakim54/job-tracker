# Git Commit & Push Helper Script (PowerShell)
# Usage: .\commit-push.ps1 "Your commit message here"
# This script commits staged changes and pushes to the remote repository

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$CommitMessage
)

$ErrorActionPreference = "Stop"

# Check if there are staged changes
$stagedChanges = git diff --cached --quiet 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  No staged changes to commit" -ForegroundColor Yellow
    exit 1
}

# Create commit
Write-Host "📝 Creating commit: `"$CommitMessage`"" -ForegroundColor Cyan
git commit -m $CommitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed" -ForegroundColor Red
    exit 1
}

$commitHash = git rev-parse --short HEAD
Write-Host "✅ Commit created: $commitHash" -ForegroundColor Green

# Get current branch
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "🚀 Pushing to remote branch: $branch" -ForegroundColor Cyan

# Push to remote
git push origin $branch

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Push failed. Check your connection or permissions." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Successfully pushed to $branch" -ForegroundColor Green
Write-Host ""
Write-Host "✨ Commit & push complete!" -ForegroundColor Green
