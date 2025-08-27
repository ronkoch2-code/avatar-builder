#!/bin/bash

# Complete Git Push Preparation Script
# =====================================
# This script prepares all changes for pushing to GitHub

echo "=" * 60
echo "🚀 Avatar Engine - Git Push Preparation"
echo "=" * 60
echo ""

# Navigate to project directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Step 1: Make scripts executable
echo "Step 1: Making scripts executable..."
chmod +x fix_model_config.py
chmod +x update_system.py
chmod +x commit_model_fix.sh
chmod +x make_scripts_executable.sh
echo "✅ Scripts are now executable"
echo ""

# Step 2: Add all modified files
echo "Step 2: Adding modified files to git..."
git add -A
echo "✅ Files added to staging"
echo ""

# Step 3: Show what's being committed
echo "Step 3: Files to be committed:"
echo "-" * 40
git status --short
echo "-" * 40
echo ""

# Step 4: Create comprehensive commit message
COMMIT_MSG="fix: Update Claude model to fix 404 API errors (v1.0.2)

FIXED:
- Updated Claude model from claude-3-5-sonnet-20240620 to claude-sonnet-4-20250514 (Claude 4)
- Resolved 404 Not Found errors when making LLM API calls
- Fixed RetryError issues in personality and relationship analysis

ADDED:
- fix_model_config.py: Utility to update existing user configurations
- update_system.py: Complete system update and verification script
- make_scripts_executable.sh: Helper to set execute permissions

MODIFIED:
- src/config_manager.py: Updated default model identifier
- CHANGELOG.md: Documented v1.0.1 release with fixes

This update ensures compatibility with current Anthropic API models."

# Step 5: Commit the changes
echo "Step 5: Creating commit..."
git commit -m "$COMMIT_MSG"
echo "✅ Commit created"
echo ""

# Step 6: Show commit info
echo "Step 6: Latest commit:"
echo "-" * 40
git log -1 --oneline
echo "-" * 40
echo ""

# Step 7: Push to GitHub
echo "Step 7: Ready to push to GitHub!"
echo ""
echo "📤 To push changes, run:"
echo "   git push origin main"
echo ""
echo "Or if you need to set upstream:"
echo "   git push -u origin main"
echo ""
echo "✨ Preparation complete!"
