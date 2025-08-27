#!/bin/bash
# Quick fix script for Avatar Engine model configuration

echo "🔧 Avatar Engine - Quick Fix for Model Configuration"
echo "====================================================="
echo ""

# Set the correct model via environment variable
export CLAUDE_MODEL="claude-3-5-sonnet-20240620"
echo "✓ Set CLAUDE_MODEL environment variable to: $CLAUDE_MODEL"

# Check if there's a user config file that needs updating
CONFIG_FILE="$HOME/.avatar-engine/avatar_config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "📁 Found user configuration file: $CONFIG_FILE"
    echo ""
    echo "Options:"
    echo "1) Delete the config file (recommended - will use new defaults)"
    echo "2) Keep the config file and override with environment variable"
    echo "3) Exit and manually edit the config file"
    echo ""
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            rm "$CONFIG_FILE"
            echo "✓ Deleted old configuration file"
            echo "  New default settings will be used"
            ;;
        2)
            echo "✓ Keeping config file, using environment variable override"
            ;;
        3)
            echo "ℹ️  Please edit $CONFIG_FILE and change the model to:"
            echo "    \"model\": \"claude-3-5-sonnet-20240620\""
            exit 0
            ;;
        *)
            echo "Invalid option, exiting..."
            exit 1
            ;;
    esac
fi

echo ""
echo "🧪 Testing the configuration..."
echo ""

# Run the diagnostic script
python3 diagnose.py

echo ""
echo "📝 To make the environment variable permanent, add this to your shell config:"
echo "   export CLAUDE_MODEL=\"claude-3-5-sonnet-20240620\""
echo ""
echo "For bash: echo 'export CLAUDE_MODEL=\"claude-3-5-sonnet-20240620\"' >> ~/.bashrc"
echo "For zsh:  echo 'export CLAUDE_MODEL=\"claude-3-5-sonnet-20240620\"' >> ~/.zshrc"
echo ""
echo "✨ Quick fix complete!"
