#!/usr/bin/env python3
"""
Run extraction using local storage to avoid NAS security issues
"""

import sys
import shutil
from pathlib import Path

# Use local storage
LOCAL_TEMP = Path('/tmp/avatar_engine')
LOCAL_TEMP.mkdir(parents=True, exist_ok=True)

# Add src to path
sys.path.insert(0, '/Volumes/FS001/pythonscripts/Avatar-Engine/src')

from imessage_extractor import IMessageExtractor

def run_with_local_storage():
    """Run extraction using local temp storage"""
    
    # Configuration that uses local storage
    config = {
        'temp_dir': str(LOCAL_TEMP / 'temp'),
        'output_dir': str(LOCAL_TEMP / 'extracted'),
        'message_limit': 100,  # Test with 100 messages
        'cleanup_temp': False
    }
    
    print("="*60)
    print("Running Extraction with LOCAL Storage")
    print("="*60)
    print(f"Temp dir: {config['temp_dir']}")
    print(f"Output dir: {config['output_dir']}")
    print()
    
    try:
        extractor = IMessageExtractor(config)
        output_file = extractor.run_extraction_pipeline(message_limit=100)
        
        print(f"\n✅ SUCCESS! Extraction completed")
        print(f"Output: {output_file}")
        
        # Copy result back to NAS
        nas_output = Path('/Volumes/FS001/pythonscripts/Avatar-Engine/data/extracted')
        nas_output.mkdir(parents=True, exist_ok=True)
        
        output_path = Path(output_file)
        if output_path.exists():
            shutil.copy2(output_path, nas_output / output_path.name)
            print(f"\nCopied to NAS: {nas_output / output_path.name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if run_with_local_storage():
        print("\n✅ Using local storage works!")
        print("The issue was NAS volume security restrictions")
    else:
        print("\n❌ Still failing even with local storage")
        print("Try granting Full Disk Access to Python/Terminal")
