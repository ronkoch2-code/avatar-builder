# LocalStorageManager Documentation

## Overview

The `LocalStorageManager` is a critical component of the Avatar-Engine that solves a significant problem with SQLite database operations on network-mounted volumes (NAS, SMB, AFP, etc.). macOS and other operating systems impose security restrictions that prevent SQLite from properly accessing databases on network volumes, even with Full Disk Access permissions.

## The Problem

When working with SQLite databases stored on network volumes:
- SQLite operations fail with "unable to open database file" errors
- JOINs and complex queries fail even if the file can be read
- WAL (Write-Ahead Logging) mode causes additional complications
- The errors occur during query execution, not file access

This is particularly problematic for the Avatar-Engine project when:
- The project is stored on a NAS for backup/collaboration
- Database files need to be processed from network locations
- Output needs to be saved back to network storage

## The Solution

`LocalStorageManager` provides transparent handling of these issues by:
1. **Automatically detecting** when files are on network volumes
2. **Copying files to local temporary storage** for processing
3. **Performing all SQLite operations locally** where they work properly
4. **Syncing results back to the network** after processing
5. **Cleaning up temporary files** automatically

## Features

### Automatic Network Volume Detection
- Platform-specific detection (macOS, Linux, Windows planned)
- Multiple detection methods for reliability
- Falls back to conservative detection if uncertain

### Transparent Operation
- No code changes needed in calling code
- Works as a drop-in enhancement
- Maintains original file paths for user transparency

### Robust Error Handling
- Handles network failures gracefully
- Cleans up partial copies on failure
- Configurable keep-on-error for debugging

### Storage Management
- Enforces configurable size limits
- Tracks temporary file usage
- Provides storage statistics
- Automatic cleanup with force option

## Usage

### Basic Usage

```python
from storage_manager import LocalStorageManager

# Initialize the manager
manager = LocalStorageManager(
    auto_cleanup=True,  # Clean up temp files automatically
    keep_on_error=False,  # Don't keep files on error
    max_temp_size_gb=10.0  # Maximum 10GB of temp storage
)

# Check if a path is on a network volume
is_network = manager.is_network_volume(Path('/Volumes/NAS/file.db'))

# Copy a file to local storage if needed
if is_network:
    local_path = manager.create_local_copy(Path('/Volumes/NAS/file.db'))
    # Process the local file
    process_database(local_path)
    # Results are automatically synced back if needed
```

### Context Manager Usage

```python
from storage_manager import LocalStorageManager, with_local_storage

# Using the context manager for automatic cleanup
files = [
    Path('/Volumes/NAS/chat.db'),
    Path('/Volumes/NAS/contacts.db')
]

with with_local_storage(files) as local_paths:
    # Work with local copies
    for original, local in local_paths.items():
        process_database(local)
    # Files are automatically cleaned up on exit
```

### Integration with IMessageExtractor

The `LocalStorageManager` is fully integrated with `IMessageExtractor`:

```python
from imessage_extractor import IMessageExtractor

# Configure with network paths - storage manager handles it automatically
config = {
    'temp_dir': '/Volumes/NAS/temp',  # Network path is OK
    'output_dir': '/Volumes/NAS/output',  # Network path is OK
    'message_limit': 1000
}

extractor = IMessageExtractor(config)
# The extractor automatically uses local storage if needed
output = extractor.run_extraction_pipeline()
```

## Configuration Options

### LocalStorageManager Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `local_temp_base` | `/tmp/avatar_engine` | Base directory for temporary files |
| `auto_cleanup` | `True` | Automatically clean up temp files |
| `keep_on_error` | `False` | Keep temp files on error for debugging |
| `max_temp_size_gb` | `10.0` | Maximum temporary storage size in GB |

### Environment Variables

You can configure the default behavior through environment variables:

```bash
export AVATAR_LOCAL_TEMP_BASE=/var/tmp/avatar
export AVATAR_MAX_TEMP_SIZE_GB=20
export AVATAR_KEEP_ON_ERROR=true
```

## Network Volume Detection

The manager detects network volumes using multiple methods:

### macOS Detection
1. Checks for `/Volumes/` paths (excluding system volumes)
2. Looks for network indicators (FS, NAS, SMB, AFP, NFS)
3. Verifies with `mount` command for filesystem type
4. Checks filesystem flags with `statvfs`

### Linux Detection
1. Parses `/proc/mounts` for network filesystems
2. Identifies NFS, CIFS, SMBFS, WebDAV, SSHFS
3. Checks filesystem flags

### Fallback Detection
- URL patterns (smb://, afp://, nfs://, etc.)
- UNC paths (\\server\share)
- Conservative: assumes network if uncertain

## Error Handling

The manager handles various error conditions:

### Insufficient Space
```python
# Raises IOError if not enough temp space
IOError: Insufficient temp space. Need 5000000, have 1000000
```

### Size Limit Exceeded
```python
# Raises IOError if would exceed max_temp_size_bytes
IOError: Would exceed max temp size. Current: 8GB, File: 3GB, Max: 10GB
```

### Network Failures
```python
# Handles network copy failures gracefully
IOError: Failed to copy file: [Errno 5] Input/output error
```

## Performance Considerations

### Caching
- Files are only copied once per session
- Mappings are maintained to avoid duplicate copies
- Related files (WAL, SHM) are copied together

### Cleanup
- Automatic cleanup prevents disk space issues
- Force cleanup available for error cases
- Cleanup is ordered (files first, then directories)

### Size Management
- Enforces size limits before copying
- Tracks current usage across all temp files
- Provides statistics for monitoring

## Troubleshooting

### Common Issues

**Q: Files aren't being detected as network volumes**
A: Check the detection logic for your platform. You may need to add custom patterns for your network mount.

**Q: Temporary files aren't being cleaned up**
A: Ensure `auto_cleanup=True` and check for errors that might trigger `keep_on_error`.

**Q: Getting "Insufficient temp space" errors**
A: Either increase available disk space in `/tmp` or change `local_temp_base` to a location with more space.

**Q: Want to debug what's happening**
A: Set logging to DEBUG level and enable `keep_on_error=True`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

manager = LocalStorageManager(keep_on_error=True)
```

### Logging

The manager provides detailed logging:
- INFO: Major operations (initialization, copy, sync)
- DEBUG: Detection logic, file operations
- WARNING: Non-critical errors
- ERROR: Operation failures

## Testing

Run the test suite to verify functionality:

```bash
# Test network volume detection and integration
python3 test_storage_integration.py

# Test with actual extraction
python3 test_storage_integration.py --full-test
```

## Future Enhancements

Planned improvements:
- Windows support with UNC path detection
- Async copy operations for better performance
- Compression for network transfers
- Persistent cache across sessions
- S3/cloud storage support
- Configurable retry logic

## API Reference

### Class: LocalStorageManager

#### Methods

**`__init__(local_temp_base, auto_cleanup, keep_on_error, max_temp_size_gb)`**
Initialize the storage manager.

**`is_network_volume(path) -> bool`**
Check if a path is on a network volume.

**`create_local_copy(source_file, include_related) -> Path`**
Copy a file to local temporary storage.

**`sync_back_to_network(local_file, network_destination) -> Path`**
Copy results back to network storage.

**`cleanup(force)`**
Remove all temporary files and directories.

**`get_storage_stats() -> Dict`**
Get statistics about temporary storage usage.

**`save_mapping_metadata(metadata_file)`**
Save file mappings for debugging.

### Context Managers

**`with_local_storage(files, **kwargs)`**
Context manager for temporary local storage operations.

### Utility Functions

**`process_with_local_storage(network_file, process_func, sync_back, **kwargs)`**
Process a file using local storage if needed.

## License

Part of the Avatar-Engine project. See LICENSE file for details.

---
*Last Updated: 2025-09-14*
