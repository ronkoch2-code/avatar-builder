#!/bin/bash
# Prepare and push message data loader integration

echo "================================================"
echo "Avatar-Engine: Message Data Loader Integration"
echo "================================================"

# Navigate to project directory
cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Make script executable
chmod +x git_push_loader_integration.sh

# Add the new files
git add src/message_data_loader.py
git add docs/message_data_loading.md
git add git_push_loader_integration.sh

# Commit the changes
git commit -m "feat: Add message data loader pipeline

- Integrated message loading functionality from iMessage Autoprocessor
- Added support for SQLite and JSON data sources
- Implemented sophisticated message text cleaning
- Created batch processing for efficient data loading
- Added comprehensive documentation
- Established Neo4j graph structure (Person, Message, GroupChat nodes)
- Included command-line interface and Python API
- Resolves missing pipeline functionality for data extraction and loading"

# Show status
git status

echo ""
echo "================================================"
echo "Integration complete! Next steps:"
echo "================================================"
echo "1. Test the loader: python3 src/message_data_loader.py --help"
echo "2. Load your data: python3 src/message_data_loader.py /path/to/data --password YOUR_PASSWORD"
echo "3. Push to GitHub: git push origin main"
echo ""
echo "The message data loading pipeline has been successfully restored!"
