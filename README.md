# Avatar-Engine Project Structure

## Overview
Enhanced Avatar Intelligence System with LLM-powered personality analysis for iMessage conversations stored in Neo4j.

## Directory Structure
```
Avatar-Engine/
│
├── enhanced_deployment.py      # Main deployment and management script
├── test_llm_fix.py             # Test script for LLM JSON parsing fix
│
├── src/                        # Source code modules
│   ├── config_manager.py       # Configuration and cost monitoring
│   ├── enhanced_avatar_pipeline.py  # Main avatar system manager
│   ├── llm_integrator.py       # LLM integration with Claude (FIXED)
│   ├── llm_integrator_original.py  # Backup of original LLM integrator
│   └── [other modules]
│
├── docs/                       # Documentation
│   └── llm_json_parsing_fix.md # Documentation of JSON parsing fix
│
└── README.md                   # This file
```

## Configuration
Configuration stored in: `~/.avatar-engine/avatar_config.json`

### Required Configuration
- **Neo4j**: Database connection settings
- **Anthropic API**: API key and model selection
- **Cost Limits**: Daily spending limits
- **System Settings**: LLM analysis toggles

## Usage

### Basic Commands
```bash
# Deploy enhanced schema
python3 enhanced_deployment.py --deploy

# Check system status
python3 enhanced_deployment.py --status

# List available people
python3 enhanced_deployment.py --list-people

# Analyze specific person
python3 enhanced_deployment.py --analyze-person "Person Name"

# Analyze all people (with limit)
python3 enhanced_deployment.py --analyze-all --max-people 5

# Export profiles
python3 enhanced_deployment.py --export

# Show costs
python3 enhanced_deployment.py --costs
```

### Testing
```bash
# Run JSON parsing tests
python3 test_llm_fix.py
```

## Key Features
- **Personality Profiling**: Big Five personality analysis
- **Relationship Dynamics**: Analyze communication patterns between people
- **Communication Style**: Formality, directness, emotional expression
- **Cost Monitoring**: Track API usage and costs
- **Batch Processing**: Analyze multiple people efficiently
- **Error Recovery**: Robust JSON parsing and error handling

## Recent Updates
- **2025-08-27**: Fixed LLM JSON parsing issue
  - Added robust JSON extraction from various response formats
  - Enhanced prompt engineering for JSON-only responses
  - Improved error handling and logging

## Dependencies
- `neo4j`: Graph database driver
- `anthropic`: Claude API client
- `pydantic`: Data validation
- `pandas`: Data processing
- `tenacity`: Retry logic
- Standard library: asyncio, json, logging, etc.

## Troubleshooting

### JSON Parsing Errors
See `docs/llm_json_parsing_fix.md` for details on the fix.

### Rate Limiting (429 errors)
- Reduce `max_concurrent` in LLM integrator
- Add delays between requests
- Monitor daily usage against limits

### Cost Management
- Set daily cost limits in configuration
- Use `--max-people` flag to limit batch processing
- Check costs regularly with `--costs` flag

## Backup and Recovery
- Original code backed up with `_original` suffix
- Configuration backed up in `~/.avatar-engine/`
- Neo4j data persisted in database

## Future Enhancements
- [ ] Web interface for profile viewing
- [ ] Real-time message processing
- [ ] Advanced visualization of relationships
- [ ] Export to various formats (PDF, HTML)
- [ ] Integration with other messaging platforms

## Contact
For issues or questions, refer to documentation in `/docs` directory.
