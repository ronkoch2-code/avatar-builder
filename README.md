# Avatar Intelligence System - LLM Enhanced 🤖

**Advanced AI-powered avatar generation from conversation data with Claude LLM integration**

Transform your conversation history into sophisticated AI avatars that truly understand personality, relationships, and communication patterns. This enhanced system uses Claude's advanced language understanding to create deeply personalized avatar profiles that capture the nuances of how people actually communicate.

## ✨ Enhanced Features

### 🧠 **Deep Personality Analysis**
- **Big Five Personality Traits** - Scientifically validated personality assessment
- **Communication Preferences** - Style patterns, formality levels, response tendencies
- **Behavioral Insights** - Conversation habits, topic interests, emotional expression patterns
- **Confidence Scoring** - Quality metrics for analysis reliability

### 💬 **Advanced Relationship Dynamics**
- **Relationship Type Detection** - Automatically identifies family, friends, colleagues, romantic partners
- **Intimacy Level Analysis** - Quantified communication depth and closeness metrics
- **Interaction Patterns** - How people communicate differently with various partners
- **Emotional Dynamics** - Conflict resolution styles, humor usage, support patterns

### 🎯 **Smart Avatar Generation**
- **Context-Aware Prompts** - Adapts to conversation type, partners, and topics
- **Personality-Driven Responses** - Maintains authentic voice and communication style
- **Relationship-Specific Adaptation** - Different communication patterns for different people
- **Topic Expertise Integration** - Leverages knowledge patterns from conversation history

### 📊 **Enterprise-Grade Management**
- **Cost Monitoring** - Daily spending limits with automatic controls
- **Batch Processing** - Efficient analysis of multiple people concurrently
- **Quality Metrics** - Confidence scoring and analysis validation
- **Export/Import** - JSON export of all profiles and insights

---

## 🚀 Quick Start

### **1. Installation**
```bash
cd /Volumes/FS001/pythonscripts/Avatar-Engine
pip install -r requirements.txt
```

### **2. Configuration**
Set up your API key and database connection:
```bash
export ANTHROPIC_API_KEY="your_claude_api_key_here"
python src/config_manager.py  # Interactive setup
```

### **3. Deploy Enhanced Schema**
```bash
python enhanced_deployment.py --deploy
```

### **4. Test Your Setup**
```bash
python examples/test_system.py  # Verify everything works
```

### **5. Run Your First Analysis**
```bash
python enhanced_deployment.py --analyze-person "Your Name"
```

### **6. Generate Avatar Prompts**
```python
from src.enhanced_avatar_pipeline import EnhancedAvatarSystemManager
from neo4j import GraphDatabase

# Initialize system
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
avatar_system = EnhancedAvatarSystemManager(
    neo4j_driver=driver,
    enable_llm_analysis=True
)

# Generate context-aware avatar prompt
prompt = await avatar_system.generate_enhanced_avatar_prompt(
    person_identifier="Claire Russell",
    conversation_type="1:1",
    partners=["Ron"],
    topic="health and wellness"
)

# Use with any LLM (Claude, ChatGPT, etc.)
print("Avatar prompt:", prompt)
```

---

## 📁 Project Structure

```
Avatar-Engine/
├── src/                                    # Core system modules
│   ├── avatar_intelligence_pipeline.py    # Original avatar system
│   ├── enhanced_avatar_pipeline.py        # LLM-enhanced system ⭐
│   ├── llm_integrator.py                  # Claude API integration ⭐
│   ├── config_manager.py                  # Configuration management ⭐
│   └── avatar_system_deployment.py        # Original deployment
├── sql/                                    # Database schemas
│   ├── avatar_intelligence_schema.cypher  # Original schema
│   └── enhanced_avatar_schema.cypher      # Enhanced schema ⭐
├── examples/                              # Usage examples
│   ├── basic_usage.py                     # Original examples
│   ├── enhanced_demo.py                   # Enhanced demo ⭐
│   └── test_system.py                     # System testing ⭐
├── enhanced_deployment.py                 # Enhanced deployment ⭐
├── requirements.txt                       # All dependencies
└── README.md                             # This file
```

⭐ = New LLM-enhanced features

---

## 🛠 System Management

### **Deploy Enhanced Schema**
```bash
python enhanced_deployment.py --deploy
```

### **Check System Status**
```bash
python enhanced_deployment.py --status
```

### **List People for Analysis**
```bash
python enhanced_deployment.py --list-people
```

### **Analyze Specific Person**
```bash
python enhanced_deployment.py --analyze-person "Claire Russell"
```

### **Batch Analyze Multiple People**
```bash
python enhanced_deployment.py --analyze-all --max-people 5
```

### **Monitor Costs**
```bash
python enhanced_deployment.py --costs
```

### **Export All Profiles**
```bash
python enhanced_deployment.py --export
```

---

## 💰 Cost Management

The system includes comprehensive cost controls:

- **Daily Spending Limits** - Automatic cutoff when approaching limits
- **Real-time Cost Tracking** - Monitor expenses across all analyses
- **Per-person Cost Estimation** - Know costs before processing
- **Budget Alerts** - Warnings when approaching spending thresholds

**Typical Costs:**
- Personality Analysis: $1-3 per person
- Relationship Analysis: $2-5 per person  
- Complete Enhanced Profile: $3-8 per person

```bash
# Set your budget
python -c "from src.config_manager import ConfigManager; ConfigManager().update_cost_limits(50, 20)"
```

---

## 🎯 Usage Examples

### **Basic Enhanced Profile Creation**
```python
import asyncio
from src.enhanced_avatar_pipeline import EnhancedAvatarSystemManager
from neo4j import GraphDatabase

async def create_profile():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    avatar_system = EnhancedAvatarSystemManager(
        neo4j_driver=driver,
        enable_llm_analysis=True
    )
    
    result = await avatar_system.create_enhanced_profile(
        person_identifier="Claire Russell",
        min_messages=100
    )
    
    print(f"Analysis completed: {result['status']}")
    print(f"Cost: ${result['total_cost']:.4f}")
    driver.close()

asyncio.run(create_profile())
```

### **Generate Different Avatar Types**
```python
# Casual conversation
casual_prompt = await avatar_system.generate_enhanced_avatar_prompt(
    person_identifier="Claire Russell",
    conversation_type="1:1",
    partners=["Ron"],
    topic="weekend plans"
)

# Professional meeting
work_prompt = await avatar_system.generate_enhanced_avatar_prompt(
    person_identifier="Claire Russell", 
    conversation_type="professional",
    partners=["Team"],
    topic="project update",
    context="Weekly standup meeting"
)

# Family group chat
family_prompt = await avatar_system.generate_enhanced_avatar_prompt(
    person_identifier="Claire Russell",
    conversation_type="group", 
    partners=["Mom", "Dad", "Sister"],
    topic="holiday planning"
)
```

### **Batch Processing Multiple People**
```python
# Analyze top 10 people with most messages
people_to_analyze = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

results = await avatar_system.batch_create_profiles(
    person_identifiers=people_to_analyze,
    min_messages=50,
    max_concurrent=3  # Conservative for cost control
)

successful = sum(1 for r in results if r.get("status") == "success")
total_cost = sum(r.get("total_cost", 0) for r in results)

print(f"Successfully analyzed {successful}/{len(results)} people")
print(f"Total cost: ${total_cost:.4f}")
```

---

## 🔧 Configuration

The system uses centralized configuration management:

### **Environment Variables**
```bash
# Required
export ANTHROPIC_API_KEY="your_claude_api_key"
export NEO4J_PASSWORD="your_neo4j_password"

# Optional
export DAILY_COST_LIMIT="50.0"
export MAX_CONCURRENT_REQUESTS="3" 
export MIN_MESSAGES_FOR_ANALYSIS="50"
```

### **Configuration File**
The system creates `~/.avatar-engine/avatar_config.json`:
```json
{
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "your_password"
  },
  "anthropic": {
    "model": "claude-3-sonnet-20240229",
    "daily_cost_limit": 50.0,
    "cost_alert_threshold": 20.0
  },
  "analysis": {
    "min_messages_for_analysis": 50,
    "personality_analysis_enabled": true,
    "relationship_analysis_enabled": true
  }
}
```

---

## 📊 Analysis Types

### **1. Personality Profiling**
- **Big Five Assessment**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- **Communication Style**: Formality, directness, emotional expressiveness
- **Behavioral Patterns**: Recurring themes and habits in communication

### **2. Relationship Dynamics**
- **Relationship Classification**: Family, friend, colleague, romantic, etc.
- **Communication Intimacy**: Depth and closeness of interactions
- **Interaction Patterns**: How communication varies by relationship type

### **3. Topic Expertise**
- **Knowledge Areas**: Subjects the person demonstrates expertise in
- **Engagement Levels**: How actively they discuss different topics
- **Interest Patterns**: Topics that generate the most engagement

### **4. Emotional Profiling**
- **Emotional Range**: Variety and intensity of emotional expression
- **Triggers**: Topics or situations that evoke strong responses
- **Emotional Patterns**: Consistent emotional themes and responses

---

## 🎨 Avatar Prompt Generation

The system generates sophisticated prompts that capture:

### **Personality Context**
```
"You are role-playing as Claire Russell. You are outgoing and social, 
cooperative and considerate, curious and open to new experiences. 
Communication style: casual and relaxed, gentle and diplomatic."
```

### **Relationship Context**  
```
"Your relationship with Ron is close friend. Communication pattern: 
warm and supportive with frequent humor and inside references."
```

### **Topic-Specific Context**
```
"You have significant knowledge and interest in health and wellness. 
You sometimes use expressions like 'that's amazing', 'I love that', 
'so interesting'."
```

### **Conversation Type Adaptation**
- **1:1 Conversations**: Personal, intimate communication style
- **Group Chats**: Engaging group dynamics, inclusive language
- **Professional**: Formal tone, work-appropriate language
- **Family**: Familiar expressions, personal references

---

## 🛡 Privacy & Security

- **Local Processing**: All conversation data remains in your local Neo4j database
- **API Key Security**: Stored as environment variables, never in files
- **Cost Controls**: Automatic spending limits prevent unexpected charges
- **Data Export**: Full control over your analysis data
- **Audit Trails**: Complete logging of all LLM analyses

---

## 🔍 System Requirements

### **Prerequisites**
- **Neo4j 5.0+** with existing conversation data loaded
- **Python 3.8+** with required dependencies
- **Memory**: 4GB+ recommended for large conversation datasets
- **Anthropic API Key** for Claude LLM integration

### **Data Schema Requirements**
Your Neo4j database should contain:
- `Person` nodes with `id`, `name`, `phone` properties
- `Message` nodes with `body`, `date`, `isFromMe` properties
- `GroupChat` nodes for conversation context
- Relationships: `Person-[:SENT]->Message`, `Message-[:SENT_TO]->GroupChat`

---

## 🚨 Troubleshooting

### **Common Issues**

**Configuration Errors**
```bash
# Fix configuration
python src/config_manager.py
```

**API Key Issues**
```bash
export ANTHROPIC_API_KEY="your_key_here"
python enhanced_deployment.py --status
```

**Database Connection Problems**
```bash
# Test connection
python examples/test_system.py
```

**Cost Limit Exceeded**
```bash
# Check costs and adjust limits
python enhanced_deployment.py --costs
python -c "from src.config_manager import ConfigManager; ConfigManager().update_cost_limits(100, 50)"
```

### **Performance Optimization**
- **Batch Processing**: Analyze multiple people concurrently
- **Message Filtering**: Focus on relevant conversations only
- **Concurrent Limits**: Balance speed vs cost with `max_concurrent_requests`
- **Incremental Analysis**: Avoid re-processing existing profiles

---

## 🤝 Integration Examples

### **Use with Claude**
```python
import anthropic

# Generate avatar prompt
avatar_prompt = await avatar_system.generate_enhanced_avatar_prompt(
    person_identifier="Claire Russell",
    topic="weekend plans"
)

# Use with Claude
claude_client = anthropic.Anthropic()
response = claude_client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[
        {"role": "user", "content": f"{avatar_prompt}\n\nHow was your weekend?"}
    ]
)

print("Avatar response:", response.content[0].text)
```

### **Use with OpenAI**
```python
import openai

# Use the same prompt with GPT
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": avatar_prompt},
        {"role": "user", "content": "How was your weekend?"}
    ]
)

print("Avatar response:", response.choices[0].message.content)
```

---

## 📈 Monitoring & Analytics

### **System Statistics**
```python
stats = avatar_system.get_system_statistics()
print(f"Profiles created: {stats['profiles_created']}")
print(f"Total cost: ${stats['total_cost']:.2f}")
print(f"LLM analyses: {stats['llm_analyses_completed']}")
```

### **Cost Monitoring**
```bash
# Daily cost tracking
python enhanced_deployment.py --costs

# Export cost history
python -c "from src.config_manager import CostMonitor, ConfigManager; print(CostMonitor(ConfigManager()).daily_costs)"
```

### **Quality Metrics**
- **Confidence Scores**: Reliability of each analysis
- **Token Usage**: Efficiency metrics for API usage
- **Processing Times**: Performance monitoring
- **Success Rates**: Analysis completion statistics

---

## 🎉 Next Steps

1. **Start with Test**: `python examples/test_system.py`
2. **Run Demo**: `python examples/enhanced_demo.py`  
3. **Analyze Your People**: `python enhanced_deployment.py --analyze-all --max-people 3`
4. **Generate Avatar Prompts**: Use the enhanced pipeline for your use cases
5. **Scale Up**: Increase cost limits and analyze your full conversation dataset

The Enhanced Avatar Intelligence System transforms your conversation data into rich, nuanced personality profiles that enable truly personalized AI interactions. Start small, monitor costs, and gradually scale to build comprehensive avatar intelligence for your entire network.

**Happy avatar building!** 🚀

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤖 About

Built with ❤️ for creating authentic AI avatars from real conversation data. Powered by Claude's advanced language understanding and Neo4j's graph database capabilities.
