#!/bin/bash
# Make all shell scripts executable

echo "Setting execute permissions on all shell scripts..."
chmod +x *.sh
chmod +x enhanced_deployment.py
chmod +x src/*.py
chmod +x examples/*.py
chmod +x test_enhanced_deployment.py

echo "✅ All scripts are now executable"
echo ""
echo "Available scripts:"
ls -la *.sh | awk '{print "  " $9}'
