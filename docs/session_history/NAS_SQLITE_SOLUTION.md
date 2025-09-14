# NAS Volume SQLite Issue - Summary & Solution

## Problem
SQLite database operations fail on network-mounted volumes (NAS) in macOS, even with Full Disk Access permissions.

## Root Cause
macOS applies special security restrictions to SQLite operations on network volumes. This is not a file corruption issue but a security block at the OS level.

## Symptoms
- Error: "unable to open database file" during query execution
- Files copy successfully but queries fail
- Works on local storage (`/tmp`, `~/Desktop`)
- Fails on NAS volumes (`/Volumes/FS001/`)

## Current Workaround

Use the local storage script:
```bash
python3 run_with_local_storage.py
```

This script:
1. Uses `/tmp` for database operations
2. Processes the extraction locally
3. Copies results back to NAS
4. Works immediately without permission changes

## Permanent Solution (To Be Implemented)

A new `LocalStorageManager` class will be created to:
- Automatically detect network volumes
- Create temporary local copies for processing
- Handle all SQLite operations locally
- Sync results back to NAS
- Clean up temporary files automatically

## Files Created for This Issue

### Diagnostic Scripts
- `diagnose_macos_security.py` - Check macOS security settings
- `diagnose_copy_methods.py` - Compare different copy methods
- `diagnose_query_failure.py` - Test query execution
- `fix_nas_security.py` - Test local vs NAS storage

### Solution Scripts
- `run_with_local_storage.py` - **USE THIS** for extraction
- `local_storage_config.py` - Configuration for local storage

### Documentation
- `LARGE_DATABASE_FIX.md` - Detailed documentation
- `SQLITE_FIX_SUMMARY.md` - Fix summary
- Updated `BACKLOG.md` - Added refactoring item
- Updated `DEVELOPMENT_STATE.md` - Session notes

## Quick Start

1. **For immediate use:**
   ```bash
   cd /Volumes/FS001/pythonscripts/Avatar-Engine
   python3 run_with_local_storage.py
   ```

2. **For testing the issue:**
   ```bash
   python3 fix_nas_security.py
   ```
   This will show local storage works but NAS doesn't.

3. **For full pipeline (after refactoring):**
   ```bash
   python3 src/pipelines/extraction_pipeline.py --limit 5000 --enable-llm
   ```

## Technical Details

The issue occurs because:
1. macOS treats network volumes as untrusted for database operations
2. SQLite needs to create temporary files for JOIN operations
3. These temp file operations are blocked on network volumes
4. Even Full Disk Access doesn't override this restriction

## Next Steps

1. **Short term:** Use `run_with_local_storage.py` for extraction
2. **Long term:** Implement the LocalStorageManager refactoring (see BACKLOG.md)
3. **Alternative:** Move project to local storage if possible

---
*Created: 2025-09-14*  
*Issue discovered in macOS 26 with NAS at /Volumes/FS001/*
