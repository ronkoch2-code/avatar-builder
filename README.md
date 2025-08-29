# Avatar-Engine

**An intelligent system for analyzing conversation data and generating personalized AI avatars based on communication patterns.**

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j 5.0+](https://img.shields.io/badge/neo4j-5.0+-green.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

Avatar-Engine is a sophisticated conversation analysis system that:
- **Loads message data** from various sources (SQLite, JSON) into Neo4j
- **Analyzes communication patterns** using advanced NLP techniques
- **Generates personality profiles** with optional LLM enhancement
- **Creates AI avatars** that can respond in the authentic voice of analyzed individuals

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Usage](#usage)
- [Data Model](#data-model)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Capabilities
- **Message Data Loading**: Import conversations from SQLite databases or JSON files
- **Intelligent Text Cleaning**: Remove binary artifacts and system metadata
- **Graph-Based Storage**: Leverage Neo4j for relationship-aware data storage
- **Pattern Detection**: Identify nicknames, signature phrases, and communication styles
- **Relationship Analysis**: Infer relationship types (family, friend, romantic, professional)
- **Personality Profiling**: Generate comprehensive communication profiles
- **LLM Integration**: Optional Claude AI enhancement for deeper insights

### Analysis Engines
- **Nickname Detector**: Identifies how people address each other
- **Relationship Inferrer**: Determines relationship types from conversation patterns
- **Linguistic Analyzer**: Analyzes communication style, formality, and emotional expression
- **Topic Analyzer**: Identifies preferred conversation topics
- **Temporal Pattern Detector**: Discovers time-based communication patterns

## 🛠️ Installation

### Prerequisites

1. **Python 3.7+**
2. **Neo4j 5.0+** (Community or Enterprise Edition)
3. **API Keys** (optional):
   - Anthropic API key for Claude integration

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/avatar-engine.git
cd avatar-engine
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure Neo4j**:
```bash
# Interactive setup
python3 utilities/setup_neo4j.py

# Or manually create .env file
echo "NEO4J_URI=bolt://localhost:7687" >> .env
echo "NEO4J_USERNAME=neo4j" >> .env
echo "NEO4J_PASSWORD=your_password" >> .env
```

4. **Initialize the database schema**:
```bash
python3 src/avatar_system_deployment.py deploy
```

## 🚀 Quick Start

### 1. Load Your Message Data

```bash
# From SQLite database
python3 src/message_data_loader.py /path/to/messages.db --password neo4j_password

# From JSON file
python3 src/message_data_loader.py /path/to/messages.json --password neo4j_password
```

### 2. Generate Avatar Profiles

```bash
# Initialize profiles for all people with 50+ messages
python3 src/avatar_intelligence_pipeline.py \
  --command init-all \
  --min-messages 50 \
  --password neo4j_password

# Or initialize a specific person
python3 src/avatar_intelligence_pipeline.py \
  --command init-person \
  --person "John Doe" \
  --password neo4j_password
```

### 3. Generate Avatar Responses

```bash
# Generate an avatar prompt for a person
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person "John Doe" \
  --partners "Jane Smith" \
  --topic "weekend plans" \
  --password neo4j_password
```

## 🏗️ Architecture

```
Avatar-Engine/
│
├── src/                              # Core source code
│   ├── avatar_intelligence_pipeline.py   # Main analysis system
│   ├── avatar_system_deployment.py       # Schema deployment
│   ├── config_manager.py                 # Configuration management
│   ├── enhanced_avatar_pipeline.py       # LLM-enhanced analysis
│   ├── llm_integrator.py                 # Claude AI integration
│   └── message_data_loader.py            # Data import pipeline
│
├── utilities/                        # Database utilities
│   ├── setup_neo4j.py               # Neo4j configuration
│   ├── reset_neo4j.py               # Database reset tool
│   ├── backup_neo4j.py              # Backup utility
│   ├── validate_data.py             # Data validation
│   └── debug_neo4j.py               # Debugging tools
│
├── examples/                         # Usage examples
│   ├── basic_usage.py               # Simple examples
│   ├── enhanced_demo.py             # Advanced features
│   └── test_system.py               # System tests
│
├── docs/                            # Documentation
│   ├── message_data_loading.md     # Data loading guide
│   ├── neo4j_data_model.md        # Database schema
│   └── llm_json_parsing_fix.md    # Technical notes
│
├── sql/                             # Database schemas
│   ├── avatar_intelligence_schema.cypher
│   └── enhanced_avatar_schema.cypher
│
├── tests/                           # Test suite
│   └── test_deployment.py
│
├── requirements.txt                 # Python dependencies
├── setup.py                        # Package setup
├── pyproject.toml                  # Modern Python packaging
├── Makefile                        # Build automation
└── CHANGELOG.md                    # Version history
```

## 📊 Data Model

The system uses a sophisticated Neo4j graph model with 19 node types and 17 relationship types:

### Core Nodes
- **Person**: Conversation participants
- **Message**: Individual messages with cleaned text
- **GroupChat**: Conversation groups

### Profile Nodes
- **CommunicationProfile**: Main avatar profile
- **PersonalityProfile**: LLM-generated analysis
- **RelationshipPattern**: Dynamics with other people

### Analysis Nodes
- **SignaturePhrase**: Characteristic expressions
- **EmotionalExpression**: Emotional patterns
- **TopicPreference**: Preferred topics

See [docs/neo4j_data_model.md](docs/neo4j_data_model.md) for complete details.

## 💻 Usage

### Python API

```python
from src.avatar_intelligence_pipeline import AvatarSystemManager
from src.message_data_loader import MessageDataLoader
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Load message data
loader = MessageDataLoader(neo4j_driver=driver)
stats = loader.load_from_sqlite("/path/to/messages.db")
print(f"Loaded {stats['messages_created']} messages")

# Create avatar profiles
avatar_system = AvatarSystemManager(driver)
avatar_system.initialize_all_people(min_messages=50)

# Generate avatar response
prompt = avatar_system.generate_response(
    person_identifier="John Doe",
    conversation_type="1:1",
    partners=["Jane Smith"],
    topic="travel plans"
)
print(prompt)
```

### Command Line Interface

All major components provide CLI interfaces:

```bash
# System deployment and management
python3 src/avatar_system_deployment.py --help

# Message data loading
python3 src/message_data_loader.py --help

# Avatar intelligence pipeline
python3 src/avatar_intelligence_pipeline.py --help

# Enhanced LLM analysis (requires Anthropic API key)
python3 src/enhanced_avatar_pipeline.py --help
```

### Neo4j Queries

Query the graph directly using Cypher:

```cypher
// Find all people
MATCH (p:Person)
RETURN p.name, p.phone
ORDER BY p.name

// Get messages from a person
MATCH (p:Person {name: "John Doe"})-[:SENT]->(m:Message)
RETURN m.body, m.date
ORDER BY m.date DESC
LIMIT 100

// Analyze relationships
MATCH (p:Person)-[:HAS_PROFILE]->(cp:CommunicationProfile)
MATCH (cp)-[:HAS_RELATIONSHIP]->(rp:RelationshipPattern)
RETURN p.name, rp.partnerName, rp.relationshipType, rp.confidence
```

## 🔧 Utilities

### Database Management

```bash
# Setup Neo4j configuration
python3 utilities/setup_neo4j.py

# Reset database (removes data, keeps schema)
python3 utilities/reset_neo4j.py --dry-run  # Preview
python3 utilities/reset_neo4j.py             # Execute

# Backup database
python3 utilities/backup_neo4j.py

# Validate data integrity
python3 utilities/validate_data.py

# Debug connection issues
python3 utilities/debug_neo4j.py
```

## 📚 Documentation

- **[Message Data Loading Guide](docs/message_data_loading.md)** - How to import your data
- **[Neo4j Data Model](docs/neo4j_data_model.md)** - Complete schema documentation
- **[Quick Start Guide](QUICKSTART.md)** - Get running quickly
- **[Change Log](CHANGELOG.md)** - Version history and updates

## 🧪 Testing

Run the test suite:

```bash
# All tests
python3 run_tests.py

# Specific test
python3 tests/test_deployment.py

# Example scripts
python3 examples/test_system.py
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Neo4j](https://neo4j.com/) graph database
- LLM integration powered by [Anthropic's Claude](https://www.anthropic.com/)
- Inspired by the need for authentic AI conversation partners

## ⚠️ Privacy Notice

This system processes and stores conversation data. Please ensure you:
- Have consent to analyze conversations
- Comply with relevant privacy laws
- Secure your Neo4j database appropriately
- Use encryption for sensitive data

## 📧 Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/yourusername/avatar-engine/issues)
- Check the [documentation](docs/)
- Review the [examples](examples/)

---

**Avatar-Engine** - *Bringing authentic AI personalities to life through conversation analysis*
