# Avatar Intelligence System - Complete Setup Guide

## 📁 Directory Structure

Your Avatar Engine directory is set up as follows:

```
/Volumes/FS001/pythonscripts/Avatar-Engine/
├── README.md                           # This setup guide
├── requirements.txt                    # Python dependencies  
├── setup.sh                          # Automated setup script
├── src/                               # Main source code
│   ├── __init__.py
│   ├── avatar_intelligence_pipeline.py    # Complete analysis pipeline
│   └── avatar_system_deployment.py        # Deployment and management
├── sql/                               # Database files
│   └── avatar_intelligence_schema.cypher  # Neo4j schema
├── docs/                              # Documentation
│   ├── relationship_inference_guide.md
│   ├── nickname_detection_guide.md
│   └── usage_examples.md
├── examples/                          # Usage examples
│   └── basic_usage.py
└── tests/                            # Test scripts
    └── test_deployment.py
```

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd /Volumes/FS001/pythonscripts/Avatar-Engine/
pip install -r requirements.txt
```

### Step 2: Deploy the System

```bash
# Deploy schema and system
python src/avatar_system_deployment.py \
    --password YOUR_NEO4J_PASSWORD \
    --command deploy

# Check deployment status
python src/avatar_system_deployment.py \
    --password YOUR_NEO4J_PASSWORD \
    --command status
```

### Step 3: Test the Installation

```bash
# Run basic example
python examples/basic_usage.py
```

## 📋 File Descriptions

### Core Files

- **`src/avatar_intelligence_pipeline.py`** - Complete analysis system with:
  - Nickname detection engine
  - Relationship inference engine  
  - Linguistic analysis
  - Avatar generation pipeline
  - Runtime system for fast queries

- **`src/avatar_system_deployment.py`** - System management:
  - Schema deployment
  - System health monitoring
  - Maintenance operations

- **`sql/avatar_intelligence_schema.cypher`** - Database schema:
  - Node constraints and indexes
  - System metadata setup
  - Sample queries and verification

## ⚙️ Configuration

### Neo4j Connection

Edit connection settings in your scripts or use environment variables:

```python
# Direct configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j" 
NEO4J_PASSWORD = "your_password"
```

## 🎯 Basic Usage Example

```python
from src.avatar_intelligence_pipeline import AvatarSystemManager
from neo4j import GraphDatabase

# Initialize system
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
avatar_system = AvatarSystemManager(driver)

# Process all people with sufficient conversation data
stats = avatar_system.initialize_all_people(min_messages=50)
print(f"Processed {stats['created']} people")

# Generate avatar response
prompt = avatar_system.generate_response(
    person_identifier="clAIre Russell",
    conversation_type="1:1",
    partners=["Ron Koch"],
    topic="health"
)

print("Avatar prompt:", prompt)
driver.close()
```

## 🔧 System Requirements

### Prerequisites
- **Neo4j 5.0+** with existing conversation data loaded
- **Python 3.7+** 
- **Memory**: 4GB+ recommended for large conversation datasets

### Existing Data Schema
Your Neo4j database should have:
- `Person` nodes with `id`, `name`, `phone` properties
- `Message` nodes with `body`, `date`, `isFromMe` properties  
- `GroupChat` nodes for conversation context
- Relationships: `Person-[:SENT]->Message`, `Message-[:SENT_TO]->GroupChat`, `Person-[:MEMBER_OF]->GroupChat`

## 🧪 Testing Your Installation

### 1. Test Database Connection
```python
from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        result = session.run("MATCH (p:Person) RETURN count(p) as people").single()
        print(f"✓ Connected! Found {result['people']} people in database")
    driver.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### 2. Verify Schema Deployment
```bash
python src/avatar_system_deployment.py --password PASSWORD --command status
```

### 3. Process a Single Person
```python
# Test with one person
stats = avatar_system.initialize_person("clAIre Russell", identifier_type="name")
print(f"✓ Created profile: {stats}")
```

## 📈 Next Steps After Installation

1. **Process Your Data**: Start with `initialize_all_people(min_messages=50)`
2. **Explore Relationships**: Use `get_person_relationships()` to see detected relationships
3. **Test Avatar Generation**: Generate prompts for different conversation contexts
4. **Analyze Nicknames**: Check nickname detection with `get_person_nicknames()`
5. **Integrate with AI**: Feed generated prompts to ChatGPT, Claude, or other LLMs

---

🎉 **You're ready to build personalized AI avatars from your conversation data!**
