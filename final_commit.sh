#!/bin/bash
# Final git commit for message loader integration

cd /Volumes/FS001/pythonscripts/Avatar-Engine

# Add all new files
git add src/message_data_loader.py
git add docs/message_data_loading.md
git add git_push_loader_integration.sh
git add commit_loader_integration.py

# Commit with comprehensive message
git commit -m "feat: Add message data loader pipeline

- Integrated message loading functionality from iMessage Autoprocessor  
- Added support for SQLite and JSON data sources
- Implemented sophisticated message text cleaning
- Created batch processing for efficient data loading
- Added comprehensive documentation
- Established Neo4j graph structure (Person, Message, GroupChat nodes)
- Included command-line interface and Python API
- Resolves missing pipeline functionality for data extraction and loading

This restores the critical functionality for loading message data
from external sources into Neo4j, which was previously in a separate
project directory. The loader is now fully integrated into Avatar-Engine."

# Show result
echo "✅ Changes committed successfully!"
git log --oneline -1
