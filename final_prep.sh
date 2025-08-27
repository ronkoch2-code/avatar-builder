#!/bin/bash

# Final preparation for git push
echo "🔧 Making all scripts executable..."

chmod +x fix_model_config.py
chmod +x update_system.py
chmod +x commit_model_fix.sh
chmod +x make_scripts_executable.sh
chmod +x git_push_ready.sh

echo "✅ All scripts are executable"
echo ""
echo "📋 Ready for git operations!"
echo "Run: ./git_push_ready.sh"
