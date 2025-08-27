#!/bin/bash
# Avatar Engine - Git Deployment Preparation Script
# This script prepares all changes for deployment to GitHub

set -e  # Exit on any error

echo "🚀 Avatar Engine - Preparing for Git Push"
echo "=========================================="
echo ""

# Change to project directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Show current status
echo "📊 Current Git Status:"
echo "----------------------"
git status --short
echo ""

# Add all modified files
echo "📝 Adding modified files..."
git add -A

# Show what will be committed
echo "📋 Files to be committed:"
echo "------------------------"
git diff --cached --name-status
echo ""

# Create comprehensive commit message
commit_message="fix: Update Claude model to current version and fix API errors

Changes:
- Updated default Claude model from deprecated claude-3-sonnet-20240229 to claude-3-5-sonnet-20240620
- Fixed 404 API errors caused by using unavailable model
- Updated supported models list in deployment script
- Added test script to verify model configuration

Technical Details:
- The old model (claude-3-sonnet-20240229) is no longer available via Anthropic API
- New model (claude-3-5-sonnet-20240620) is the latest Sonnet version
- This fix resolves the error occurring in python3 ./enhanced_deployment.py --analyze-all

Files Modified:
- src/config_manager.py: Updated default model in AnthropicConfig
- enhanced_deployment.py: Updated supported models list
- test_model_update.py: Added verification script
- commit_model_update.sh: Added deployment helper script"

# Commit changes
echo "💾 Committing changes..."
git commit -m "$commit_message" || {
    echo "⚠️  No changes to commit or commit failed"
    echo "If you've already committed, you can push with: git push origin main"
    exit 0
}

echo ""
echo "✅ Changes committed successfully!"
echo ""

# Show commit details
echo "📦 Latest commit:"
echo "-----------------"
git log -1 --stat
echo ""

# Final instructions
echo "🎯 Ready for deployment!"
echo "========================"
echo ""
echo "To push to GitHub, run:"
echo "  git push origin main"
echo ""
echo "Or if you need to set upstream:"
echo "  git push -u origin main"
echo ""
echo "Current branch: $(git branch --show-current)"
echo "Remote URL: $(git remote get-url origin 2>/dev/null || echo 'No remote configured')"
echo ""
echo "✨ All preparation complete!"
