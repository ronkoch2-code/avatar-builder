#!/usr/bin/env python3
"""
iMessage Data Extractor for Avatar-Engine
==========================================

Extracts and processes messages from macOS iMessage database (chat.db)
and enriches them with contact information from AddressBook.

This module is the first stage in the Avatar-Engine pipeline, converting
raw iMessage data into structured JSON for further processing.

Author: Avatar-Engine Team
Date: 2025-09-07
Version: 1.0.0
"""

import sqlite3
import datetime
import os
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import shutil
import subprocess
import getpass
from dotenv import load_dotenv

# Load environment variables BEFORE importing security modules
load_dotenv()

from security_utils import SecurityManager, SecureLogger, InputValidator
from storage_manager import LocalStorageManager

# Configure logging
logger = SecureLogger(__name__, log_file="logs/imessage_extractor.log")
security_manager = SecurityManager()
input_validator = InputValidator()


@dataclass
class MessageRecord:
    """Data class for message records"""
    rowid: int
    date: str
    body: str
    phone_number: str
    is_from_me: bool
    cache_roomname: Optional[str] = None
    group_chat_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_hash: Optional[str] = None  # Anonymized phone for privacy


@dataclass
class Contact:
    """Data class for contact records"""
    first_name: Optional[str]
    last_name: Optional[str]
    full_number: str
    clean_number: str


class IMessageExtractor:
    """Main class for extracting and processing iMessage data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the iMessage extractor
        
        Args:
            config: Configuration dictionary with paths and options
        """
        # Start with default config and update with provided config
        self.config = self._get_default_config()
        if config:
            # Merge provided config with defaults
            for key, value in config.items():
                if value is not None:  # Only override if value is explicitly set
                    self.config[key] = value
        
        self.security_manager = security_manager
        self.input_validator = input_validator
        self.logger = logger
        
        # Validate configuration
        self._validate_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        home = Path.home()
        return {
            'source_chat_db': str(home / 'Library/Messages/chat.db'),
            'source_addressbook': str(home / 'Library/Application Support/AddressBook'),
            'output_dir': str(Path.cwd() / 'data/extracted'),
            'temp_dir': str(Path.cwd() / 'data/temp'),
            'anonymize_phones': True,
            'human_readable_dates': True,
            'message_limit': None,  # None = all messages
            'batch_size': 1000,  # Process messages in batches
            'cleanup_temp': True
        }
    
    def _validate_config(self):
        """Validate configuration paths and settings"""
        # Source paths are system paths and don't need traversal validation
        # They're read-only access to system databases
        source_paths = ['source_chat_db', 'source_addressbook']
        
        # Output paths need validation to prevent writing to dangerous locations
        output_paths = ['output_dir', 'temp_dir']
        
        # Validate output paths for security (these are where we write)
        for key in output_paths:
            if key in self.config and self.config[key]:
                path_str = str(self.config[key])
                # For output directories, ensure they're not trying to write to system directories
                if path_str.startswith('/'):
                    # Check it's not a sensitive system directory
                    sensitive_dirs = ['/etc/', '/root/', '/proc/', '/sys/', '/dev/', '/bin/', '/sbin/']
                    if any(path_str.startswith(d) for d in sensitive_dirs):
                        raise ValueError(f"Cannot write to system directory: {path_str}")
                # Check for directory traversal
                if '..' in path_str:
                    raise ValueError(f"Directory traversal detected in {key}: {path_str}")
        
        # Create output directories if they don't exist
        for dir_key in output_paths:
            dir_path = Path(self.config[dir_key])
            dir_path.mkdir(parents=True, exist_ok=True, mode=0o750)
    
    def copy_databases_secure(self, dest_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Securely copy chat.db and AddressBook database to working directory
        Handles WAL files and extended attributes for SQLite databases
        Automatically uses local storage for network volumes
        
        Args:
            dest_dir: Destination directory (uses temp_dir from config if None)
            
        Returns:
            Tuple of (chat_db_path, addressbook_db_path)
        """
        dest_dir = dest_dir or self.config['temp_dir']
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        # Initialize LocalStorageManager to handle network volumes
        storage_manager = LocalStorageManager(
            auto_cleanup=False,  # We'll handle cleanup ourselves
            keep_on_error=True   # Keep files for debugging if there's an error
        )
        
        # Check if destination is on a network volume
        if storage_manager.is_network_volume(dest_path):
            self.logger.log_event("storage_detection", {
                "path": str(dest_path),
                "type": "network_volume",
                "action": "using_local_storage"
            })
            # Use local storage instead
            dest_path = storage_manager.local_temp_base / 'databases'
            dest_path.mkdir(parents=True, exist_ok=True, mode=0o750)
            # Store the storage manager for later cleanup
            self._storage_manager = storage_manager
            self._original_dest_dir = Path(dest_dir)
        else:
            self.logger.log_event("storage_detection", {
                "path": str(dest_path),
                "type": "local_storage",
                "action": "direct_copy"
            })
            self._storage_manager = None
            self._original_dest_dir = None
        
        # Destination paths
        dest_chat = dest_path / 'chat.db'
        dest_ab = dest_path / 'AddressBook-v22.abcddb'
        
        self.logger.log_event("database_copy", {
            "action": "starting",
            "dest_chat": str(dest_chat),
            "dest_addressbook": str(dest_ab)
        })
        
        try:
            # Copy chat.db with WAL handling
            source_chat = Path(self.config['source_chat_db'])
            if source_chat.exists():
                # Copy main database file
                shutil.copy2(source_chat, dest_chat)
                
                # Copy WAL and SHM files if they exist
                source_dir = source_chat.parent
                wal_file = source_dir / 'chat.db-wal'
                shm_file = source_dir / 'chat.db-shm'
                
                if wal_file.exists():
                    shutil.copy2(wal_file, dest_path / 'chat.db-wal')
                    self.logger.log_event("database_copy", {
                        "action": "copied_wal",
                        "file": "chat.db-wal"
                    })
                
                if shm_file.exists():
                    shutil.copy2(shm_file, dest_path / 'chat.db-shm')
                    self.logger.log_event("database_copy", {
                        "action": "copied_shm",
                        "file": "chat.db-shm"
                    })
                
                # Remove extended attributes on macOS (quarantine flags, etc.)
                try:
                    subprocess.run(['xattr', '-c', str(dest_chat)], 
                                 check=False, capture_output=True)
                    if (dest_path / 'chat.db-wal').exists():
                        subprocess.run(['xattr', '-c', str(dest_path / 'chat.db-wal')], 
                                     check=False, capture_output=True)
                    if (dest_path / 'chat.db-shm').exists():
                        subprocess.run(['xattr', '-c', str(dest_path / 'chat.db-shm')], 
                                     check=False, capture_output=True)
                except:
                    pass  # xattr might not be available on all systems
                
                # Set proper permissions (readable by owner and group)
                os.chmod(dest_chat, 0o644)
                if (dest_path / 'chat.db-wal').exists():
                    os.chmod(dest_path / 'chat.db-wal', 0o644)
                if (dest_path / 'chat.db-shm').exists():
                    os.chmod(dest_path / 'chat.db-shm', 0o644)
                
                # DO NOT try to checkpoint or modify the database - it causes corruption
                # Just log that we've copied the files
                self.logger.log_event("database_copy", {
                    "action": "wal_files_copied",
                    "note": "Database kept in original state to avoid corruption"
                })
            else:
                # Try with sudo if direct access fails
                self._copy_with_sudo(self.config['source_chat_db'], str(dest_chat))
            
            # Find and copy AddressBook database
            ab_base = Path(self.config['source_addressbook'])
            ab_db_path = None
            
            # Search for the .abcddb file
            for source_dir in ab_base.glob('Sources/*'):
                for abcddb in source_dir.glob('*.abcddb'):
                    ab_db_path = abcddb
                    break
                if ab_db_path:
                    break
            
            if not ab_db_path:
                raise FileNotFoundError("Could not find AddressBook database")
            
            # Copy AddressBook
            if ab_db_path.exists():
                shutil.copy2(ab_db_path, dest_ab)
                # Remove extended attributes
                try:
                    subprocess.run(['xattr', '-c', str(dest_ab)], 
                                 check=False, capture_output=True)
                except:
                    pass
                os.chmod(dest_ab, 0o644)  # More permissive for reading
            else:
                self._copy_with_sudo(str(ab_db_path), str(dest_ab))
            
            self.logger.log_event("database_copy", {
                "action": "completed",
                "status": "success"
            })
            
            return str(dest_chat), str(dest_ab)
            
        except Exception as e:
            self.logger.log_event("database_copy", {
                "action": "failed",
                "error": str(e)
            }, level="error")
            raise
    
    def _copy_with_sudo(self, source: str, dest: str):
        """
        Copy file using sudo (fallback for permission issues)
        
        Args:
            source: Source file path
            dest: Destination file path
        """
        print(f"Need elevated permissions to copy {source}")
        username = input("Enter username for sudo: ")
        password = getpass.getpass(f"Enter password for {username}: ")
        
        # Use subprocess with sudo
        cmd = ["sudo", "-S", "-u", username, "cp", source, dest]
        proc = subprocess.run(
            cmd,
            input=password + "\n",
            text=True,
            capture_output=True
        )
        
        if proc.returncode != 0:
            raise RuntimeError(f"Failed to copy {source}: {proc.stderr.strip()}")
        
        # Set secure permissions
        os.chmod(dest, 0o640)
    
    def get_chat_mapping(self, db_path: str) -> Dict[str, str]:
        """
        Get mapping of room names to display names for group chats
        
        Args:
            db_path: Path to chat.db
            
        Returns:
            Dictionary mapping room_name to display_name
        """
        # Check if database is accessible (combines existence and readability)
        if not os.access(db_path, os.R_OK):
            self.logger.log_event("database_info", {
                "action": "get_chat_mapping",
                "note": f"Database not accessible: {db_path}"
            })
            return {}
        
        try:
            # Use context manager for automatic connection cleanup
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Efficient check for table existence using PRAGMA
                cursor.execute("PRAGMA table_info(chat)")
                if not cursor.fetchall():
                    self.logger.log_event("database_info", {
                        "action": "get_chat_mapping",
                        "note": "No group chats found (chat table does not exist)"
                    })
                    return {}
                
                # Get chat mappings with explicit NULL handling
                cursor.execute("""
                    SELECT room_name, display_name 
                    FROM chat 
                    WHERE room_name IS NOT NULL 
                    AND room_name != ''
                """)
                rows = cursor.fetchall()
                
                # Create mapping with explicit filtering
                # Only exclude NULL values, keep empty strings if they exist
                mapping = {}
                for room_name, display_name in rows:
                    if room_name is not None:  # Explicit None check
                        mapping[room_name] = display_name
                
                self.logger.log_event("database_info", {
                    "action": "get_chat_mapping",
                    "group_chats_found": len(mapping)
                })
                
                return mapping
                
        except sqlite3.Error as e:
            self.logger.log_event("database_warning", {
                "action": "get_chat_mapping",
                "error": f"SQLite error: {str(e)}"
            })
            return {}
        except Exception as e:
            self.logger.log_event("database_error", {
                "action": "get_chat_mapping",
                "error": f"Unexpected error: {str(e)}"
            }, level="error")
            return {}
    
    def extract_messages(self, db_path: str, limit: Optional[int] = None) -> List[MessageRecord]:
        """
        Extract messages from chat.db
        
        Args:
            db_path: Path to chat.db
            limit: Maximum number of messages to extract
            
        Returns:
            List of MessageRecord objects
        """
        # Connect to database - try read-only first, then regular
        try:
            # Try read-only connection (safer for WAL databases)
            conn_string = f"file:{db_path}?mode=ro"
            conn = sqlite3.connect(conn_string, uri=True, check_same_thread=False)
            self.logger.log_event("database_connection", {
                "mode": "read-only URI",
                "path": db_path
            })
        except (sqlite3.OperationalError, sqlite3.NotSupportedError):
            # Fallback to regular connection
            try:
                conn = sqlite3.connect(db_path, check_same_thread=False)
                self.logger.log_event("database_connection", {
                    "mode": "regular",
                    "path": db_path
                })
            except sqlite3.DatabaseError as e:
                # If database is corrupted, try to work around it
                self.logger.log_event("database_connection", {
                    "mode": "failed",
                    "error": str(e)
                }, level="error")
                raise RuntimeError(f"Cannot open database: {e}")
        
        cursor = conn.cursor()
        
        # Force SQLite to use memory for temp storage (fixes JOIN issues)
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        try:
            # Check for and detach any attached databases that might cause issues
            try:
                cursor.execute("PRAGMA database_list")
                databases = cursor.fetchall()
                for db in databases:
                    if db[1] != 'main' and db[1] != 'temp':
                        try:
                            cursor.execute(f"DETACH DATABASE '{db[1]}'")
                            self.logger.log_event("database_detach", {
                                "database": db[1],
                                "status": "detached"
                            })
                        except:
                            pass  # Ignore if can't detach
            except:
                pass  # Ignore if can't list databases
            
            # Get chat mapping for group names
            chat_mapping = self.get_chat_mapping(db_path)
            
            # Build query - use simpler query if the full one fails
            query = """
            SELECT message.ROWID, message.date, message.text, message.attributedBody,
                   handle.id, message.is_from_me, message.cache_roomnames
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            ORDER BY message.date DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            messages = []
            
            try:
                cursor.execute(query)
            except sqlite3.OperationalError as e:
                # If the query fails, try a simpler version without the JOIN
                self.logger.log_event("query_fallback", {
                    "error": str(e),
                    "action": "trying simpler query"
                }, level="warning")
                
                query = """
                SELECT ROWID, date, text, attributedBody,
                       NULL as handle_id, is_from_me, cache_roomnames
                FROM message
                ORDER BY date DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                cursor.execute(query)
            
            # Process in batches
            batch_size = self.config.get('batch_size', 1000)
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    msg = self._process_message_row(row, chat_mapping)
                    if msg:
                        messages.append(msg)
                
                self.logger.log_event("message_extraction", {
                    "processed": len(messages),
                    "batch_size": batch_size
                })
            
            return messages
            
        except Exception as e:
            self.logger.log_event("message_extraction_error", {
                "error": str(e),
                "db_path": db_path
            }, level="error")
            raise
        finally:
            conn.close()
    
    def _process_message_row(self, row: tuple, chat_mapping: Dict[str, str]) -> Optional[MessageRecord]:
        """
        Process a single message row from the database
        
        Args:
            row: Database row tuple
            chat_mapping: Mapping of room names to display names
            
        Returns:
            MessageRecord or None if message should be skipped
        """
        rowid, date, text, attributed_body, handle_id, is_from_me, cache_roomnames = row
        
        # Extract message body
        if text:
            body = text
        elif attributed_body:
            try:
                # Handle attributed body (NSAttributedString)
                body = attributed_body.decode('utf-8', 'ignore')
                # Clean up attributed string artifacts
                body = re.sub(r'\s+', ' ', body)
            except:
                body = ""
        else:
            return None  # Skip empty messages
        
        # Clean phone number
        phone = handle_id or ""
        if phone.startswith('tel:'):
            phone = phone[4:]
        phone = self._normalize_phone_number(phone)
        
        # Get group chat name if applicable
        group_name = None
        if cache_roomnames:
            group_name = chat_mapping.get(cache_roomnames)
        
        # Convert date (macOS stores as nanoseconds since 2001-01-01)
        if date:
            # Convert from Mac absolute time to Unix timestamp
            mac_epoch = datetime.datetime(2001, 1, 1)
            timestamp = mac_epoch + datetime.timedelta(seconds=date/1_000_000_000)
            date_str = timestamp.isoformat() if self.config.get('human_readable_dates', True) else str(date)
        else:
            date_str = ""
        
        # Create message record
        msg = MessageRecord(
            rowid=rowid,
            date=date_str,
            body=body,
            phone_number=phone,
            is_from_me=bool(is_from_me),
            cache_roomname=cache_roomnames,
            group_chat_name=group_name
        )
        
        # Anonymize phone if configured
        if self.config.get('anonymize_phones', True) and phone:
            msg.phone_hash = hashlib.sha256(phone.encode()).hexdigest()[:12]
            msg.phone_number = f"PHONE_{msg.phone_hash}"
        
        return msg
    
    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number to consistent format
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Normalized phone number
        """
        if not phone:
            return ""
        
        # Remove common prefixes
        phone = phone.replace('tel:', '')
        phone = phone.replace('sms:', '')
        
        # Remove non-digits except + at start
        if phone.startswith('+'):
            phone = '+' + re.sub(r'\D', '', phone[1:])
        else:
            phone = re.sub(r'\D', '', phone)
        
        # Add US country code if needed
        if len(phone) == 10:
            phone = '+1' + phone
        elif len(phone) == 11 and phone.startswith('1'):
            phone = '+' + phone
        
        return phone
    
    def extract_contacts(self, addressbook_path: str) -> List[Contact]:
        """
        Extract contacts from AddressBook database
        
        Args:
            addressbook_path: Path to AddressBook .abcddb file
            
        Returns:
            List of Contact objects
        """
        conn = sqlite3.connect(addressbook_path)
        cursor = conn.cursor()
        
        # Force SQLite to use memory for temp storage (fixes JOIN issues)
        cursor.execute("PRAGMA temp_store = MEMORY")
        
        try:
            query = """
            SELECT 
                ZABCDRECORD.ZFIRSTNAME as first,
                ZABCDRECORD.ZLASTNAME as last,
                ZABCDPHONENUMBER.ZFULLNUMBER as full
            FROM ZABCDRECORD
            LEFT JOIN ZABCDPHONENUMBER ON ZABCDRECORD.Z_PK = ZABCDPHONENUMBER.ZOWNER
            WHERE ZABCDPHONENUMBER.ZFULLNUMBER IS NOT NULL
            """
            
            cursor.execute(query)
            contacts = []
            
            for row in cursor.fetchall():
                first, last, full = row
                
                # Clean up phone number
                if not full:
                    continue
                    
                # Extract just digits for comparison
                digits = re.sub(r'\D', '', full)
                
                # Format for matching
                if len(digits) == 10:
                    clean = f"+1{digits}"
                elif len(digits) == 11 and digits.startswith('1'):
                    clean = f"+{digits}"
                else:
                    clean = full  # Keep original if format unclear
                
                contacts.append(Contact(
                    first_name=first,
                    last_name=last,
                    full_number=full,
                    clean_number=clean
                ))
            
            return contacts
            
        finally:
            conn.close()
    
    def enrich_messages_with_contacts(self, messages: List[MessageRecord], 
                                     contacts: List[Contact]) -> List[MessageRecord]:
        """
        Enrich messages with contact names
        
        Args:
            messages: List of message records
            contacts: List of contact records
            
        Returns:
            Enriched message records
        """
        # Create lookup dictionary for faster matching
        contact_lookup = {c.clean_number: c for c in contacts}
        
        for message in messages:
            if message.phone_number in contact_lookup:
                contact = contact_lookup[message.phone_number]
                message.first_name = contact.first_name
                message.last_name = contact.last_name
            # Also try without country code
            elif message.phone_number.startswith('+1'):
                phone_without_code = message.phone_number[2:]
                if phone_without_code in contact_lookup:
                    contact = contact_lookup[phone_without_code]
                    message.first_name = contact.first_name
                    message.last_name = contact.last_name
        
        return messages
    
    def export_to_json(self, messages: List[MessageRecord], output_path: str):
        """
        Export messages to JSON file
        Handles network volumes by using local storage if needed
        
        Args:
            messages: List of message records
            output_path: Path to output JSON file
        """
        # Convert to dictionaries
        message_dicts = [asdict(msg) for msg in messages]
        
        # Check if output path is on network volume
        output_file = Path(output_path)
        storage_manager = LocalStorageManager(auto_cleanup=False)
        
        if storage_manager.is_network_volume(output_file):
            # Write to local storage first
            local_temp = storage_manager.local_temp_base / 'exports'
            local_temp.mkdir(parents=True, exist_ok=True, mode=0o750)
            local_file = local_temp / output_file.name
            
            self.logger.log_event("export", {
                "type": "network_volume_detected",
                "using_local": str(local_file)
            })
            
            # Write to local file
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(message_dicts, f, indent=2, ensure_ascii=False)
            os.chmod(local_file, 0o640)
            
            # Sync back to network
            output_file.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
            storage_manager.sync_back_to_network(local_file, output_file)
            
            # Clean up local file
            storage_manager.cleanup()
            
            self.logger.log_event("export", {
                "file": str(output_file),
                "message_count": len(messages),
                "synced_from_local": True
            })
        else:
            # Direct write to local storage
            output_file.parent.mkdir(parents=True, exist_ok=True, mode=0o750)
            
            # Write JSON with secure permissions
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(message_dicts, f, indent=2, ensure_ascii=False)
            
            # Set secure file permissions
            os.chmod(output_file, 0o640)
            
            self.logger.log_event("export", {
                "file": str(output_file),
                "message_count": len(messages),
                "size_bytes": output_file.stat().st_size
            })
    
    def run_extraction_pipeline(self, message_limit: Optional[int] = None) -> str:
        """
        Run the complete extraction pipeline
        
        Args:
            message_limit: Maximum number of messages to extract (None = all)
            
        Returns:
            Path to output JSON file
        """
        self.logger.log_event("pipeline", {"status": "starting", "limit": message_limit})
        
        try:
            # Step 1: Copy databases
            chat_db, addressbook_db = self.copy_databases_secure()
            
            # Step 2: Extract messages
            messages = self.extract_messages(
                chat_db, 
                limit=message_limit or self.config.get('message_limit')
            )
            self.logger.log_event("pipeline", {
                "stage": "message_extraction",
                "count": len(messages)
            })
            
            # Step 3: Extract contacts
            contacts = self.extract_contacts(addressbook_db)
            self.logger.log_event("pipeline", {
                "stage": "contact_extraction",
                "count": len(contacts)
            })
            
            # Step 4: Enrich messages with contact names
            enriched_messages = self.enrich_messages_with_contacts(messages, contacts)
            
            # Step 5: Export to JSON
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(self.config['output_dir']) / f"imessage_export_{timestamp}.json"
            self.export_to_json(enriched_messages, str(output_file))
            
            # Clean up temporary files (optional)
            if self.config.get('cleanup_temp', True):
                try:
                    os.remove(chat_db)
                    os.remove(addressbook_db)
                    # Also clean up any WAL/SHM files
                    for ext in ['-wal', '-shm']:
                        wal_file = Path(chat_db).parent / f"chat.db{ext}"
                        if wal_file.exists():
                            os.remove(wal_file)
                except Exception as e:
                    self.logger.log_event("cleanup", {"error": str(e)}, level="warning")
                
                # Clean up storage manager if it was used
                if hasattr(self, '_storage_manager') and self._storage_manager:
                    self.logger.log_event("cleanup", {"action": "cleaning_local_storage"})
                    self._storage_manager.cleanup(force=True)
            
            self.logger.log_event("pipeline", {
                "status": "completed",
                "output": str(output_file),
                "messages_processed": len(enriched_messages)
            })
            
            print(f"✅ Extraction complete!")
            print(f"📊 Processed {len(enriched_messages)} messages")
            print(f"💾 Output saved to: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.log_event("pipeline", {
                "status": "failed",
                "error": str(e)
            }, level="error")
            raise


def main():
    """Command-line interface for iMessage extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract iMessage data for Avatar-Engine processing"
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        help='Maximum number of messages to extract'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/extracted',
        help='Output directory for JSON export'
    )
    parser.add_argument(
        '--no-anonymize',
        action='store_true',
        help='Disable phone number anonymization'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override with command-line arguments
    if args.output_dir:
        config['output_dir'] = args.output_dir
    if args.no_anonymize:
        config['anonymize_phones'] = False
    
    # Run extraction
    extractor = IMessageExtractor(config)
    output_file = extractor.run_extraction_pipeline(message_limit=args.limit)
    
    return output_file


if __name__ == "__main__":
    main()
