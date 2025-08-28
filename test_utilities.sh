#!/bin/bash
# Quick test script for Neo4j utilities

echo "Testing Neo4j Utilities"
echo "======================="

cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Test if utilities can be imported
echo "1. Testing Python imports..."
python3 -c "
import sys
sys.path.append('.')
try:
    from utilities.reset_neo4j import Neo4jResetUtility
    print('   ✓ reset_neo4j module imports successfully')
except ImportError as e:
    print(f'   ✗ Import error: {e}')
"

# Test help commands
echo ""
echo "2. Testing help commands..."
echo "   Testing reset_neo4j.py..."
python3 utilities/reset_neo4j.py --help > /dev/null 2>&1 && echo "   ✓ reset_neo4j.py works" || echo "   ✗ reset_neo4j.py failed"

echo "   Testing backup_neo4j.py..."
python3 utilities/backup_neo4j.py --help > /dev/null 2>&1 && echo "   ✓ backup_neo4j.py works" || echo "   ✗ backup_neo4j.py failed"

echo "   Testing validate_data.py..."
python3 utilities/validate_data.py --help > /dev/null 2>&1 && echo "   ✓ validate_data.py works" || echo "   ✗ validate_data.py failed"

echo ""
echo "3. Checking Neo4j driver..."
python3 -c "
try:
    import neo4j
    print(f'   ✓ Neo4j driver installed (version {neo4j.__version__})')
except ImportError:
    print('   ✗ Neo4j driver not installed - run: pip install neo4j')
"

echo ""
echo "Test complete!"
echo ""
echo "To use the utilities:"
echo "  Dry run reset:    python3 utilities/reset_neo4j.py --dry-run"
echo "  Create backup:    python3 utilities/backup_neo4j.py"
echo "  Validate data:    python3 utilities/validate_data.py"
