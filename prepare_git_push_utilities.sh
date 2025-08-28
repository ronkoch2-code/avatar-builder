#!/bin/bash
# Prepare Avatar-Engine for Git push
# This script ensures all files are properly organized and ready for commit

echo "========================================="
echo "Avatar-Engine Git Preparation Script"
echo "========================================="

# Navigate to project root
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Make utility scripts executable
echo "1. Making utility scripts executable..."
chmod +x utilities/*.py
chmod +x utilities/make_executable.sh
echo "   ✓ Utilities are executable"

# Clean up Python cache files
echo "2. Cleaning up Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✓ Cache cleaned"

# Create necessary directories if they don't exist
echo "3. Ensuring directory structure..."
mkdir -p utilities/backups 2>/dev/null || true
mkdir -p utilities/reports 2>/dev/null || true
echo "   ✓ Directory structure verified"

# Update documentation
echo "4. Documentation status..."
if [ -f "utilities/README.md" ]; then
    echo "   ✓ Utilities README exists"
else
    echo "   ⚠ Utilities README missing"
fi

# Git status check
echo ""
echo "5. Git Status:"
echo "----------------------------------------"
git status --short

# Count changes
MODIFIED=$(git status --short | grep -c "^ M" || true)
ADDED=$(git status --short | grep -c "^??" || true)
DELETED=$(git status --short | grep -c "^ D" || true)

echo ""
echo "Summary:"
echo "  Modified files: $MODIFIED"
echo "  New files: $ADDED"
echo "  Deleted files: $DELETED"

# Stage new utilities
echo ""
echo "6. Staging new utilities..."
git add utilities/
git add .gitignore

# Show what will be committed
echo ""
echo "7. Files staged for commit:"
echo "----------------------------------------"
git diff --cached --name-status

# Prepare commit message
echo ""
echo "========================================="
echo "Ready for commit!"
echo ""
echo "Suggested commit message:"
echo "----------------------------------------"
echo "feat: Add Neo4j database utilities"
echo ""
echo "- Added reset_neo4j.py for safe database resets"
echo "- Added backup_neo4j.py for comprehensive backups"
echo "- Added validate_data.py for data integrity checks"
echo "- Created utilities directory structure"
echo "- Added proper .gitignore files"
echo "- Preserves schema while clearing data"
echo "- Includes safety features (dry-run, backups)"
echo ""
echo "To commit and push:"
echo "  git commit -m \"feat: Add Neo4j database utilities\""
echo "  git push origin main"
echo "========================================="
