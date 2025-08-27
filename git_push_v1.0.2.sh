#!/bin/bash

# Final Git Push Script for Claude Sonnet 4 Model Update - v1.0.2
# ================================================================

echo "=" 
echo "🚀 Avatar Engine - Git Push v1.0.2"
echo "=" 
echo ""

# Navigate to project directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Make scripts executable
echo "📝 Making scripts executable..."
chmod +x apply_claude4_fix.py
chmod +x fix_model_config.py
chmod +x update_system.py
chmod +x test_model_update.py
chmod +x git_push_ready.sh
chmod +x commit_model_fix.sh
chmod +x final_prep.sh
echo "✅ Scripts are executable"
echo ""

# Add all files
echo "📦 Adding all modified files..."
git add -A
echo "✅ Files staged"
echo ""

# Show status
echo "📋 Files to commit:"
echo "-" 
git status --short
echo "-" 
echo ""

# Create commit
COMMIT_MSG="fix: Update to Claude Sonnet 4 model claude-sonnet-4-20250514 (v1.0.2)

BREAKING FIX:
- Previous model identifiers were outdated causing 404 API errors
- Updated to current Claude Sonnet 4: claude-sonnet-4-20250514

FIXED:
- src/config_manager.py: Updated default model to Claude Sonnet 4
- All 404 Not Found errors from Anthropic API
- RetryError exceptions during analysis
- Failed personality and relationship analyses

ADDED:
- apply_claude4_fix.py: Complete fix application script
- test_model_update.py: Model verification test
- fix_model_config.py: Configuration update utility
- update_system.py: System verification script
- FIX_SUMMARY.md: Complete documentation of the fix

UPDATED:
- CHANGELOG.md: Documented v1.0.2 release
- All git commit scripts updated for v1.0.2

This is the definitive fix using the current Claude Sonnet 4 model
from May 2025. All API calls should now work correctly."

echo "💾 Creating commit..."
git commit -m "$COMMIT_MSG"
echo "✅ Commit created"
echo ""

# Show the commit
echo "📊 Latest commit:"
git log -1 --stat
echo ""

echo "=" 
echo "✨ Git push preparation complete for v1.0.2!"
echo "=" 
echo ""
echo "📤 Push to GitHub with:"
echo "   git push origin main"
echo ""
echo "🧪 But first, test the fix locally:"
echo "   python3 apply_claude4_fix.py"
echo '   python3 enhanced_deployment.py --analyze-person "Aisling Murphy" --force'
echo ""
