#!/bin/bash

# Git commit script for model update fix
echo "🔧 Preparing git commit for model update fix..."

# Navigate to the project directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Add all changed files
echo "📦 Adding updated files..."
git add src/config_manager.py
git add fix_model_config.py
git add update_system.py
git add CHANGELOG.md

# Show status
echo "📋 Current git status:"
git status

# Create commit message
COMMIT_MSG="fix: Update Claude model identifier to fix 404 API errors (v1.0.2)

- Changed model from claude-3-5-sonnet-20240620 to claude-sonnet-4-20250514
- This is the current Claude Sonnet 4 model from May 2025
- Added fix_model_config.py utility to update existing configurations
- Added update_system.py for complete system verification and update
- Added test_model_update.py to verify the model configuration
- Updated CHANGELOG.md with version 1.0.2

This fixes the 404 Not Found errors when making LLM API calls."

# Commit the changes
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

echo "✅ Commit complete!"
echo ""
echo "📤 To push to GitHub, run:"
echo "   git push origin main"
echo ""
echo "Or use the full push script:"
echo "   ./prepare_git_push.sh"
