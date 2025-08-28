#!/bin/bash
# Quick test of enhanced_deployment.py fixes

echo "🧪 Testing Enhanced Deployment Script Fixes"
echo "==========================================="
echo ""

# Run the test script
python3 test_enhanced_deployment.py

echo ""
echo "🎯 Testing actual script with --help option:"
echo "----------------------------------------"
python3 enhanced_deployment.py --help 2>&1 | head -20

echo ""
echo "✅ If you see the help text above, the script is working!"
echo ""
echo "Next steps:"
echo "1. Configure API keys: python3 src/config_manager.py"
echo "2. Deploy schema: python3 enhanced_deployment.py --deploy"
echo "3. Check status: python3 enhanced_deployment.py --status"
echo "4. List people: python3 enhanced_deployment.py --list-people"
