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
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import shutil
import subprocess
import getpass

from security_utils import SecurityManager, SecureLogger, InputValidator

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
        self.config = config or self._get_default_config()
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
        }
    
    def _validate_config(self):
        """Validate configuration paths and settings"""
        # Validate paths don't contain directory traversal
        for key in ['source_chat_db', 'source_addressbook', 'output_dir', 'temp_dir']:
            if key in self.config and self.config[key]:
                self.input_validator.validate_file_path(str(self.config[key]))
        
        # Create output directories if they don't exist
        for dir_key in ['output_dir', 'temp_dir']:
            dir_path = Path(self.config[dir_key])
            dir_path.mkdir(parents=True, exist_ok=True, mode=0o750)
    
    def copy_databases_secure(self, dest_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Securely copy chat.db and AddressBook database to working directory
        
        Args:
            dest_dir: Destination directory (uses temp_dir from config if None)
            
        Returns:
            Tuple of (chat_db_path, addressbook_db_path)
        """
        dest_dir = dest_dir or self.config['temp_dir']
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True, mode=0o750)
        
        # Destination paths
        dest_chat = dest_path / 'chat.db'
        dest_ab = dest_path / 'AddressBook-v22.abcddb'
        
        self.logger.log_event("database_copy", {
            "action": "starting",
            "dest_chat": str(dest_chat),
            "dest_addressbook": str(dest_ab)
        })
        
        try:
            # Find the AddressBook database
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
            
            # Copy chat.db
            if Path(self.config['source_chat_db']).exists():
                shutil.copy2(self.config['source_chat_db'], dest_chat)
                os.chmod(dest_chat, 0o640)  # Secure permissions
            else:
                # Try with sudo if direct access fails
                self._copy_with_sudo(self.config['source_chat_db'], str(dest_chat))
            
            # Copy AddressBook
            if ab_db_path.exists():
                shutil.copy2(ab_db_path, dest_ab)
                os.chmod(dest_ab, 0o640)  # Secure permissions
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT room_name, display_name FROM chat")
            rows = cursor.fetchall()
            return {room_name: display_name for room_name, display_name in rows if room_name}
        finally:
            conn.close()
    
    def extract_messages(self, db_path: str, limit: Optional[int] = None) -> List[MessageRecord]:
        """
        Extract messages from chat.db
        
        Args:
            db_path: Path to chat.db
            limit: Maximum number of messages to extract
            
        Returns:
            List of MessageRecord objects
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get chat mapping for group names
            chat_mapping = self.get_chat_mapping(db_path)
            
            # Build query
            query = """
            SELECT message.ROWID, message.date, message.text, message.attributedBody,
                   handle.id, message.is_from_me, message.cache_roomnames
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            ORDER BY message.date DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            messages = []
            
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
            
        finally:
            conn.close()
    
    def _process_message_row(self, row: tuple, chat_mapping: Dict[str, str]) -> Optional[MessageRecord]:
        """
        Process a single message row from the database
        
        Args:
            row: Database row tuple
            chat_mapping: Group chat name mapping
            
        Returns:
            MessageRecord or None if message should be skipped
        """
        rowid, date, text, attributed_body, handle_id, is_from_me, cache_roomname = row
        
        # Determine sender
        phone_number = 'Me' if (is_from_me or handle_id is None) else handle_id
        
        # Extract message body
        if text:
            body = text
        elif attributed_body:
            # Handle attributed body (rich text)
            body = self._extract_attributed_body(attributed_body)
            if not body:
                return None
        else:
            return None  # Skip empty messages
        
        # Convert date if needed
        if self.config.get('human_readable_dates', True):
            date_str = self._convert_apple_date(date)
        else:
            date_str = str(date)
        
        # Anonymize phone number if configured
        phone_hash = None
        if self.config.get('anonymize_phones', True) and phone_number != 'Me':
            phone_hash = self.security_manager.hash_pii(phone_number)
            # Keep area code for context
            if phone_number.startswith('+1') and len(phone_number) >= 7:
                phone_number = f"{phone_number[:5]}****{phone_hash[:4]}"
            else:
                phone_number = f"user_{phone_hash[:8]}"
        
        return MessageRecord(
            rowid=rowid,
            date=date_str,
            body=body,
            phone_number=phone_number,
            is_from_me=bool(is_from_me),
            cache_roomname=cache_roomname,
            group_chat_name=chat_mapping.get(cache_roomname) if cache_roomname else None,
            phone_hash=phone_hash
        )
    
    def _extract_attributed_body(self, attributed_body: bytes) -> Optional[str]:
        """
        Extract text from attributed body (rich text messages)
        
        Args:
            attributed_body: Raw attributed body bytes
            
        Returns:
            Extracted text or None
        """
        try:
            decoded = attributed_body.decode('utf-8', errors='replace')
            
            # Look for NSString marker
            if "NSString" in decoded:
                # Extract text between NSString and closing brace
                parts = decoded.split("NSString")
                if len(parts) > 1:
                    text = parts[1].split("}")[0]
                    # Clean up the text
                    text = text.strip()
                    if text:
                        return text
            
            # Fallback: return decoded if it seems like readable text
            if decoded and not decoded.startswith('bplist'):
                return decoded
                
        except Exception as e:
            self.logger.log_event("attributed_body_extraction", {
                "error": str(e)
            }, level="warning")
        
        return None
    
    def _convert_apple_date(self, apple_timestamp: int) -> str:
        """
        Convert Apple timestamp to human-readable format
        
        Args:
            apple_timestamp: Timestamp in Apple format (nanoseconds since 2001-01-01)
            
        Returns:
            ISO format date string
        """
        # Apple epoch starts at 2001-01-01
        apple_epoch = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)
        
        # Convert nanoseconds to seconds
        seconds = apple_timestamp / 1_000_000_000
        
        # Calculate actual timestamp
        timestamp = apple_epoch + datetime.timedelta(seconds=seconds)
        
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def extract_contacts(self, addressbook_path: str) -> List[Contact]:
        """
        Extract contacts from AddressBook database
        
        Args:
            addressbook_path: Path to AddressBook database
            
        Returns:
            List of Contact objects
        """
        conn = sqlite3.connect(addressbook_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT
                    ZABCDRECORD.ZFIRSTNAME,
                    ZABCDRECORD.ZLASTNAME,
                    ZABCDPHONENUMBER.ZFULLNUMBER
                FROM ZABCDRECORD
                LEFT JOIN ZABCDPHONENUMBER
                    ON ZABCDRECORD.Z_PK = ZABCDPHONENUMBER.ZOWNER
                ORDER BY ZABCDRECORD.ZLASTNAME,
                         ZABCDRECORD.ZFIRSTNAME,
                         ZABCDPHONENUMBER.ZORDERINGINDEX ASC
            """)
            
            contacts = []
            for first, last, full in cursor.fetchall():
                if not full:
                    continue
                
                # Clean phone number
                digits = "".join(c for c in full if c.isdigit())
                
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
        
        Args:
            messages: List of message records
            output_path: Path to output JSON file
        """
        # Convert to dictionaries
        message_dicts = [asdict(msg) for msg in messages]
        
        # Ensure output directory exists
        output_file = Path(output_path)
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
                except Exception as e:
                    self.logger.log_event("cleanup", {"error": str(e)}, level="warning")
            
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
