#!/bin/bash
# Avatar Engine - Final deployment preparation with model fix
# This script ensures all fixes are applied and prepares for git deployment

set -e  # Exit on any error

echo "🚀 Avatar Engine - Complete Fix & Deployment Preparation"
echo "========================================================="
echo ""
echo "This script will:"
echo "1. Fix the Claude model configuration"
echo "2. Run diagnostics"
echo "3. Prepare changes for git push"
echo ""

# Step 1: Set correct environment variable
echo "Step 1: Setting environment variable..."
export CLAUDE_MODEL="claude-3-5-sonnet-20240620"
echo "✓ CLAUDE_MODEL set to: $CLAUDE_MODEL"
echo ""

# Step 2: Check and fix configuration
echo "Step 2: Checking configuration..."
python3 fix_config.py
echo ""

# Step 3: Run diagnostics
echo "Step 3: Running diagnostics..."
python3 diagnose.py
echo ""

# Step 4: Test the model configuration
echo "Step 4: Testing model configuration..."
python3 test_model_update.py
echo ""

# Step 5: Prepare git changes
echo "Step 5: Preparing git changes..."
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Show current status
echo "📊 Current Git Status:"
git status --short
echo ""

# Add all modified files
git add -A

# Create commit message
commit_message="fix: Correct Claude model to claude-3-5-sonnet-20240620

This fixes the 404 API errors by using the correct, currently available model.

Changes:
- Updated model from claude-3-sonnet-20240229 to claude-3-5-sonnet-20240620
- Added diagnostic and fix scripts
- Updated all configuration references

The correct current models are:
- claude-3-5-sonnet-20240620 (recommended)
- claude-3-opus-20240229
- claude-3-haiku-20240307

Files modified:
- src/config_manager.py
- enhanced_deployment.py
- test_model_update.py
- Added: diagnose.py, fix_config.py, quick_fix.sh

Tested and verified working."

# Commit changes
echo "💾 Committing changes..."
git commit -m "$commit_message" || {
    echo "ℹ️  No changes to commit or already committed"
}

echo ""
echo "✅ All fixes applied and ready for deployment!"
echo ""
echo "📋 Summary of fixes:"
echo "  • Model updated to: claude-3-5-sonnet-20240620"
echo "  • Configuration files checked and fixed"
echo "  • Diagnostic tools added"
echo "  • All changes committed to git"
echo ""
echo "🎯 Next step - Push to GitHub:"
echo "  git push origin main"
echo ""
echo "If you still get errors, run:"
echo "  ./quick_fix.sh"
echo "Or check the diagnostics:"
echo "  python3 diagnose.py"
echo ""
echo "✨ Deployment preparation complete!"
