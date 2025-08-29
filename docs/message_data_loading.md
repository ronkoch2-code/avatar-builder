# Message Data Loading Pipeline

## Overview

The `message_data_loader.py` module provides functionality to load message data from various sources (SQLite databases or JSON files) into Neo4j for use with the Avatar-Engine intelligence system.

## Features

- **Multiple Source Support**: Load from SQLite databases or JSON files
- **Automatic Message Cleaning**: Removes binary artifacts and cleans message text
- **Batch Processing**: Efficiently processes messages in configurable batches
- **Entity Creation**: Automatically creates Person, Message, and GroupChat nodes
- **Relationship Mapping**: Establishes SENT, SENT_TO, and MEMBER_OF relationships
- **Error Handling**: Robust error handling with detailed logging

## Installation

The loader is now integrated into the Avatar-Engine project. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

```bash
# Load from SQLite database
python3 src/message_data_loader.py /path/to/messages.db --password your_neo4j_password

# Load from JSON file
python3 src/message_data_loader.py /path/to/messages.json --password your_neo4j_password

# Load with limit (for testing)
python3 src/message_data_loader.py /path/to/messages.db --limit 1000 --password your_neo4j_password

# Custom Neo4j connection
python3 src/message_data_loader.py messages.db \
  --neo4j-uri bolt://localhost:7687 \
  --username neo4j \
  --password your_password
```

### Python API

```python
from src.message_data_loader import MessageDataLoader
from neo4j import GraphDatabase

# Initialize with existing driver
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
loader = MessageDataLoader(neo4j_driver=driver)

# Load from SQLite
stats = loader.load_from_sqlite("/path/to/messages.db", limit=10000)

# Load from JSON
stats = loader.load_from_json("/path/to/messages.json")

# Check statistics
print(f"Persons created: {stats['persons_created']}")
print(f"Messages created: {stats['messages_created']}")
print(f"Groups created: {stats['groups_created']}")
```

## Data Format

### SQLite Database Schema

The loader expects a SQLite database with a `messages` table containing:
- `rowid`: Unique message identifier
- `date`: Message timestamp
- `body` or `cleaned_body`: Message text content
- `phone_number`: Sender's phone number
- `is_from_me`: Boolean indicating if message was sent by the user
- `cache_roomname`: Group chat identifier
- `group_chat_name`: Human-readable group name
- `first_name`, `last_name`: Contact name information

### JSON Format

The loader accepts JSON files with the following structure:

```json
[
  {
    "rowid": 12345,
    "date": "2024-01-15 10:30:00",
    "body": "Hello, this is a message",
    "phone_number": "+1234567890",
    "is_from_me": 0,
    "cache_roomname": "chat123",
    "group_chat_name": "Family Chat",
    "first_name": "John",
    "last_name": "Doe"
  }
]
```

Or wrapped in an object:

```json
{
  "messages": [
    {
      "text": "Message content",
      "phone_number": "+1234567890",
      ...
    }
  ]
}
```

## Neo4j Graph Structure

The loader creates the following graph structure:

### Nodes
- **Person**: Represents conversation participants
  - Properties: `id`, `phone`, `name`
- **Message**: Individual messages
  - Properties: `id`, `body`, `date`, `isFromMe`
- **GroupChat**: Conversation groups
  - Properties: `id`, `name`

### Relationships
- `(Person)-[:SENT]->(Message)`: Person sent a message
- `(Message)-[:SENT_TO]->(GroupChat)`: Message was sent to a group
- `(Person)-[:MEMBER_OF]->(GroupChat)`: Person is a member of a group

## Integration with Avatar-Engine

After loading message data, you can use the Avatar-Engine to analyze communication patterns:

```python
from src.avatar_intelligence_pipeline import AvatarSystemManager
from src.message_data_loader import MessageDataLoader
from neo4j import GraphDatabase

# Setup driver
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Step 1: Load message data
loader = MessageDataLoader(neo4j_driver=driver)
loader.load_from_sqlite("/path/to/messages.db")

# Step 2: Initialize avatar profiles
avatar_system = AvatarSystemManager(driver)
stats = avatar_system.initialize_all_people(min_messages=50)

# Step 3: Generate avatar responses
prompt = avatar_system.generate_response(
    person_identifier="John Doe",
    conversation_type="1:1",
    partners=["Jane Smith"],
    topic="weekend plans"
)
```

## Message Cleaning

The loader includes sophisticated message cleaning to remove:
- Binary artifacts from Apple's message format
- Control characters and non-printable characters
- System metadata (NSDictionary, NSData, etc.)
- Trailing artifacts and malformed characters

This ensures only meaningful text content is stored in Neo4j.

## Performance Considerations

- **Batch Size**: Default is 1000 messages per batch. Adjust based on available memory
- **Large Datasets**: For databases with millions of messages, consider:
  - Processing in chunks using the `limit` parameter
  - Running during off-peak hours
  - Monitoring Neo4j memory usage

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify Neo4j password is correct
   - Check Neo4j is running: `neo4j status`

2. **No Messages Loaded**
   - Check if messages have content longer than 3 characters
   - Verify the source file format matches expected schema

3. **Memory Issues**
   - Reduce batch_size in the code
   - Process data in smaller chunks using `--limit`

### Debug Mode

Enable verbose logging by modifying the logging level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Related Components

- **Avatar Intelligence Pipeline**: Core analysis system (`src/avatar_intelligence_pipeline.py`)
- **Enhanced Avatar Pipeline**: LLM-powered analysis (`src/enhanced_avatar_pipeline.py`)
- **Neo4j Utilities**: Database management tools (`utilities/`)

## Contributing

When modifying the loader, ensure:
1. Message cleaning preserves meaningful content
2. Batch processing remains efficient
3. Error handling is comprehensive
4. Documentation is updated

## License

Part of the Avatar-Engine project. See LICENSE file for details.
