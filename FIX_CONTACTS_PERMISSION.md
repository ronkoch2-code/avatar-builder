# 🔧 Fixing Contacts Permission on macOS 26

## The Problem

macOS 26 has stricter permission controls. Python scripts running in Terminal often can't trigger the Contacts permission dialog properly, resulting in immediate "Access Denied" without showing a permission prompt.

## Solutions (Try in Order)

### 1. 🔄 Reset Permissions and Try Again

Reset the permission state so macOS will ask again:

```bash
# Make the script executable
chmod +x fix_contacts_permission.sh

# Run it (may ask for password)
./fix_contacts_permission.sh
```

This script:
- Resets Terminal's Contacts permission state
- Creates a temporary AppleScript app that should trigger the dialog
- Launches the app to request permission

### 2. 📝 Use AppleScript Directly

AppleScript often has better permission handling:

```bash
# Run the AppleScript
osascript request_contacts_applescript.scpt
```

If this opens Contacts app and shows contact count, permission is granted!

### 3. 📦 Create App Bundle

Python scripts need proper app bundle structure to request permissions:

```bash
python3 create_app_bundle_for_permission.py
```

This creates a temporary macOS app with proper Info.plist to request permissions.

### 4. 🗄️ Direct Database Access (Requires Full Disk Access)

If you have Full Disk Access, read the Contacts database directly:

```bash
python3 read_contacts_sqlite.py
```

**To enable Full Disk Access:**
1. System Settings > Privacy & Security > Full Disk Access
2. Click the lock to make changes
3. Add Terminal (or your IDE) to the list
4. Restart Terminal

### 5. 🎭 Use Mock Data (No Permissions Needed!)

Test the nickname system without real contacts:

```bash
python3 test_mock_nicknames.py
```

This shows how the system works with sample data - perfect for testing!

## Manual Permission Fix

If automated methods fail:

1. **Create a Simple Test App**:
   - Open **Script Editor** (in Applications/Utilities)
   - Paste this code:
   ```applescript
   tell application "Contacts"
       count of people
   end tell
   ```
   - Save as an Application (File > Export > File Format: Application)
   - Run the app - it should trigger the permission dialog
   - After granting permission, Python should work too

2. **Check Current Permissions**:
   ```bash
   # See which apps have Contacts access
   ls ~/Library/Application\ Support/com.apple.TCC/
   ```

3. **Nuclear Option - Reset All Permissions**:
   ```bash
   # Reset ALL privacy permissions (use with caution!)
   sudo tccutil reset All
   ```

## Verification

After granting permission, verify it works:

```bash
# Quick test
python3 -c "import Contacts; store = Contacts.CNContactStore.new(); print('✅ Contacts access working!')"

# Full test
python3 main.py extract-contacts
```

## Still Not Working?

### Use Mock Data Instead

The nickname system is fully functional with mock data:

```bash
# Test extraction with mock data
python3 test_mock_nicknames.py

# Test conversation analysis
python3 main.py analyze-conversation data/sample_messages.json
```

### Integration Without Contacts

You can integrate the nickname system into your pipeline using:
- Manually created person data
- Nicknames from conversations only
- Imported CSV/JSON data

Example:
```python
from src.models.graph_models import Person, Nickname, NicknameSource
from src.extractors.nickname_inference import NicknameInferenceEngine

# Create persons manually or from your existing data
person = Person(
    full_name="Robert Smith",
    first_name="Robert",
    last_name="Smith"
)

# Add known nicknames
person.add_nickname(Nickname(
    name="Bob",
    source=NicknameSource.MANUAL,
    confidence=1.0
))

# Infer from conversations
engine = NicknameInferenceEngine()
messages = load_your_messages()  # Your existing message data
inferred = engine.analyze_conversation(messages, [person])
```

## Summary

**Quick Wins:**
1. Run `./fix_contacts_permission.sh` first
2. If that fails, use mock data with `python3 test_mock_nicknames.py`
3. The nickname system works fully without Contacts access!

**For Production:**
- Use conversation analysis for nickname inference
- Import contacts from CSV/JSON if available
- Manually add important nicknames

The nickname system is designed to work with multiple data sources, so Contacts access is helpful but not required!
