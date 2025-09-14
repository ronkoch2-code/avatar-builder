# Avatar-Engine Utilities

This directory contains utility scripts and tools for the Avatar-Engine project.

## Directory Structure

### Main Utilities (./utilities/)
- **generate_secure_env.py** - Generates secure environment configuration with encryption keys
- **audit_code_completeness.py** - Audits code for completeness, finding TODOs and incomplete implementations
- **run_extractor.py** - Main runner script for the iMessage extraction pipeline
- **run_with_local_storage.py** - NAS workaround runner that uses local temp storage for SQLite operations
- **backup_neo4j.py** - Backs up Neo4j database
- **reset_neo4j.py** - Resets Neo4j database to clean state
- **setup_neo4j.py** - Sets up Neo4j database with schema
- **validate_data.py** - Validates data integrity
- **organize_project_files.py** - Organizes project files

### Debug Tools (./debug/)
Contains test scripts and debugging tools used during development:
- Test scripts (test_*.py) - Various test utilities for different components
- Debug scripts (debug_*.py) - Debugging tools for environment and configuration
- Verify scripts (verify_*.py) - Verification tools for fixes and configurations
- Run scripts (run_*.py) - Test runners and configuration testers

### Archived Fixes (./archived_fixes/)
Contains historical fix scripts from various debugging sessions:
- Fix scripts (fix_*.py) - Scripts that fixed specific issues
- Apply scripts (apply_*.py) - Scripts that applied fixes
- Restore scripts (restore_*.py) - Scripts that restored functionality
- Workaround scripts - Various workarounds for specific issues

### SLM Tools (./slm/)
Structured Local Memory (SLM) management tools:
- **add_slm_to_git.py** - Adds SLM files to git
- **complete_slm_git_integration.py** - Completes SLM git integration
- **quick_add_slm.py** - Quick script to add SLM files
- **analyze_organization.py** - Analyzes project organization
- **final_prep_repository.py** - Final repository preparation

### Diagnostic Scripts (../diagnostic_scripts/)
Comprehensive diagnostic tools:
- **diagnose_extractor.py** - Diagnoses extractor issues
- **diagnose_pipeline_issue.py** - Diagnoses pipeline problems
- **diagnose_sqlite_*.py** - SQLite-specific diagnostics
- **diagnose_macos_security.py** - macOS security diagnostics
- **diagnose_copy_methods.py** - File copy method diagnostics
- **diagnose_query_failure.py** - Query failure diagnostics

## Usage

### Running the Extraction Pipeline
```bash
# Standard extraction
python3 utilities/run_extractor.py

# With NAS workaround (uses local temp storage)
python3 utilities/run_with_local_storage.py
```

### Environment Setup
```bash
# Generate secure environment configuration
python3 utilities/generate_secure_env.py
```

### Code Auditing
```bash
# Audit code for completeness
python3 utilities/audit_code_completeness.py
```

### Neo4j Management
```bash
# Setup Neo4j
python3 utilities/setup_neo4j.py

# Backup Neo4j
python3 utilities/backup_neo4j.py

# Reset Neo4j
python3 utilities/reset_neo4j.py
```

## Notes
- Debug and archived_fixes directories contain historical scripts for reference
- Most active utilities are in the main utilities directory
- Diagnostic scripts remain in their original location for backward compatibility

*Last Updated: 2025-09-14*
