#!/usr/bin/osascript
# AppleScript to trigger Contacts permission
# This might work better than Python for permission requests

on run
    tell application "System Events"
        display dialog "This script will request access to your Contacts to extract nicknames for Avatar-Engine.\n\nClick OK to proceed." buttons {"Cancel", "OK"} default button "OK" with title "Avatar-Engine Contacts Access"
    end tell
    
    try
        # Try to access contacts - this should trigger permission
        tell application "Contacts"
            set contactCount to count of people
            display dialog "Success! Found " & contactCount & " contacts.\n\nYou can now run: python3 main.py extract-contacts" buttons {"OK"} default button "OK" with title "Contacts Access Granted"
        end tell
    on error errMsg
        display dialog "Contacts access was denied or failed.\n\nError: " & errMsg & "\n\nPlease check System Settings > Privacy & Security > Contacts" buttons {"OK"} default button "OK" with title "Contacts Access Failed" with icon caution
    end try
end run
