#!/bin/bash
# Reset and request Contacts permission using various methods
# Last Updated: September 29, 2025

echo "========================================"
echo "Avatar-Engine: Fix Contacts Permissions"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "This script will try multiple methods to fix Contacts permission."
echo ""

# Method 1: Reset permissions using tccutil
echo -e "${YELLOW}Method 1: Reset Contacts permissions${NC}"
echo "This will reset the permission state so you get asked again."
echo "You may need to enter your password."
echo ""

# Try to reset Python permissions
tccutil reset AddressBook com.apple.Terminal 2>/dev/null
tccutil reset Contacts com.apple.Terminal 2>/dev/null
tccutil reset AddressBook org.python.python 2>/dev/null
tccutil reset Contacts org.python.python 2>/dev/null

# Also try for Python3
tccutil reset AddressBook Python 2>/dev/null
tccutil reset Contacts Python 2>/dev/null

echo -e "${GREEN}✓${NC} Permission state reset"
echo ""

# Method 2: Create a simple AppleScript app
echo -e "${YELLOW}Method 2: Creating AppleScript app${NC}"

# Create a temporary AppleScript application
SCRIPT_CONTENT='
tell application "Contacts"
    set contactCount to count of people
    display dialog "Found " & contactCount & " contacts. Permissions working!" buttons {"OK"}
end tell
'

# Save as an application
TEMP_APP="/tmp/AvatarContactsTest.app"
rm -rf "$TEMP_APP" 2>/dev/null

echo "$SCRIPT_CONTENT" | osacompile -o "$TEMP_APP" 2>/dev/null

if [ -f "$TEMP_APP/Contents/MacOS/applet" ]; then
    echo -e "${GREEN}✓${NC} Created temporary app at $TEMP_APP"
    echo ""
    echo "Launching app - LOOK FOR PERMISSION DIALOG!"
    open -W "$TEMP_APP"
else
    echo -e "${RED}✗${NC} Could not create AppleScript app"
fi

echo ""
echo "========================================"
echo "After granting permission, test with:"
echo "  python3 test_mock_nicknames.py    # Test with mock data"
echo "  python3 main.py extract-contacts  # Extract real contacts"
echo ""
echo "If still having issues, try:"
echo "  1. Restart Terminal"
echo "  2. Grant Full Disk Access to Terminal in System Settings"
echo "  3. Use the mock data for testing"
echo "========================================"
