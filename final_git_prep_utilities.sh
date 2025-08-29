#!/bin/bash
# Final preparation for git push - Neo4j Utilities Update

echo "========================================="
echo "FINAL GIT PREPARATION - Neo4j Utilities"
echo "========================================="

cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Make all shell scripts executable
echo "1. Setting executable permissions..."
chmod +x prepare_git_push_utilities.sh
chmod +x test_utilities.sh
chmod +x utilities/make_executable.sh
chmod +x utilities/*.py
echo "   ✓ All scripts are executable"

# Run tests
echo ""
echo "2. Running utility tests..."
chmod +x test_utilities.sh
./test_utilities.sh

# Clean up
echo ""
echo "3. Final cleanup..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ Cleanup complete"

# Git operations
echo ""
echo "4. Git operations..."
git add utilities/
git add .gitignore
git add prepare_git_push_utilities.sh
git add test_utilities.sh

# Show final status
echo ""
echo "5. Final Git Status:"
echo "----------------------------------------"
git status

echo ""
echo "========================================="
echo "✅ READY FOR GIT COMMIT AND PUSH"
echo "========================================="
echo ""
echo "Execute the following commands:"
echo ""
echo "git commit -m \"feat: Add comprehensive Neo4j database utilities"
echo ""
echo "- Added reset_neo4j.py for safe database resets"
echo "- Added backup_neo4j.py for JSON/Cypher backups"  
echo "- Added validate_data.py for integrity checks"
echo "- Created organized utilities directory structure"
echo "- Preserves schema while clearing data"
echo "- Includes safety features (dry-run, auto-backup)\""
echo ""
echo "git push origin main"
echo ""
echo "========================================="
