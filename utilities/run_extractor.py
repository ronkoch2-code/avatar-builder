#!/usr/bin/env python3
"""
Safe runner for iMessage extractor with environment checks
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check that environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check .env exists
    if not Path('.env').exists():
        print("❌ No .env file found!")
        print("   Run: python3 generate_secure_env.py")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required variables
    if not os.getenv('AVATAR_ENCRYPTION_KEY'):
        print("❌ AVATAR_ENCRYPTION_KEY not set in .env")
        print("   Run: python3 generate_secure_env.py")
        return False
    
    # Check directories
    for dir_path in ['logs', 'data', 'data/extracted', 'data/temp']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Environment configured properly")
    return True

def main():
    """Run the iMessage extractor with proper setup"""
    
    if not check_environment():
        sys.exit(1)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run iMessage extractor safely")
    parser.add_argument('--limit', type=int, help='Message limit')
    parser.add_argument('--output-dir', type=str, help='Output directory')
    parser.add_argument('--no-anonymize', action='store_true', help='Disable anonymization')
    args = parser.parse_args()
    
    # Build command
    cmd_parts = ['python3', 'src/imessage_extractor.py']
    if args.limit:
        cmd_parts.extend(['--limit', str(args.limit)])
    if args.output_dir:
        cmd_parts.extend(['--output-dir', args.output_dir])
    if args.no_anonymize:
        cmd_parts.append('--no-anonymize')
    
    # Run the extractor
    import subprocess
    print(f"\n🚀 Running: {' '.join(cmd_parts)}")
    print("-" * 50)
    
    result = subprocess.run(cmd_parts)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
