# Avatar-Engine Quick Start Guide

🚀 **Get up and running in 5 minutes!**

## Prerequisites

- **Python 3.7+** installed
- **Neo4j 5.0+** running (Community or Enterprise)
- **pip** package manager

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/avatar-engine.git
cd avatar-engine

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Neo4j

```bash
# Interactive setup (recommended)
python3 utilities/setup_neo4j.py

# This will:
# - Prompt for your Neo4j credentials
# - Test the connection
# - Create a .env file with your settings
```

**Alternative:** Create `.env` manually:
```bash
echo "NEO4J_URI=bolt://localhost:7687" >> .env
echo "NEO4J_USERNAME=neo4j" >> .env
echo "NEO4J_PASSWORD=your_password" >> .env
```

## Step 3: Deploy Database Schema

```bash
# Deploy the Avatar-Engine schema to Neo4j
python3 src/avatar_system_deployment.py deploy

# Verify deployment
python3 src/avatar_system_deployment.py status
```

## Step 4: Load Your Data

### Option A: From SQLite Database
```bash
python3 src/message_data_loader.py /path/to/messages.db --password your_neo4j_password
```

### Option B: From JSON File
```bash
python3 src/message_data_loader.py /path/to/messages.json --password your_neo4j_password
```

### Option C: Test with Sample Data
```bash
# Run the basic usage example
python3 examples/basic_usage.py
```

## Step 5: Generate Avatar Profiles

```bash
# Initialize profiles for all people with 50+ messages
python3 src/avatar_intelligence_pipeline.py \
  --command init-all \
  --min-messages 50 \
  --password your_neo4j_password

# Check statistics
python3 src/avatar_intelligence_pipeline.py \
  --command stats \
  --password your_neo4j_password
```

## Step 6: Use the Avatar System

### Generate a Personalized Avatar Response

```python
from src.avatar_intelligence_pipeline import AvatarSystemManager
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_password"))
avatar_system = AvatarSystemManager(driver)

# Generate avatar response
prompt = avatar_system.generate_response(
    person_identifier="John Doe",
    conversation_type="1:1",
    partners=["Jane Smith"],
    topic="weekend plans"
)

print("AI Avatar Prompt:")
print(prompt)
driver.close()
```

### Command Line Usage

```bash
# Process a specific person
python3 src/avatar_intelligence_pipeline.py \
  --command init-person \
  --person "John Doe" \
  --password your_password

# Generate response prompt
python3 src/avatar_intelligence_pipeline.py \
  --command generate \
  --person "John Doe" \
  --partners "Jane Smith" \
  --topic "travel" \
  --password your_password
```

## 🔍 Verify Your Setup

### Check Neo4j Connection
```bash
python3 utilities/debug_neo4j.py
```

### Check Data Loading
```cypher
# In Neo4j Browser (http://localhost:7474)
# Count loaded data
MATCH (p:Person) RETURN count(p) as people;
MATCH (m:Message) RETURN count(m) as messages;
MATCH (g:GroupChat) RETURN count(g) as groups;
```

### Check Avatar Profiles
```cypher
# See who has profiles
MATCH (p:Person)-[:HAS_PROFILE]->(cp:CommunicationProfile)
RETURN p.name, cp.messageCount, cp.responseStyle
ORDER BY cp.messageCount DESC;
```

## 📊 Using the Makefile

The project includes a Makefile for common tasks:

```bash
# Deploy system
make deploy-system NEO4J_PASSWORD=your_password

# Check system status
make check-system NEO4J_PASSWORD=your_password

# Run tests
make test

# Clean build artifacts
make clean

# See all available commands
make help
```

**Note:** On macOS, use `PYTHON=python3` if you get "python not found":
```bash
make test PYTHON=python3
```

## 🛠️ Troubleshooting

### Neo4j Connection Issues

```bash
# 1. Verify Neo4j is running
neo4j status

# 2. Test connection
python3 -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
    with driver.session() as session:
        session.run('RETURN 1')
    print('✅ Connection successful!')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### No Data After Loading?

```bash
# Check if data was loaded
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
with driver.session() as session:
    people = session.run('MATCH (p:Person) RETURN count(p) as count').single()['count']
    messages = session.run('MATCH (m:Message) RETURN count(m) as count').single()['count']
    print(f'People: {people}, Messages: {messages}')
    if people == 0:
        print('❌ No data loaded - run message_data_loader.py first')
    else:
        print('✅ Data loaded successfully')
driver.close()
"
```

### Missing Dependencies?

```bash
# Check all required packages
python3 -c "
import sys
required = ['neo4j', 'pandas', 'numpy', 'regex', 'python-dateutil']
missing = []
for pkg in required:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'❌ Missing packages: {missing}')
    print(f'   Install with: pip install {" ".join(missing)}')
else:
    print('✅ All dependencies installed')
"
```

## 🎯 What You Can Do Now

1. **Analyze Communication Patterns**
   - See how different people communicate
   - Identify signature phrases and expressions
   - Understand relationship dynamics

2. **Generate AI Avatars**
   - Create prompts that capture someone's communication style
   - Use with ChatGPT, Claude, or other LLMs
   - Build chatbots that sound like specific people

3. **Explore the Graph**
   - Use Neo4j Browser to visualize relationships
   - Query patterns and trends
   - Export data for further analysis

## 📚 Next Steps

- **Read the Documentation**
  - [Message Data Loading Guide](docs/message_data_loading.md)
  - [Neo4j Data Model](docs/neo4j_data_model.md)
  
- **Try the Examples**
  - `examples/basic_usage.py` - Simple demonstration
  - `examples/enhanced_demo.py` - Advanced features with LLM

- **Enable LLM Enhancement** (Optional)
  ```bash
  # Add Anthropic API key to .env
  echo "ANTHROPIC_API_KEY=your_api_key" >> .env
  
  # Use enhanced pipeline
  python3 src/enhanced_avatar_pipeline.py
  ```

## 🆘 Getting Help

- **Check the docs:** `docs/` directory
- **Run examples:** `examples/` directory  
- **Debug utilities:** `utilities/debug_neo4j.py`
- **Open an issue:** GitHub repository

---

🎉 **You're ready!** The Avatar-Engine is set up and ready to analyze conversations and generate AI avatars.
