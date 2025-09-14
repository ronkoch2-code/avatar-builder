#!/usr/bin/env python3
"""Quick script to check and add SLM files"""
import subprocess
import sys

def git_add_slm():
    commands = [
        "cd /Volumes/FS001/pythonscripts/Avatar-Engine",
        "git add src/slm/*.py",
        "git add examples/slm/*.py", 
        "git add docs/slm/*.md",
        "git add README.md",
        "git status --short | head -20"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}", file=sys.stderr)
        print()

if __name__ == "__main__":
    git_add_slm()
