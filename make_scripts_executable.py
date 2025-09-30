#!/usr/bin/env python3
"""Make scripts executable"""
import os
import stat

scripts = [
    'fix_contacts_permission.sh',
    'request_contacts_applescript.scpt'
]

for script in scripts:
    try:
        # Add execute permissions
        st = os.stat(script)
        os.chmod(script, st.st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP)
        print(f"✓ Made executable: {script}")
    except FileNotFoundError:
        print(f"⚠ File not found: {script}")
    except Exception as e:
        print(f"⚠ Error with {script}: {e}")

print("\nScripts are ready!")
