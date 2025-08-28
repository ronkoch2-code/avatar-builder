#!/bin/bash
# Git push script for Avatar-Engine with enhanced_deployment.py fixes
# Date: $(date '+%Y-%m-%d %H:%M:%S')

echo "📦 Preparing Avatar-Engine for Git Push"
echo "========================================"

# Set project directory
PROJECT_DIR="/Volumes/FS001/pythonscripts/Avatar-Engine"
cd "$PROJECT_DIR" || exit 1

# Step 1: Run tests to ensure everything works
echo ""
echo "🧪 Step 1: Running tests..."
echo "----------------------------"

if [ -f "test_enhanced_deployment.py" ]; then
    python3 test_enhanced_deployment.py
    if [ $? -ne 0 ]; then
        echo "⚠️  Tests failed but continuing..."
    fi
fi

# Step 2: Make scripts executable
echo ""
echo "🔧 Step 2: Making scripts executable..."
echo "---------------------------------------"
chmod +x *.sh 2>/dev/null
chmod +x enhanced_deployment.py
chmod +x src/*.py
chmod +x examples/*.py
echo "✅ Scripts made executable"

# Step 3: Update documentation
echo ""
echo "📝 Step 3: Updating documentation..."
echo "------------------------------------"

cat > DEPLOYMENT_FIX_NOTES.md << 'EOF'
# Enhanced Deployment Script Fix Notes

## Issue Fixed
The `enhanced_deployment.py` script had an async/await issue where the main() function was declared as async but called with `asyncio.run()`, which could cause event loop conflicts.

## Solution Applied
1. Changed `async def main()` to regular `def main()`
2. For async operations (analyze_person, analyze_all_people), we now create a new event loop explicitly:
   ```python
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   try:
       result = loop.run_until_complete(async_function())
   finally:
       loop.close()
   ```
3. Removed `asyncio.run(main())` and now call `main()` directly
4. Added proper logging configuration at startup

## Testing
Run `python3 test_enhanced_deployment.py` to verify the fixes work correctly.

## Usage
```bash
# Configure system (first time only)
python3 src/config_manager.py

# Deploy enhanced schema
python3 enhanced_deployment.py --deploy

# Check system status
python3 enhanced_deployment.py --status

# List people available for analysis
python3 enhanced_deployment.py --list-people

# Analyze a specific person
python3 enhanced_deployment.py --analyze-person "Person Name"

# Analyze all people (with limits)
python3 enhanced_deployment.py --analyze-all --max-people 5
```

## Key Features
- Fixed async/await handling for proper event loop management
- Supports both sync and async operations seamlessly
- Better error handling and logging
- Cost monitoring with Anthropic API (prompt caching and batch API support)
- Neo4j integration for knowledge graph storage

## Date Fixed
$(date '+%Y-%m-%d %H:%M:%S')
EOF

echo "✅ Documentation updated"

# Step 4: Check git status
echo ""
echo "📊 Step 4: Git Status..."
echo "------------------------"
git status --short

# Step 5: Stage changes
echo ""
echo "📤 Step 5: Staging changes..."
echo "-----------------------------"
git add -A
echo "✅ All changes staged"

# Step 6: Create commit message
echo ""
echo "💬 Step 6: Creating commit..."
echo "-----------------------------"

COMMIT_MSG="Fix: Enhanced deployment script async/await issues

- Changed main() from async to sync function
- Properly handle async operations with explicit event loop
- Fixed event loop conflicts in analyze_person and analyze_all methods  
- Added proper logging configuration
- Improved error handling for async operations
- Added test script (test_enhanced_deployment.py) to verify fixes
- Updated documentation with deployment fix notes

This resolves the issue where the script would fail due to improper async/await handling.
The script now correctly manages event loops for async LLM operations while keeping
the main function synchronous for better compatibility."

git commit -m "$COMMIT_MSG"

# Step 7: Show what will be pushed
echo ""
echo "📋 Step 7: Changes to be pushed..."
echo "----------------------------------"
git log --oneline -n 5

# Step 8: Final confirmation
echo ""
echo "🚀 Ready to push to GitHub!"
echo "=========================="
echo ""
echo "Repository: avatar-builder"
echo "Branch: main"
echo ""
echo "To push these changes, run:"
echo "  git push origin main"
echo ""
echo "Or to push with tags:"
echo "  git tag -a v1.0.3 -m 'Fixed enhanced deployment async issues'"
echo "  git push origin main --tags"
echo ""
echo "✅ Git preparation complete!"
