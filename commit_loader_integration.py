#!/usr/bin/env python3
"""
Git commit helper for message loader integration
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                          cwd="/Volumes/FS001/pythonscripts/Avatar-Engine")
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 60)
    print("Avatar-Engine: Message Data Loader Integration")
    print("=" * 60)
    
    # Check git status
    print("\n📊 Checking git status...")
    code, stdout, stderr = run_command("git status --short")
    if stdout:
        print("Files to commit:")
        print(stdout)
    
    # Add files
    print("\n📁 Adding new files...")
    files_to_add = [
        "src/message_data_loader.py",
        "docs/message_data_loading.md",
        "git_push_loader_integration.sh"
    ]
    
    for file in files_to_add:
        code, _, _ = run_command(f"git add {file}")
        if code == 0:
            print(f"  ✅ Added: {file}")
        else:
            print(f"  ❌ Failed to add: {file}")
    
    # Commit
    print("\n💾 Committing changes...")
    commit_message = """feat: Add message data loader pipeline

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
project directory. The loader is now fully integrated into Avatar-Engine."""
    
    code, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if code == 0:
        print("✅ Successfully committed changes!")
        print(stdout)
    else:
        print("❌ Commit failed:")
        print(stderr)
    
    # Show final status
    print("\n📊 Final git status:")
    code, stdout, _ = run_command("git status")
    print(stdout)
    
    print("\n" + "=" * 60)
    print("✨ Integration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test the loader: python3 src/message_data_loader.py --help")
    print("2. Load data: python3 src/message_data_loader.py /path/to/data.db --password YOUR_PASSWORD")
    print("3. Push to GitHub: git push origin main")
    print("\nThe message data loading pipeline has been successfully restored!")

if __name__ == "__main__":
    main()
