#!/usr/bin/env python3
"""
Trigger Contacts permission request on macOS
This script will prompt the system to ask for Contacts access
Last Updated: September 29, 2025
"""

import sys
import platform

print("=" * 60)
print("Avatar-Engine: Contacts Permission Request")
print("=" * 60)
print()

# Check if we're on macOS
if platform.system() != 'Darwin':
    print("This script is for macOS only.")
    sys.exit(1)

print("This script will request access to your Contacts.")
print("You should see a system dialog asking for permission.")
print()

try:
    # Import the Contacts framework
    import Contacts
    from Foundation import NSBundle
    
    # Get the app name for the permission dialog
    bundle = NSBundle.mainBundle()
    app_name = bundle.infoDictionary().get('CFBundleName', 'Terminal')
    
    print(f"Requesting Contacts access for: {app_name}")
    print()
    
    # Create the contact store
    store = Contacts.CNContactStore.new()
    
    # Check current authorization status
    auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(
        Contacts.CNEntityTypeContacts
    )
    
    status_messages = {
        Contacts.CNAuthorizationStatusNotDetermined: "Not yet determined - will request access now...",
        Contacts.CNAuthorizationStatusRestricted: "Access is restricted by system policy",
        Contacts.CNAuthorizationStatusDenied: "Access was previously denied",
        Contacts.CNAuthorizationStatusAuthorized: "Access is already authorized!",
    }
    
    if hasattr(Contacts, 'CNAuthorizationStatusLimited'):
        status_messages[Contacts.CNAuthorizationStatusLimited] = "Limited access granted"
    
    current_status = status_messages.get(auth_status, f"Unknown status: {auth_status}")
    print(f"Current status: {current_status}")
    print()
    
    if auth_status == Contacts.CNAuthorizationStatusAuthorized:
        print("✅ You already have Contacts access!")
        print("You can now run: python3 main.py extract-contacts")
        sys.exit(0)
    
    elif auth_status == Contacts.CNAuthorizationStatusDenied:
        print("❌ Contacts access was previously denied.")
        print()
        print("To fix this:")
        print("1. Open System Settings")
        print("2. Go to Privacy & Security > Contacts")
        print("3. Find Terminal (or your IDE) in the list")
        print("4. Toggle it ON")
        print()
        print("If you don't see Terminal in the list:")
        print("1. Open System Settings > Privacy & Security > Full Disk Access")
        print("2. Add Terminal to Full Disk Access")
        print("3. Restart Terminal and try again")
        sys.exit(1)
    
    elif auth_status == Contacts.CNAuthorizationStatusRestricted:
        print("❌ Contacts access is restricted by system policy.")
        print("This might be due to MDM or parental controls.")
        sys.exit(1)
    
    elif auth_status == Contacts.CNAuthorizationStatusNotDetermined:
        print("📱 Requesting Contacts access...")
        print("IMPORTANT: Look for a system dialog asking for permission!")
        print()
        
        # Request access - this should trigger the system dialog
        from time import sleep
        import threading
        
        access_granted = [None]  # Use list to modify in closure
        
        def request_callback(granted, error):
            if granted:
                access_granted[0] = True
                print("✅ Access granted!")
            else:
                access_granted[0] = False
                if error:
                    print(f"❌ Access denied: {error}")
                else:
                    print("❌ Access denied by user")
        
        # Make the request
        store.requestAccessForEntityType_completionHandler_(
            Contacts.CNEntityTypeContacts,
            request_callback
        )
        
        # Wait for response (with timeout)
        max_wait = 30  # seconds
        waited = 0
        while access_granted[0] is None and waited < max_wait:
            sleep(0.5)
            waited += 0.5
        
        if access_granted[0] is None:
            print("⏱️ Timed out waiting for response.")
            print("Check if there's a permission dialog on screen.")
        elif access_granted[0]:
            print()
            print("🎉 Success! Contacts access has been granted.")
            print("You can now run: python3 main.py extract-contacts")
        else:
            print()
            print("Access was denied. You can change this in System Settings.")
    
except ImportError as e:
    print(f"❌ Error importing Contacts framework: {e}")
    print()
    print("Please install the required packages:")
    print("pip3 install pyobjc-framework-Contacts pyobjc-framework-Cocoa")
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
