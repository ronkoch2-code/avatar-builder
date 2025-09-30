# Nickname Management System for Avatar-Engine

## Quick Start

### Test Without Contacts Access

If you're having trouble with Contacts permissions on macOS 26, start with the mock data test:

```bash
python3 test_mock_nicknames.py
```

This will show you how the nickname system works without requiring any permissions.

### Request Contacts Permission

For macOS 26, you need to trigger the permission request:

```bash
python3 request_contacts_permission.py
```

This will:
1. Check your current permission status
2. Trigger the system permission dialog if needed
3. Guide you through any troubleshooting steps

### Extract Nicknames from Contacts

Once you have permission:

```bash
# Extract and display contacts with nicknames
python3 main.py extract-contacts

# Save to JSON file
python3 main.py extract-contacts -o contacts_nicknames.json

# Save to CSV
python3 main.py extract-contacts -o contacts_nicknames.csv -f csv
```

### Import to Neo4j

If you have Neo4j running:

```bash
# Import all contacts and nicknames to graph
python3 main.py import-to-graph

# Clear existing data first
python3 main.py import-to-graph --clear
```

### Analyze Conversations

To infer nicknames from conversations:

```bash
# Use the sample messages
python3 main.py analyze-conversation data/sample_messages.json

# Use your own messages (must be JSON format)
python3 main.py analyze-conversation your_messages.json
```

## File Locations

All nickname-related code is in the `src/` directory:

- **Models**: `src/models/graph_models.py`
  - Person entity
  - Nickname entity  
  - NicknameSource and NicknameType enums
  - Relationship models

- **Extractors**: `src/extractors/`
  - `address_book_extractor.py` - macOS Contacts integration
  - `nickname_inference.py` - Conversation analysis

- **Database**: `src/database/graph_builder.py`
  - Neo4j operations
  - Graph queries
  - Export functionality

- **CLI**: `main.py` (in root directory)
  - Command-line interface
  - All user commands

## Nickname Types Supported

The system recognizes 8 types of nicknames:

1. **Given** - Explicitly provided nicknames
2. **Diminutive** - Shortened versions (Bob from Robert)
3. **Formal** - Full versions (Robert from Bob)
4. **Initials** - Letter-based (RS from Robert Smith)
5. **Cultural** - Cultural variations (Sasha from Alexander)
6. **Professional** - Work names (Professor Chen)
7. **Family** - Family nicknames
8. **Social** - Social media handles

## Nickname Sources

Nicknames are tracked by where they come from:

- **addressbook** - Extracted from Contacts app
- **conversation** - Found in message analysis
- **self_reference** - Person referring to themselves
- **manual** - Manually added
- **inferred** - Automatically detected patterns

## Confidence Scoring

Each nickname has a confidence score (0.0 to 1.0):

- **1.0** - Explicit from Address Book
- **0.95** - Self-references in messages
- **0.8-0.9** - Strong patterns
- **0.5-0.7** - Moderate confidence
- **< 0.5** - Low confidence inferences

## Troubleshooting

### macOS Contacts Permission Issues

If you can't get Contacts permission on macOS 26:

1. **Use the permission script**:
   ```bash
   python3 request_contacts_permission.py
   ```

2. **Check Full Disk Access**:
   - System Settings > Privacy & Security > Full Disk Access
   - Add Terminal (or your IDE)

3. **Use mock data for testing**:
   ```bash
   python3 test_mock_nicknames.py
   ```

### Missing Dependencies

Install macOS-specific packages:
```bash
pip3 install -r requirements-macos.txt
```

Or individually:
```bash
pip3 install pyobjc-framework-Contacts pyobjc-framework-AddressBook
```

### Neo4j Connection Issues

1. **Check if Neo4j is running**:
   ```bash
   neo4j status
   ```

2. **Set password in .env file**:
   ```bash
   echo "NEO4J_PASSWORD=your_password" >> .env
   ```

3. **Test without Neo4j**:
   ```bash
   # Just extract to JSON
   python3 main.py extract-contacts -o output.json
   ```

## Integration with Main Pipeline

To integrate nickname extraction into your main pipeline, add this to your extraction script:

```python
from src.extractors.address_book_extractor import AddressBookExtractor
from src.extractors.nickname_inference import NicknameInferenceEngine
from src.database.graph_builder import GraphBuilder

# Extract from Address Book
extractor = AddressBookExtractor()
persons = extractor.extract_all_contacts()

# Analyze conversations for nicknames
inference = NicknameInferenceEngine()
messages = load_your_messages()  # Your message loading logic
inferred_nicknames = inference.analyze_conversation(messages, persons)

# Store in Neo4j
graph = GraphBuilder()
for person in persons:
    graph.create_person(person)
```

## Next Steps

1. **Test with mock data** first to verify the system works
2. **Get Contacts permission** using the request script
3. **Extract your real contacts** with nicknames
4. **Analyze your conversations** to find more nicknames
5. **Import to Neo4j** for graph analysis
6. **Integrate into main pipeline** once tested

## Support Files

- `request_contacts_permission.py` - Trigger permission dialog
- `test_mock_nicknames.py` - Test without Contacts
- `data/sample_messages.json` - Sample conversation data
- `requirements-macos.txt` - macOS-specific packages
