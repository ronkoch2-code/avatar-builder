#!/usr/bin/env python3
"""
Local Storage Manager for Network Volume Compatibility

This module provides transparent handling of SQLite database operations
on network-mounted volumes (NAS/SMB/AFP) by automatically detecting
network storage and using local temporary storage for operations.

Author: Avatar-Engine Team
Date: 2025-09-14
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from contextlib import contextmanager
import hashlib
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class LocalStorageManager:
    """
    Manages temporary local copies for network volume operations.
    
    This class automatically detects when files are on network volumes
    and transparently handles copying to local storage for SQLite operations,
    then syncing results back to the network location.
    """
    
    def __init__(
        self,
        local_temp_base: Optional[Path] = None,
        auto_cleanup: bool = True,
        keep_on_error: bool = False,
        max_temp_size_gb: float = 10.0
    ):
        """
        Initialize the LocalStorageManager.
        
        Args:
            local_temp_base: Base directory for temporary files (default: /tmp/avatar_engine)
            auto_cleanup: Automatically cleanup temporary files
            keep_on_error: Keep temporary files on error for debugging
            max_temp_size_gb: Maximum size for temporary storage in GB
        """
        self.local_temp_base = local_temp_base or Path('/tmp/avatar_engine')
        self.auto_cleanup = auto_cleanup
        self.keep_on_error = keep_on_error
        self.max_temp_size_bytes = int(max_temp_size_gb * 1024 * 1024 * 1024)
        
        # Track temporary files and directories for cleanup
        self.temp_files: Set[Path] = set()
        self.temp_dirs: Set[Path] = set()
        self.file_mappings: Dict[Path, Path] = {}  # Original -> Temp mapping
        
        # Create base temp directory if it doesn't exist
        self.local_temp_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorageManager initialized with temp base: {self.local_temp_base}")
    
    def is_network_volume(self, path: Path) -> bool:
        """
        Detect if a path is on a network volume.
        
        Uses multiple detection methods:
        1. Path patterns (e.g., /Volumes/ on macOS)
        2. Filesystem type checks
        3. Mount point analysis
        
        Args:
            path: Path to check
            
        Returns:
            True if path is on a network volume, False otherwise
        """
        try:
            path = Path(path).resolve()
            path_str = str(path)
            
            # Platform-specific detection
            import platform
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                # Check for common network mount points on macOS
                if path_str.startswith('/Volumes/'):
                    mount_point = path_str.split('/')[2] if len(path_str.split('/')) > 2 else ''
                    
                    # Known network indicators
                    network_indicators = ['FS', 'NAS', 'SMB', 'AFP', 'NFS', 'CIFS']
                    if any(indicator in mount_point.upper() for indicator in network_indicators):
                        logger.debug(f"Detected network volume (macOS): {mount_point}")
                        return True
                    
                    # Check if it's not the system volume
                    if mount_point and mount_point != 'Macintosh HD':
                        # Use mount command to check if it's a network mount
                        try:
                            import subprocess
                            result = subprocess.run(
                                ['mount'], 
                                capture_output=True, 
                                text=True, 
                                timeout=5
                            )
                            if result.returncode == 0:
                                for line in result.stdout.split('\n'):
                                    if f'/Volumes/{mount_point}' in line:
                                        # Check for network filesystem types
                                        if any(fs in line.lower() for fs in ['smbfs', 'afpfs', 'nfs', 'webdav']):
                                            logger.debug(f"Confirmed network mount via mount command: {mount_point}")
                                            return True
                        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                            pass
            
            elif system == 'linux':
                # Check /proc/mounts for network filesystems
                try:
                    with open('/proc/mounts', 'r') as f:
                        for line in f:
                            parts = line.split()
                            if len(parts) >= 3:
                                mount_path = parts[1]
                                fs_type = parts[2]
                                if path_str.startswith(mount_path):
                                    network_fs_types = ['nfs', 'nfs4', 'cifs', 'smbfs', 'webdav', 'fuse.sshfs']
                                    if any(fs in fs_type.lower() for fs in network_fs_types):
                                        logger.debug(f"Detected network filesystem (Linux): {fs_type}")
                                        return True
                except (IOError, OSError):
                    pass
            
            # Generic filesystem flag check (works on most Unix-like systems)
            try:
                stat = os.statvfs(str(path))
                # Check for remote filesystem flag
                # ST_REMOTE flag (0x1000) indicates remote filesystem
                if hasattr(stat, 'f_flag') and (stat.f_flag & 0x1000):
                    logger.debug(f"Detected remote filesystem via statvfs flags: {path}")
                    return True
            except (OSError, AttributeError):
                pass
            
            # Check for network path patterns (fallback)
            network_patterns = ['smb://', 'afp://', 'nfs://', '\\\\', '//', 'ftp://', 'sftp://']
            if any(pattern in path_str.lower() for pattern in network_patterns):
                logger.debug(f"Detected network path pattern: {path}")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if path is network volume: {e}")
            # Conservative: assume it might be network if we can't determine
            # This ensures we use safe local storage in uncertain cases
            return True  # Changed from False to True for safety
    
    def _generate_temp_path(self, original_path: Path, preserve_structure: bool = True) -> Path:
        """
        Generate a unique temporary path for a file.
        
        Args:
            original_path: Original file path
            preserve_structure: Whether to preserve directory structure
            
        Returns:
            Temporary file path
        """
        # Create a unique session directory
        session_id = hashlib.md5(
            f"{datetime.now().isoformat()}_{os.getpid()}".encode()
        ).hexdigest()[:8]
        
        session_dir = self.local_temp_base / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dirs.add(session_dir)
        
        if preserve_structure:
            # Preserve relative directory structure
            relative_parts = original_path.parts[-3:] if len(original_path.parts) > 3 else original_path.parts
            temp_path = session_dir / Path(*relative_parts)
        else:
            # Just use filename
            temp_path = session_dir / original_path.name
        
        # Ensure parent directory exists
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        return temp_path
    
    def create_local_copy(self, source_file: Path, include_related: bool = True) -> Path:
        """
        Copy a file from network storage to local temporary storage.
        
        Args:
            source_file: Source file on network volume
            include_related: Also copy related files (e.g., SQLite WAL/SHM files)
            
        Returns:
            Path to the local copy
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If copy operation fails
        """
        source_file = Path(source_file).resolve()
        
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        # Check if already copied
        if source_file in self.file_mappings:
            logger.debug(f"File already copied: {source_file}")
            return self.file_mappings[source_file]
        
        # Generate temporary path
        temp_path = self._generate_temp_path(source_file)
        
        try:
            # Check available space and enforce size limits
            stat = os.statvfs(str(self.local_temp_base))
            available_bytes = stat.f_bavail * stat.f_frsize
            file_size = source_file.stat().st_size
            
            # Calculate current temp usage
            current_temp_usage = sum(f.stat().st_size for f in self.temp_files if f.exists())
            
            if file_size > available_bytes:
                raise IOError(f"Insufficient temp space. Need {file_size}, have {available_bytes}")
            
            # Check if adding this file would exceed max temp size
            if current_temp_usage + file_size > self.max_temp_size_bytes:
                raise IOError(
                    f"Would exceed max temp size. Current: {current_temp_usage}, "
                    f"File: {file_size}, Max: {self.max_temp_size_bytes}"
                )
            
            # Copy the main file with error handling
            logger.info(f"Copying {source_file} to {temp_path}")
            try:
                shutil.copy2(source_file, temp_path)
            except (IOError, OSError) as e:
                logger.error(f"Failed to copy {source_file}: {e}")
                # Clean up partial copy if it exists
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except:
                        pass
                raise IOError(f"Failed to copy file: {e}") from e
            
            self.temp_files.add(temp_path)
            self.file_mappings[source_file] = temp_path
            
            # Copy related files if requested (for SQLite databases)
            if include_related:
                related_extensions = ['.wal', '.shm', '-wal', '-shm', '.db-wal', '.db-shm']
                for ext in related_extensions:
                    related_source = source_file.parent / f"{source_file.stem}{ext}"
                    if related_source.exists():
                        related_temp = temp_path.parent / f"{temp_path.stem}{ext}"
                        logger.debug(f"Copying related file: {related_source}")
                        shutil.copy2(related_source, related_temp)
                        self.temp_files.add(related_temp)
            
            logger.info(f"Successfully copied to local storage: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to create local copy: {e}")
            # Cleanup partial copy
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def sync_back_to_network(self, local_file: Path, network_destination: Optional[Path] = None) -> Path:
        """
        Copy processed results back to network storage.
        
        Args:
            local_file: Local file to sync back
            network_destination: Destination on network (uses original location if None)
            
        Returns:
            Path to the file on network storage
        """
        local_file = Path(local_file).resolve()
        
        # Find original network path if not specified
        if network_destination is None:
            # Look for the original path in our mappings
            for orig, temp in self.file_mappings.items():
                if temp == local_file:
                    network_destination = orig
                    break
            
            if network_destination is None:
                # Use original structure under data directory
                network_destination = Path('/Volumes/FS001/pythonscripts/Avatar-Engine/data') / local_file.name
        
        network_destination = Path(network_destination)
        
        try:
            # Ensure destination directory exists
            network_destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file back to network
            logger.info(f"Syncing {local_file} back to {network_destination}")
            shutil.copy2(local_file, network_destination)
            
            logger.info(f"Successfully synced to network: {network_destination}")
            return network_destination
            
        except Exception as e:
            logger.error(f"Failed to sync back to network: {e}")
            raise
    
    def cleanup(self, force: bool = False):
        """
        Remove all temporary files and directories.
        
        Args:
            force: Force cleanup even if keep_on_error is True
        """
        if not self.auto_cleanup and not force:
            logger.debug("Auto-cleanup disabled, skipping cleanup")
            return
        
        logger.info("Cleaning up temporary files")
        
        # Remove files first
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Removed temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        
        # Remove directories
        for temp_dir in sorted(self.temp_dirs, reverse=True):  # Remove deepest first
            try:
                if temp_dir.exists() and temp_dir.is_dir():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Removed temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
        
        # Clear tracking
        self.temp_files.clear()
        self.temp_dirs.clear()
        self.file_mappings.clear()
        
        logger.info("Cleanup completed")
    
    def get_local_path(self, network_path: Path) -> Path:
        """
        Get the local temporary path for a network file.
        
        Args:
            network_path: Path on network storage
            
        Returns:
            Local temporary path if file is copied, otherwise original path
        """
        network_path = Path(network_path).resolve()
        return self.file_mappings.get(network_path, network_path)
    
    @contextmanager
    def local_storage_context(self, files: List[Path], include_related: bool = True):
        """
        Context manager for working with files in local storage.
        
        Args:
            files: List of files to copy to local storage
            include_related: Also copy related files
            
        Yields:
            Dictionary mapping original paths to local paths
        """
        local_paths = {}
        
        try:
            # Copy all files to local storage
            for file_path in files:
                file_path = Path(file_path)
                if file_path.exists() and self.is_network_volume(file_path):
                    local_path = self.create_local_copy(file_path, include_related)
                    local_paths[file_path] = local_path
                else:
                    # File is already local or doesn't need copying
                    local_paths[file_path] = file_path
            
            yield local_paths
            
        except Exception as e:
            logger.error(f"Error in local storage context: {e}")
            if not self.keep_on_error:
                self.cleanup(force=True)
            raise
        
        finally:
            if self.auto_cleanup and not self.keep_on_error:
                self.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        if exc_type is not None:
            logger.error(f"Exception in context: {exc_type.__name__}: {exc_val}")
            if self.keep_on_error:
                logger.info(f"Keeping temp files for debugging at: {self.local_temp_base}")
                return False
        
        if self.auto_cleanup:
            self.cleanup()
        
        return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about temporary storage usage.
        
        Returns:
            Dictionary with storage statistics
        """
        total_size = sum(f.stat().st_size for f in self.temp_files if f.exists())
        
        # Get available space
        stat = os.statvfs(str(self.local_temp_base))
        available_bytes = stat.f_bavail * stat.f_frsize
        total_bytes = stat.f_blocks * stat.f_frsize
        
        return {
            'temp_files_count': len(self.temp_files),
            'temp_dirs_count': len(self.temp_dirs),
            'total_temp_size_bytes': total_size,
            'total_temp_size_mb': total_size / (1024 * 1024),
            'available_space_bytes': available_bytes,
            'available_space_gb': available_bytes / (1024 * 1024 * 1024),
            'total_space_bytes': total_bytes,
            'total_space_gb': total_bytes / (1024 * 1024 * 1024),
            'max_allowed_size_bytes': self.max_temp_size_bytes,
            'max_allowed_size_gb': self.max_temp_size_bytes / (1024 * 1024 * 1024)
        }
    
    def save_mapping_metadata(self, metadata_file: Optional[Path] = None):
        """
        Save file mapping metadata for debugging or recovery.
        
        Args:
            metadata_file: Path to save metadata (default: temp_dir/mappings.json)
        """
        if metadata_file is None:
            metadata_file = self.local_temp_base / 'mappings.json'
        
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'pid': os.getpid(),
            'mappings': {
                str(orig): str(temp) for orig, temp in self.file_mappings.items()
            },
            'temp_files': [str(f) for f in self.temp_files],
            'temp_dirs': [str(d) for d in self.temp_dirs],
            'stats': self.get_storage_stats()
        }
        
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved mapping metadata to: {metadata_file}")
        except Exception as e:
            logger.warning(f"Failed to save mapping metadata: {e}")


# Convenience functions for common use cases

@contextmanager
def with_local_storage(files: List[Path], **kwargs):
    """
    Convenience context manager for temporary local storage operations.
    
    Args:
        files: List of files to work with locally
        **kwargs: Additional arguments for LocalStorageManager
        
    Example:
        with with_local_storage([db_path]) as local_paths:
            local_db = local_paths[db_path]
            # Work with local_db
    """
    manager = LocalStorageManager(**kwargs)
    with manager.local_storage_context(files) as local_paths:
        yield local_paths


def process_with_local_storage(
    network_file: Path,
    process_func,
    sync_back: bool = True,
    **manager_kwargs
) -> Any:
    """
    Process a file using local storage if it's on a network volume.
    
    Args:
        network_file: File to process
        process_func: Function to process the file (takes file path as argument)
        sync_back: Whether to sync results back to network
        **manager_kwargs: Additional arguments for LocalStorageManager
        
    Returns:
        Result from process_func
    """
    manager = LocalStorageManager(**manager_kwargs)
    
    if manager.is_network_volume(network_file):
        logger.info(f"Processing {network_file} via local storage")
        local_file = manager.create_local_copy(network_file)
        
        try:
            result = process_func(local_file)
            
            if sync_back:
                manager.sync_back_to_network(local_file, network_file)
            
            return result
            
        finally:
            if manager.auto_cleanup:
                manager.cleanup()
    else:
        # File is already local
        logger.debug(f"Processing {network_file} directly (local storage)")
        return process_func(network_file)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test network volume detection
    test_paths = [
        Path('/tmp/test.db'),
        Path('/Volumes/FS001/test.db'),
        Path('/Users/test/file.db'),
        Path('/Volumes/NAS/data/file.db')
    ]
    
    manager = LocalStorageManager()
    
    print("Network Volume Detection Test:")
    print("-" * 40)
    for path in test_paths:
        is_network = manager.is_network_volume(path)
        print(f"{path}: {'Network' if is_network else 'Local'}")
    
    print("\nStorage Stats:")
    print("-" * 40)
    stats = manager.get_storage_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
