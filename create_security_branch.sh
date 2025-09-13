#!/bin/zsh
# Create new feature branch for security enhancements
# Author: Avatar-Engine Team
# Date: 2025-01-30

echo "========================================="
echo "Creating Security Enhancement Feature Branch"
echo "========================================="

# Check current branch
echo "\n📍 Current branch:"
git branch --show-current

# Check for uncommitted changes
echo "\n📋 Git status:"
git status --short

# Create and checkout new feature branch
BRANCH_NAME="feature/security-enhancements-phase1"
echo "\n🔄 Creating new feature branch: $BRANCH_NAME"
git checkout -b $BRANCH_NAME

# Verify branch creation
echo "\n✅ Now on branch:"
git branch --show-current

echo "\n========================================="
echo "Ready to stage and commit security changes"
echo "========================================="
