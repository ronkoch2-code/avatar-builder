# Avatar-Engine Utilities

This directory contains utility scripts for maintaining and managing the Avatar-Engine Neo4j database and related operations.

## Quick Setup

### First Time Setup
If you haven't configured Neo4j yet, run the setup script:
```bash
python3 utilities/setup_neo4j.py
```

This will:
- Create a `.env` file with your Neo4j credentials
- Test the connection
- Set up environment variables

### Debugging Connection Issues
If you're having authentication problems:
```bash
python3 utilities/debug_neo4j.py
```

This will show:
- Current environment variables
- Config file locations
- Connection test results
- Specific recommendations

## Available Utilities

### 1. reset_neo4j.py
**Purpose:** Safely reset the Neo4j database while preserving schema

**Features:**
- Deletes all data nodes (Person, Message, Profile, etc.)
- Preserves database schema (constraints and indexes)
- Preserves system metadata nodes
- Creates backup statistics before reset
- Supports dry-run mode for safety

**Usage:**
```bash
# Dry run - see what would be deleted
python3 utilities/reset_neo4j.py --dry-run

# Reset with automatic backup
python3 utilities/reset_neo4j.py

# Reset without backup (use carefully!)
python3 utilities/reset_neo4j.py --no-backup

# Custom Neo4j connection
python3 utilities/reset_neo4j.py --uri bolt://localhost:7687 --username neo4j --password mypass
```

### 2. backup_neo4j.py
**Purpose:** Create comprehensive backups of Neo4j data

**Features:**
- Export all nodes and relationships to JSON
- Timestamped backup files
- Compression support
- Selective backup by node types

**Usage:**
```bash
# Full backup
python3 utilities/backup_neo4j.py

# Backup specific node types
python3 utilities/backup_neo4j.py --nodes Person Message

# Compressed backup
python3 utilities/backup_neo4j.py --compress
```

### 3. validate_data.py
**Purpose:** Validate data integrity in Neo4j database

**Features:**
- Check for orphaned nodes
- Verify relationship integrity
- Validate required properties
- Generate integrity report

**Usage:**
```bash
# Run full validation
python3 utilities/validate_data.py

# Check specific validations
python3 utilities/validate_data.py --check orphans relationships

# Generate detailed report
python3 utilities/validate_data.py --report
```

### 4. migrate_schema.py
**Purpose:** Apply schema migrations to Neo4j database

**Features:**
- Apply schema updates from .cypher files
- Track migration history
- Rollback support
- Dry-run mode

**Usage:**
```bash
# Apply pending migrations
python3 utilities/migrate_schema.py

# Check migration status
python3 utilities/migrate_schema.py --status

# Rollback last migration
python3 utilities/migrate_schema.py --rollback
```

## Configuration

All utilities read configuration from (in order of priority):
1. Command-line arguments (highest priority)
2. `.env` file in project root
3. Environment variables (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
4. `~/.avatar-engine/avatar_config.json` (if exists)
5. Default values

### Setting Up Authentication

**Method 1: Use the setup script (recommended)**
```bash
python3 utilities/setup_neo4j.py
```

**Method 2: Create .env file manually**
```bash
cp .env.example .env
# Edit .env and add your Neo4j password
```

**Method 3: Export environment variables**
```bash
export NEO4J_PASSWORD='your_password'
export NEO4J_URI='bolt://localhost:7687'
export NEO4J_USERNAME='neo4j'
```

**Method 4: Pass as command-line arguments**
```bash
python3 utilities/reset_neo4j.py --password 'your_password' --uri 'bolt://localhost:7687'
```

## Backup Directory

Backups are stored in `utilities/backups/` with timestamp-based naming:
- `neo4j_backup_YYYYMMDD_HHMMSS.json`
- `neo4j_export_YYYYMMDD_HHMMSS.cypher`

## Safety Features

All destructive operations include:
- Confirmation prompts
- Dry-run mode
- Automatic backups (unless explicitly disabled)
- Transaction rollback on errors
- Detailed logging

## Requirements

- Python 3.8+
- neo4j driver (`pip install neo4j`)
- Access to Neo4j database (default: bolt://localhost:7687)

## Development

To add new utilities:
1. Create a new Python script in this directory
2. Follow the existing pattern for configuration and logging
3. Update this README with documentation
4. Add tests in the `tests/utilities/` directory

## Troubleshooting

**Connection Issues:**
```bash
# Test Neo4j connection
python3 -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')).verify_connectivity()"
```

**Permission Issues:**
- Ensure Neo4j user has appropriate permissions
- Check file permissions for backup directory

**Memory Issues:**
- Use batch processing for large datasets
- Adjust batch_size parameter in scripts
