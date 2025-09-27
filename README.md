# Avatar-Engine

**An intelligent system for analyzing conversation data and generating personalized AI avatars based on communication patterns.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security Audit](https://img.shields.io/badge/security-audited-green.svg)](SECURITY_ENHANCEMENTS.md)
[![Neo4j 5.0+](https://img.shields.io/badge/neo4j-5.0+-green.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

Avatar-Engine is a sophisticated conversation analysis system that transforms your iMessage conversations into personalized AI avatars through a five-stage pipeline:

1. **📱 Extract** - Pulls messages from iMessage database with contact enrichment
2. **💾 Load** - Imports conversations into Neo4j graph database
3. **🔍 Analyze** - Detects communication patterns, nicknames, and relationships
4. **🧠 Enhance** - (Optional) Adds deep personality insights via LLM
5. **🤖 Generate** - Creates contextual responses in authentic voice

### End-to-End Process Flow

```
iMessage Database → JSON Export → Neo4j Graph → Avatar Profiles → AI Responses
     (Extract)        (Load)       (Analyze)      (Enhance)       (Generate)
```

### 📝 How It Works

1. **Extraction**: The system reads your iMessage database (`~/Library/Messages/chat.db`), enriches messages with contact names, anonymizes phone numbers for privacy, and exports to JSON.

2. **Loading**: The JSON data is imported into Neo4j, creating a graph of People, Messages, and their relationships (who sent what to whom).

3. **Analysis**: The avatar intelligence pipeline analyzes the graph to detect communication patterns, nicknames, signature phrases, and relationship types.

4. **Enhancement** (Optional): With an Anthropic API key, Claude AI performs deep personality analysis, adding psychological insights and communication style profiling.

5. **Generation**: The system can generate contextual responses that match each person's authentic communication style, or train local SLM models for offline use.

## 📢 Latest Updates (2025-09-14)

- ✅ **Fixed**: ImportError in extraction pipeline (`AvatarIntelligencePipeline` → `AvatarSystemManager`)
- ✅ **Fixed**: NAS/network volume SQLite access issues with automatic local storage fallback
- ✅ **Added**: Comprehensive reliability module with error handling, retry logic, and circuit breakers
- ✅ **Enhanced**: Security features including removed default credentials and strong input validation
- ✅ **Consolidated**: Backlog management with prioritized feature tracking

### 🔒 Security Features (v2.1 - Enhanced)
- **Encrypted sensitive data** - PII protection with AES-256 encryption
- **PBKDF2 key derivation** - Enhanced key security with 100,000 iterations
- **No default credentials** - Mandatory explicit configuration for all secrets

### 🚀 MLX Framework Support (v2.3 - Resolved)
- **MLX Issue Fixed** - Resolved conflicts with instructlab package
- **Apple Silicon Optimization** - Full Metal acceleration support for SLM training
- **Fallback Options** - CPU-based training available when MLX unavailable
- **Platform Detection** - Robust handling of Rosetta 2 emulation scenarios
- **Anonymized phone numbers** - Privacy-preserving data storage
- **Parameterized queries** - SQL/Cypher injection prevention
- **Secure API key management** - Environment-based configuration with validation
- **Comprehensive input validation** - Protection against prompt injection and path traversal
- **Rate limiting** - Configurable abuse prevention for APIs and database
- **Secure audit logging** - Automatic PII/secret redaction in all logs
- **Enhanced pattern detection** - AWS keys, JWT tokens, and configurable patterns

### 🌐 Network Volume Support (v2.2 - NEW)
- **Automatic NAS/Network Detection** - Transparently handles SQLite on network volumes
- **Local Storage Manager** - Automatic local caching for network-mounted databases
- **Platform Support** - Works on macOS and Linux network mounts (SMB, AFP, NFS)
- **Zero Configuration** - No code changes needed, works automatically
- **Smart Sync** - Results automatically synced back to network storage
- **Error Recovery** - Graceful handling of network failures
- See [LocalStorageManager Documentation](docs/LOCAL_STORAGE_MANAGER.md) for details

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

### Pipeline Stages

#### Stage 1: Message Extraction
- **iMessage Integration**: Direct extraction from macOS chat.db
- **Contact Enrichment**: Automatic name resolution from AddressBook
- **Privacy Protection**: Phone number anonymization via SHA-256
- **Batch Processing**: Handle millions of messages efficiently
- **Checkpoint Recovery**: Resume interrupted extractions

#### Stage 2: Data Loading
- **Graph Import**: Load conversations into Neo4j
- **Relationship Mapping**: Create SENT/RECEIVED connections
- **Group Detection**: Identify and model group conversations
- **Text Cleaning**: Remove binary artifacts and metadata
- **Secure Queries**: Parameterized Cypher to prevent injection

#### Stage 3: Avatar Generation
- **Pattern Detection**: Identify communication signatures
- **Nickname Discovery**: Find how people address each other
- **Relationship Inference**: Determine connection types
- **Topic Analysis**: Discover conversation preferences
- **Temporal Patterns**: Analyze time-based behaviors

#### Stage 4: LLM Enhancement (Optional)
- **Deep Analysis**: Psychological profiling via Claude AI
- **Personality Insights**: MBTI-style assessments
- **Communication Style**: Formal/informal analysis
- **Emotional Patterns**: Sentiment and expression mapping

#### Stage 5: Response Generation
- **Contextual Responses**: Topic and partner-aware generation
- **Voice Authenticity**: Maintain individual communication style
- **SLM Training**: Create local models for offline use

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
- **Interactive Chat Interface**: NEW! Command-line interface for chatting with trained models
  - `python3 src/slm/inference/chat.py` - Start interactive chat
  - Model selection menu with auto-detection
  - Conversation history and save/load support
  - Works with both MLX and fallback models
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

### Option A: Full Pipeline (Recommended)

Run the complete extraction → loading → profiling pipeline:

```bash
# Extract, load, and generate profiles automatically
python3 src/pipelines/extraction_pipeline.py --limit 5000

# With LLM enhancement (requires Anthropic API key)
python3 src/pipelines/extraction_pipeline.py --limit 5000 --enable-llm
```

### Option B: Step-by-Step Process

#### Step 1: Extract Messages from iMessage

```bash
# Extract recent messages (recommended for testing)
python3 src/imessage_extractor.py --limit 5000

# Extract all messages
python3 src/imessage_extractor.py
```

This creates: `data/extracted/imessage_export_YYYYMMDD_HHMMSS.json`

#### Step 2: Load into Neo4j

```bash
# Load the extracted JSON
python3 src/message_data_loader.py data/extracted/imessage_export_*.json \
  --password your_neo4j_password
```

#### Step 3: Generate Avatar Profiles

```bash
# Create profiles for all participants with 50+ messages
python3 src/avatar_intelligence_pipeline.py \
  --command init-all \
  --min-messages 50 \
  --password neo4j_password
```

#### Step 4: (Optional) Enhance with LLM

```bash
# Add deep personality analysis via Claude
python3 src/enhanced_avatar_pipeline.py \
  --person "John Doe" \
  --password neo4j_password
```

#### Step 5: Generate Avatar Responses

```bash
# Generate contextual response
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person "John Doe" \
  --partners "Jane Smith" \
  --topic "weekend plans" \
  --password neo4j_password
```

### Option C: Train Small Language Models (Mac Only)

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
│   ├── imessage_extractor.py            # iMessage database extraction
│   ├── message_data_loader.py           # JSON to Neo4j import
│   ├── avatar_intelligence_pipeline.py   # Avatar profile generation
│   ├── enhanced_avatar_pipeline.py       # LLM-enhanced analysis
│   ├── llm_integrator.py                 # Claude AI integration
│   ├── avatar_system_deployment.py       # Schema deployment
│   ├── config_manager.py                 # Configuration management
│   ├── security_utils.py                 # Security utilities
│   ├── secure_database.py                # Secure Neo4j wrapper
│   └── pipelines/
│       └── extraction_pipeline.py        # Orchestrates full pipeline
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
from src.imessage_extractor import IMessageExtractor
from src.message_data_loader import MessageDataLoader
from src.avatar_intelligence_pipeline import AvatarSystemManager
from neo4j import GraphDatabase

# Step 1: Extract from iMessage
extractor = IMessageExtractor()
json_file = extractor.run_extraction_pipeline(limit=5000)

# Step 2: Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# Step 3: Load extracted messages
loader = MessageDataLoader(neo4j_driver=driver)
stats = loader.load_from_json(json_file)
print(f"Loaded {stats['messages_created']} messages")

# Step 4: Create avatar profiles
avatar_system = AvatarSystemManager(driver)
avatar_system.initialize_all_people(min_messages=50)

# Step 5: Generate avatar response
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
# Full extraction pipeline (recommended)
python3 src/pipelines/extraction_pipeline.py --help

# Individual components:
# Extract from iMessage
python3 src/imessage_extractor.py --help

# Load into Neo4j
python3 src/message_data_loader.py --help

# Generate avatar profiles
python3 src/avatar_intelligence_pipeline.py --help

# LLM enhancement (requires Anthropic API key)
python3 src/enhanced_avatar_pipeline.py --help

# System deployment and management
python3 src/avatar_system_deployment.py --help
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

- **[iMessage Extraction Guide](docs/IMESSAGE_EXTRACTION_GUIDE.md)** - Step-by-step extraction instructions
- **[Message Data Loading Guide](docs/message_data_loading.md)** - How to import your data
- **[Neo4j Data Model](docs/neo4j_data_model.md)** - Complete schema documentation
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Quick Start Guide](QUICKSTART.md)** - Get running quickly
- **[Security Enhancements](SECURITY_ENHANCEMENTS.md)** - Security features documentation
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

### v2.3.0 (2025-09-27) - MLX Framework Resolution
- 🍏 **MLX Training Support**
  - Resolved instructlab package conflicts
  - Full Apple Silicon Metal acceleration
  - Robust platform detection for Rosetta 2
  - Dynamic library path configuration
  - CPU fallback options available
- 🔧 **Developer Experience**
  - Comprehensive diagnostic tools
  - Multiple fix strategies documented
  - Wrapper scripts for environment setup
- 📚 **Documentation**
  - MLX troubleshooting guide
  - Platform-specific setup instructions
  - Optional dependency management standards

### v2.2.0 (2025-09-14) - Network Volume Support
- 🌐 **Network Storage Compatibility**
  - Automatic detection of NAS/network volumes
  - Transparent local storage for SQLite operations
  - Fixes "unable to open database file" on network mounts
  - Platform-specific detection (macOS, Linux)
  - Smart sync back to network storage
- 🔧 **LocalStorageManager Implementation**
  - Zero-configuration operation
  - Robust error handling and recovery
  - Storage size limit enforcement
  - Automatic cleanup mechanisms
- 📝 **Documentation**
  - Comprehensive LocalStorageManager guide
  - Troubleshooting documentation
  - Integration examples

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
