#!/bin/bash
# Git Commit & Push Helper Script
# Usage: ./commit-push.sh "Your commit message here"
# This script commits staged changes and pushes to the remote repository

set -e  # Exit on any error

if [ $# -eq 0 ]; then
    echo "❌ Error: Commit message required"
    echo "Usage: $0 \"Your commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"

# Check if there are staged changes
if ! git diff --cached --quiet; then
    echo "📝 Creating commit: \"$COMMIT_MESSAGE\""
    git commit -m "$COMMIT_MESSAGE"
    COMMIT_HASH=$(git rev-parse --short HEAD)
    echo "✅ Commit created: $COMMIT_HASH"
else
    echo "⚠️  No staged changes to commit"
    exit 1
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🚀 Pushing to remote branch: $BRANCH"

if git push origin "$BRANCH"; then
    echo "✅ Successfully pushed to $BRANCH"
else
    echo "❌ Push failed. Check your connection or permissions."
    exit 1
fi

echo ""
echo "✨ Commit & push complete!"
