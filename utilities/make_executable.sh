#!/bin/bash
# Make all utility scripts executable

echo "Making utility scripts executable..."

# Navigate to utilities directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine/utilities

# Make Python scripts executable
chmod +x reset_neo4j.py
chmod +x backup_neo4j.py
chmod +x validate_data.py

echo "✓ All utility scripts are now executable"

# Display script status
echo ""
echo "Available utilities:"
ls -la *.py | grep -E "^-rwx"
