#!/bin/bash
# Test Python Detection Script

echo "🐍 Testing Python Detection for Avatar Intelligence System"
echo "========================================================="

# Test different Python executables
echo "Available Python executables:"

if command -v python3 >/dev/null 2>&1; then
    echo "✅ python3 found: $(python3 --version)"
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    echo "✅ python found: $(python --version)"
    PYTHON_CMD="python"
else
    echo "❌ No Python executable found"
    exit 1
fi

echo ""
echo "🎯 Recommended Python command: $PYTHON_CMD"
echo ""

# Test make variable detection
echo "Testing Makefile Python detection..."
DETECTED_PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python)
echo "Makefile will use: $DETECTED_PYTHON"

# Test basic import
echo ""
echo "Testing Python imports..."
$PYTHON_CMD -c "
import sys
print(f'✅ Python {sys.version} working')
try:
    import neo4j
    print('✅ neo4j module available')
except ImportError:
    print('⚠️  neo4j module not installed (run: pip install neo4j)')

try:
    import pandas
    print('✅ pandas module available')
except ImportError:
    print('⚠️  pandas module not installed (run: pip install pandas)')

try:
    import pytest
    print('✅ pytest module available')
except ImportError:
    print('⚠️  pytest module not installed (run: pip install pytest)')
" 2>/dev/null

echo ""
echo "🎉 Python detection test complete!"
echo ""
echo "If tests are failing, try:"
echo "  make test PYTHON=$PYTHON_CMD"
echo "  or"
echo "  $PYTHON_CMD run_tests.py"
