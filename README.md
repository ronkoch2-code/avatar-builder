# Avatar-Engine

**An intelligent system for analyzing conversation data and generating personalized AI avatars based on communication patterns.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security Audit](https://img.shields.io/badge/security-audited-green.svg)](SECURITY_ENHANCEMENTS.md)
[![Neo4j 5.0+](https://img.shields.io/badge/neo4j-5.0+-green.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

Avatar-Engine is a sophisticated conversation analysis system that:
- **Loads message data** from various sources (SQLite, JSON) into Neo4j
- **Analyzes communication patterns** using advanced NLP techniques
- **Generates personality profiles** with optional LLM enhancement
- **Creates AI avatars** that can respond in the authentic voice of analyzed individuals
- **Protects privacy** with comprehensive security features (NEW in v2.0)

### 🔒 Security Features (v2.1 - Enhanced)
- **Encrypted sensitive data** - PII protection with AES-256 encryption
- **PBKDF2 key derivation** - Enhanced key security with 100,000 iterations
- **No default credentials** - Mandatory explicit configuration for all secrets
- **Anonymized phone numbers** - Privacy-preserving data storage
- **Parameterized queries** - SQL/Cypher injection prevention
- **Secure API key management** - Environment-based configuration with validation
- **Comprehensive input validation** - Protection against prompt injection and path traversal
- **Rate limiting** - Configurable abuse prevention for APIs and database
- **Secure audit logging** - Automatic PII/secret redaction in all logs
- **Enhanced pattern detection** - AWS keys, JWT tokens, and configurable patterns

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

### Small Language Models (SLM) - Mac Metal Optimized
- **Personalized Training**: Train custom language models from conversation data
- **Metal Acceleration**: Leverages Apple Silicon for efficient training and inference
- **MLX Framework**: Optimized for M1/M2/M3 processors
- **Local Inference**: Run avatar models locally without cloud dependencies
- **Interactive Chat**: Real-time conversation with trained avatars
- **Streaming Generation**: Low-latency response streaming
- **Batch Processing**: Efficient multi-prompt processing

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

# For Mac Metal SLM support (Apple Silicon only):
pip install mlx mlx-lm
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

### 1. Load Your Message Data (Securely)

```bash
# From SQLite database with anonymization
python3 src/message_data_loader.py /path/to/messages.db --password neo4j_password --anonymize

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

### 4. Train Small Language Models (Mac Only)

```bash
# Full pipeline: Extract, Train, and Chat
python3 examples/slm/slm_pipeline_example.py full --person "John Doe"

# Or run individual steps:
# Extract conversation data
python3 examples/slm/slm_pipeline_example.py extract --person "John Doe"

# Train personalized model
python3 examples/slm/slm_pipeline_example.py train \
  --data-path data/extracted/john_doe.jsonl

# Start interactive chat
python3 examples/slm/slm_pipeline_example.py chat \
  --model-path models/john_avatar
```

For detailed SLM documentation, see [docs/slm/slm_documentation.md](docs/slm/slm_documentation.md)

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

## 🖄 Version History

### v2.0.0 (2025-01-30) - Security Enhancement Release
- 🔒 **Major Security Overhaul**
  - Implemented comprehensive security features
  - Added encryption for sensitive data
  - Parameterized all database queries
  - Secure API key management
  - Phone number anonymization
  - Rate limiting and input validation
- 🔧 **Infrastructure Improvements**
  - Created secure database wrapper
  - Added security utilities module
  - Enhanced error handling
- 🧪 **Testing**
  - Comprehensive security test suite
  - 100% coverage for security features

### v1.x - Previous Versions
See CHANGELOG.md for earlier version history.

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
