# Avatar Intelligence System - Quick Start Guide

🚀 **Get up and running in 5 minutes!**

## Step 1: Verify Your Setup (NEW! 🔧)

```bash
cd /Volumes/FS001/pythonscripts/Avatar-Engine/

# Complete setup verification (recommended)
python3 verify_setup.py

# Or test just the basics
python3 run_tests.py
```

**Expected output:** Setup verification should show all checks passing ✅

## Step 2: Test the Package

```bash
cd /Volumes/FS001/pythonscripts/Avatar-Engine/

# Run the simple test runner
python run_tests.py
```

**Expected output:** All tests should pass ✅

## Step 3: Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install with all development tools
pip install -e ".[dev,test]"
```

## Step 4: Deploy to Neo4j

**Make sure Neo4j is running first!**

```bash
# Using make (recommended) - FIXED for python3!
make deploy-system NEO4J_PASSWORD=your_neo4j_password

# Or directly with Python
python3 src/avatar_system_deployment.py --password your_password --command deploy

# If make doesn't work, override Python:
make deploy-system NEO4J_PASSWORD=your_password PYTHON=python3
```

## Step 5: Check System Status

```bash
# Check if deployment worked  
make check-system NEO4J_PASSWORD=your_neo4j_password

# Or directly
python3 src/avatar_system_deployment.py --password your_password --command status
```

## Step 6: Process Your Data

```bash
# Run the basic usage example
python3 examples/basic_usage.py

# Follow the prompts to enter your Neo4j password
```

## Step 7: Use the System

### In Your Python Code:

```python
from src.avatar_intelligence_pipeline import AvatarSystemManager
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_password"))
avatar_system = AvatarSystemManager(driver)

# Process all people with 50+ messages
stats = avatar_system.initialize_all_people(min_messages=50)
print(f"Created {stats['created']} avatar profiles")

# Generate a personalized AI prompt
prompt = avatar_system.generate_response(
    person_identifier="John Doe",  # Use actual name from your data
    conversation_type="1:1",
    partners=["Jane Smith"],  # Who they're talking with
    topic="travel"  # Optional topic
)

print("AI Avatar Prompt:")
print(prompt)

driver.close()
```

### Command Line Usage:

```bash
# Process all people with sufficient messages
python src/avatar_intelligence_pipeline.py --password your_password --command init-all --min-messages 50

# Process a specific person
python src/avatar_intelligence_pipeline.py --password your_password --command init-person --person "John Doe"

# Generate response for someone
python src/avatar_intelligence_pipeline.py --password your_password --command generate --person "John Doe" --partners "Jane Smith" --topic "work"

# Get system statistics
python src/avatar_intelligence_pipeline.py --password your_password --command stats
```

## Troubleshooting

### Python Command Issues ("python: No such file or directory")

This is common on macOS. Try these solutions:

```bash
# Option 1: Use python3 directly
python3 run_tests.py

# Option 2: Override the Python command in make
make test PYTHON=python3

# Option 3: Check what Python you have
sh test_python.sh

# Option 4: Create a symlink (if you have admin access)
sudo ln -sf $(which python3) /usr/local/bin/python
```

### Deployment Issues ("System deployment failed!")

This usually happens when there's an existing partial deployment. Try these solutions:

```bash
# Option 1: Test deployment directly
python3 test_deployment_direct.py

# Option 2: Force redeploy via command line
python3 src/avatar_system_deployment.py --password your_password --command deploy --force

# Option 3: Clean up existing deployment and start fresh
python3 cleanup_system.py

# Option 4: Check what's in your database
python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
with driver.session() as session:
    sys_result = session.run('MATCH (sys:AvatarSystem) RETURN count(sys) as systems').single()
    profile_result = session.run('MATCH (cp:CommunicationProfile) RETURN count(cp) as profiles').single()
    print(f'System metadata: {sys_result["systems"]}, Profiles: {profile_result["profiles"]}')
driver.close()
"
```

### Tests Failing?
```bash
# Check if all dependencies are installed
python3 -c "import neo4j, pandas, numpy, pytest; print('All dependencies OK!')"

# Install missing packages
pip install neo4j pandas numpy pytest
```

### Neo4j Connection Issues?
```bash
# Check if Neo4j is running
# Visit http://localhost:7474 in your browser

# Check connection
python -c "from neo4j import GraphDatabase; print('Neo4j driver imported OK')"
```

### No Conversation Data?
```bash
# Check if you have Person and Message nodes
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password'))
with driver.session() as session:
    people = session.run('MATCH (p:Person) RETURN count(p)').single()[0]
    messages = session.run('MATCH (m:Message) RETURN count(m)').single()[0]
    print(f'Found {people} people, {messages} messages')
driver.close()
"
```

## What the System Does

1. **Analyzes your conversation data** to understand how each person communicates
2. **Detects nicknames** people use for each other
3. **Infers relationships** (romantic, family, friend, professional)
4. **Analyzes communication styles** (formal vs casual, emotional expressions, topics)
5. **Generates personalized AI prompts** that capture someone's communication style

## Next Steps

- **Integrate with ChatGPT/Claude**: Use the generated prompts with AI services
- **Build Applications**: Create chatbots that mimic specific people's communication styles  
- **Analyze Relationships**: Explore the relationship data to understand social networks
- **Customize Analysis**: Modify the linguistic analysis to detect patterns specific to your use case

## Quick Development Commands

```bash
# Run all tests
make test

# Format code
make format

# Run linting
make lint

# Build package
make build

# See all commands
make help
```

---

🎉 **You're all set!** The Avatar Intelligence System is ready to create personalized AI avatars from your conversation data.
