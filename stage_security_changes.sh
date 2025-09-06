#!/bin/zsh
# Stage and commit security enhancement changes
# Author: Avatar-Engine Team  
# Date: 2025-01-30

echo "========================================="
echo "Git Workflow for Security Enhancements"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check current branch
echo "\n${YELLOW}Step 1: Checking current branch...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "${RED}Warning: Not on main branch!${NC}"
    echo "Please run from main branch or adjust as needed."
fi

# Step 2: Create feature branch if not exists
BRANCH_NAME="feature/security-enhancements-phase1"
echo "\n${YELLOW}Step 2: Creating feature branch...${NC}"

# Check if branch already exists
if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo "Branch $BRANCH_NAME already exists. Checking out..."
    git checkout $BRANCH_NAME
else
    echo "Creating new branch: $BRANCH_NAME"
    git checkout -b $BRANCH_NAME
fi

# Step 3: Check for changes
echo "\n${YELLOW}Step 3: Checking for changes...${NC}"
git status --short

# Step 4: Stage security-related files
echo "\n${YELLOW}Step 4: Staging security enhancement files...${NC}"

# New security files
echo "Adding new security modules..."
git add src/security_utils.py
git add src/secure_database.py
git add tests/test_security_phase1.py
git add DEVELOPMENT_STATE.md
git add SECURITY_ENHANCEMENTS.md

# Modified files for security
echo "Adding modified files..."
git add src/config_manager.py
git add src/llm_integrator.py
git add src/message_data_loader.py
git add requirements.txt

# Add the git helper scripts
git add create_security_branch.sh
git add stage_security_changes.sh

# Optional: Add .env.example if modified
if [[ -f ".env.example" ]]; then
    git add .env.example
fi

# Step 5: Show what will be committed
echo "\n${YELLOW}Step 5: Files staged for commit:${NC}"
git status --short --branch

# Step 6: Create commit
echo "\n${YELLOW}Step 6: Creating commit...${NC}"
echo "${GREEN}Commit message preview:${NC}"
cat << 'EOF'
feat(security): Implement comprehensive security enhancements (Phase 1)

SECURITY IMPROVEMENTS:
- Implement secure API key management with environment variables
- Add database query parameterization to prevent SQL injection
- Create data encryption utilities for sensitive information
- Add phone number anonymization for PII protection
- Fix JSON parsing vulnerability in LLM integrator
- Implement rate limiting for API and database operations
- Add comprehensive input validation and sanitization
- Create secure logging with automatic PII redaction

NEW MODULES:
- src/security_utils.py: Core security utilities (encryption, validation)
- src/secure_database.py: Secure Neo4j wrapper with parameterized queries
- tests/test_security_phase1.py: Comprehensive security test suite

MODIFIED MODULES:
- src/config_manager.py: Secure credential management
- src/llm_integrator.py: Fixed JSON extraction vulnerability
- src/message_data_loader.py: Added data anonymization

SECURITY FEATURES:
✅ All database queries now parameterized (injection-safe)
✅ API keys stored securely, never logged
✅ Phone numbers anonymized by default
✅ Rate limiting prevents abuse
✅ Comprehensive error handling with retry logic
✅ Audit logging without PII exposure
✅ Input validation blocks malicious content
✅ Encryption available for sensitive data

BREAKING CHANGES:
- MessageDataLoader now uses secure connections by default
- Neo4j password is required (no empty passwords)
- API keys must be in environment variables

Testing: Run tests/test_security_phase1.py to validate all security features

Refs: #security-phase1
EOF

echo "\n${YELLOW}Do you want to commit with this message? (y/n)${NC}"
read -r response

if [[ "$response" == "y" || "$response" == "Y" ]]; then
    git commit -m "feat(security): Implement comprehensive security enhancements (Phase 1)

SECURITY IMPROVEMENTS:
- Implement secure API key management with environment variables
- Add database query parameterization to prevent SQL injection
- Create data encryption utilities for sensitive information
- Add phone number anonymization for PII protection
- Fix JSON parsing vulnerability in LLM integrator
- Implement rate limiting for API and database operations
- Add comprehensive input validation and sanitization
- Create secure logging with automatic PII redaction

NEW MODULES:
- src/security_utils.py: Core security utilities (encryption, validation)
- src/secure_database.py: Secure Neo4j wrapper with parameterized queries
- tests/test_security_phase1.py: Comprehensive security test suite

MODIFIED MODULES:
- src/config_manager.py: Secure credential management
- src/llm_integrator.py: Fixed JSON extraction vulnerability
- src/message_data_loader.py: Added data anonymization

SECURITY FEATURES:
✅ All database queries now parameterized (injection-safe)
✅ API keys stored securely, never logged
✅ Phone numbers anonymized by default
✅ Rate limiting prevents abuse
✅ Comprehensive error handling with retry logic
✅ Audit logging without PII exposure
✅ Input validation blocks malicious content
✅ Encryption available for sensitive data

BREAKING CHANGES:
- MessageDataLoader now uses secure connections by default
- Neo4j password is required (no empty passwords)
- API keys must be in environment variables

Testing: Run tests/test_security_phase1.py to validate all security features

Refs: #security-phase1"
    
    echo "\n${GREEN}✅ Commit created successfully!${NC}"
    
    # Step 7: Show the commit
    echo "\n${YELLOW}Step 7: Commit details:${NC}"
    git show --stat HEAD
    
    echo "\n${GREEN}=========================================${NC}"
    echo "${GREEN}Security enhancements committed to $BRANCH_NAME${NC}"
    echo "${GREEN}=========================================${NC}"
    
    echo "\n${YELLOW}Next steps:${NC}"
    echo "1. Test the security features: python3 tests/test_security_phase1.py"
    echo "2. Push to remote: git push -u origin $BRANCH_NAME"
    echo "3. Create a pull request to merge into main"
    echo "4. Get code review before merging"
    
else
    echo "\n${YELLOW}Commit cancelled. Files remain staged.${NC}"
    echo "You can commit manually with: git commit -m 'your message'"
fi
