#!/usr/bin/env python3
"""
Generate secure environment configuration for Avatar-Engine
===========================================================

This script generates secure keys and creates a properly configured .env file
with all required environment variables for Avatar-Engine.

Usage:
    python3 generate_secure_env.py
"""

import os
import secrets
import string
from pathlib import Path
from cryptography.fernet import Fernet


def generate_secure_password(length=20):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_env_file():
    """Generate a secure .env file with all required variables"""
    
    # Generate secure keys
    encryption_key = Fernet.generate_key().decode()
    key_salt = secrets.token_urlsafe(32)
    hash_salt = secrets.token_urlsafe(24)
    
    env_content = f"""# Avatar-Engine Environment Configuration
# Generated securely on {os.popen('date').read().strip()}
# ========================================
# SECURITY WARNING: This file contains sensitive credentials.
# Never commit this file to version control!

# ====================
# DATABASE CONFIGURATION
# ====================

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
# IMPORTANT: Change this password to match your Neo4j installation
NEO4J_PASSWORD=CHANGE_THIS_NEO4J_PASSWORD
NEO4J_DATABASE=neo4j

# ====================
# API CONFIGURATION
# ====================

# Add your Anthropic API key here
ANTHROPIC_API_KEY=sk-ant-YOUR_API_KEY_HERE
CLAUDE_MODEL=claude-sonnet-4-20250514

# ====================
# SECURITY CONFIGURATION
# ====================

# Encryption key (auto-generated - DO NOT SHARE)
AVATAR_ENCRYPTION_KEY={encryption_key}

# Key derivation salt (auto-generated)
AVATAR_KEY_SALT={key_salt}

# Hash salt for PII anonymization (auto-generated)
AVATAR_HASH_SALT={hash_salt}

# ====================
# SYSTEM CONFIGURATION
# ====================

LOG_LEVEL=INFO
LOG_FILE=logs/avatar_engine.log

# Cost Management
DAILY_COST_LIMIT=50.0
COST_ALERT_THRESHOLD=20.0

# ====================
# ANALYSIS CONFIGURATION
# ====================

MIN_MESSAGES_FOR_ANALYSIS=50
MAX_MESSAGES_PER_ANALYSIS=1000
MIN_CONFIDENCE_SCORE=0.3
HIGH_CONFIDENCE_THRESHOLD=0.7

# Feature Toggles
PERSONALITY_ANALYSIS_ENABLED=true
RELATIONSHIP_ANALYSIS_ENABLED=true
TOPIC_ANALYSIS_ENABLED=true
EMOTIONAL_ANALYSIS_ENABLED=true

# ====================
# IMESSAGE EXTRACTION
# ====================

IMESSAGE_OUTPUT_DIR=data/extracted
IMESSAGE_TEMP_DIR=data/temp
IMESSAGE_ANONYMIZE_PHONES=true
IMESSAGE_BATCH_SIZE=1000
IMESSAGE_CLEANUP_TEMP=true

# ====================
# PERFORMANCE SETTINGS
# ====================

ASYNC_PROCESSING=true
BATCH_SIZE=10
RETRY_ATTEMPTS=3
MAX_CONCURRENT_REQUESTS=3
RATE_LIMIT_PER_MINUTE=50

# ====================
# BACKUP CONFIGURATION
# ====================

BACKUP_ENABLED=true
BACKUP_INTERVAL_HOURS=24
BACKUP_LOCATION=backups/

# ====================
# NOTES
# ====================
# 1. Update NEO4J_PASSWORD with your actual Neo4j password
# 2. Add your Anthropic API key if you want to use LLM features
# 3. Keep this file secure and never share it
# 4. For production, use a proper secret management service
"""
    
    # Check if .env already exists
    env_path = Path('.env')
    if env_path.exists():
        backup_path = Path('.env.backup')
        print(f"⚠️  Existing .env file found. Backing up to {backup_path}")
        env_path.rename(backup_path)
    
    # Write new .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions (Unix/Linux/Mac only)
    try:
        os.chmod('.env', 0o600)  # Read/write for owner only
        print("✅ Set secure file permissions (600)")
    except:
        print("⚠️  Could not set file permissions (may not be supported on this OS)")
    
    print(f"""
✅ Secure .env file generated successfully!

🔐 Security Keys Generated:
   - Encryption key: {encryption_key[:20]}... (truncated)
   - Key salt: {key_salt[:20]}... (truncated)
   - Hash salt: {hash_salt[:20]}... (truncated)

📝 Next Steps:
   1. Edit .env and update NEO4J_PASSWORD with your actual password
   2. Add your Anthropic API key if using LLM features
   3. Review and adjust other settings as needed
   
⚠️  IMPORTANT:
   - Never commit .env to version control
   - Keep these keys secure
   - Use different keys for production
""")


if __name__ == "__main__":
    generate_env_file()
