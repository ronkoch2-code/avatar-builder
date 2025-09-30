#!/usr/bin/env python3
"""
Create a minimal macOS app bundle to properly request Contacts permission
This works around the Terminal permission issues
Last Updated: September 29, 2025
"""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>avatar_contacts</string>
    <key>CFBundleIdentifier</key>
    <string>com.avatar-engine.contacts</string>
    <key>CFBundleName</key>
    <string>Avatar Contacts</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSContactsUsageDescription</key>
    <string>Avatar-Engine needs access to your contacts to extract nicknames and build your personal knowledge graph.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
"""

PYTHON_SCRIPT = """#!/usr/bin/env python3
import sys
sys.path.insert(0, '{project_path}')
sys.path.insert(0, '{project_path}/src')

try:
    import Contacts
    from Foundation import NSBundle
    import AppKit
    
    # Initialize the app
    app = AppKit.NSApplication.sharedApplication()
    
    # Create contact store
    store = Contacts.CNContactStore.new()
    
    # Check authorization
    auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(
        Contacts.CNEntityTypeContacts
    )
    
    if auth_status == Contacts.CNAuthorizationStatusAuthorized:
        print("✅ Contacts access already authorized!")
        sys.exit(0)
    
    # Request access
    def callback(granted, error):
        if granted:
            print("✅ Contacts access granted!")
        else:
            print(f"❌ Access denied: {{error}}")
        AppKit.NSApplication.sharedApplication().terminate_(None)
    
    store.requestAccessForEntityType_completionHandler_(
        Contacts.CNEntityTypeContacts,
        callback
    )
    
    # Run the app briefly to handle the callback
    app.run()
    
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

def create_app_bundle():
    """Create a temporary macOS app bundle"""
    print("Creating temporary macOS app bundle...")
    
    # Get project path
    project_path = Path(__file__).parent.absolute()
    
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp(prefix="avatar_contacts_"))
    app_path = temp_dir / "AvatarContacts.app"
    
    # Create app structure
    contents = app_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    
    os.makedirs(macos)
    os.makedirs(resources)
    
    # Write Info.plist
    plist_path = contents / "Info.plist"
    plist_path.write_text(PLIST_TEMPLATE)
    
    # Write executable script
    script_path = macos / "avatar_contacts"
    script_content = PYTHON_SCRIPT.format(project_path=str(project_path))
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    return app_path

def main():
    print("=" * 60)
    print("Avatar-Engine: App Bundle Contacts Permission Request")
    print("=" * 60)
    print()
    
    try:
        # Create app bundle
        app_path = create_app_bundle()
        print(f"Created app bundle at: {app_path}")
        print()
        
        print("Launching app to request Contacts permission...")
        print("LOOK FOR THE PERMISSION DIALOG!")
        print()
        
        # Run the app
        result = subprocess.run(
            ["open", "-W", str(app_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ App launched successfully!")
        else:
            print(f"⚠️ App launch returned code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        
        # Check the output
        exec_path = app_path / "Contents" / "MacOS" / "avatar_contacts"
        result = subprocess.run(
            [str(exec_path)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
        # Cleanup
        print("\nCleaning up temporary app...")
        shutil.rmtree(app_path.parent)
        
        print("\n" + "=" * 60)
        print("If permission was granted, you can now run:")
        print("  python3 main.py extract-contacts")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
