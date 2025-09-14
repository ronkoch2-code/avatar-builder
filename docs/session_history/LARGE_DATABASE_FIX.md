# SQLite Large Database Fix Summary

## Problem
Your iMessage database (544MB) was failing with:
1. "database disk image is malformed" - caused by WAL checkpoint corruption
2. Timeout issues with sqlite3 CLI backup (120 second timeout too short)

## Solution Applied

### Key Changes to `imessage_extractor.py`:

1. **No Database Modification** - The checkpoint code that was corrupting the database has been removed
2. **Smart Copy Strategy**:
   - For databases < 200MB: Use sqlite3 CLI backup (clean copy)
   - For databases > 200MB: Use direct file copy (much faster)
   - Always copy WAL/SHM files when present
3. **Proper Timeouts** - 5 minute timeout for CLI backup operations
4. **Read-Only Access** - Database queries use read-only mode

## Current Implementation

The `copy_databases_secure()` method now:
- ✅ Detects database size and chooses appropriate method
- ✅ Copies WAL/SHM files for WAL mode databases
- ✅ Removes macOS extended attributes
- ✅ Sets proper permissions (644)
- ✅ Does NOT modify the database (no checkpoint, no journal mode change)

## Testing Your Fix

### Quick Test (5 messages):
```bash
python3 test_sqlite_fixes.py
```

### Test with Different Methods:
```bash
# Test with longer timeout
python3 fix_with_longer_timeout.py

# Test CLI backup specifically
python3 test_cli_backup.py
```

### Full Pipeline:
```bash
python3 src/pipelines/extraction_pipeline.py --limit 5000 --enable-llm
```

## Recommendations

For your 544MB database:
1. **Use direct copy method** (fastest) - This is now the default for large databases
2. **Keep WAL files together** - Always copy chat.db-wal and chat.db-shm
3. **Don't modify after copying** - Prevents corruption
4. **Use read-only mode** - Already implemented in `extract_messages()`

## If Issues Persist

1. **Close Messages app** - Ensures database isn't locked
2. **Check permissions** - Make sure you can read the source database
3. **Install sqlite3 CLI** (optional): `brew install sqlite3`
4. **Increase timeout** - Edit the timeout value in the code if needed

## Manual Application

If the automatic script didn't work, the key fix is already applied:
- The checkpoint code has been removed
- WAL files are being copied
- Read-only mode is used for queries

Just ensure you have all three files copied:
- chat.db (main database)
- chat.db-wal (write-ahead log)
- chat.db-shm (shared memory)

---
*Last Updated: 2025-09-13*
