#!/bin/bash
set -e

# Script to commit model update fixes
echo "🔧 Committing Claude model update fixes..."

cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Add the changed files
git add src/config_manager.py
git add enhanced_deployment.py

# Commit with descriptive message
git commit -m "fix: Update Claude model to current version (claude-3-5-sonnet-20241022)

- Updated default model from deprecated claude-3-sonnet-20240229 to claude-3-5-sonnet-20241022
- Updated supported models list in deployment script
- Fixes 404 errors when calling Anthropic API

The old model claude-3-sonnet-20240229 is no longer available, causing API calls to fail with 404 errors.
This update switches to the latest available Sonnet model."

echo "✅ Changes committed successfully!"
echo ""
echo "To push to GitHub, run:"
echo "  git push origin main"
echo ""
echo "Current git status:"
git status
