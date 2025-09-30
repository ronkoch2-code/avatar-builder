#!/usr/bin/env python3
"""
Alternative: Read Contacts directly from SQLite database
This requires Full Disk Access but bypasses the Contacts API permission
Last Updated: September 29, 2025
"""

import os
import sqlite3
import platform
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console

console = Console()

# Possible locations of the Contacts database on macOS
CONTACTS_DB_PATHS = [
    Path.home() / "Library/Application Support/AddressBook/AddressBook-v22.abcddb",
    Path.home() / "Library/Application Support/AddressBook/Sources",
    # Older versions
    Path.home() / "Library/Application Support/AddressBook/AddressBook.abcddb",
]

def find_contacts_database():
    """Find the Contacts database file"""
    for base_path in CONTACTS_DB_PATHS:
        if base_path.exists():
            if base_path.is_dir():
                # Search for .abcddb files in Sources directory
                for db_file in base_path.glob("*/*.abcddb"):
                    return db_file
            else:
                return base_path
    return None

def read_contacts_sqlite():
    """Read contacts directly from SQLite database"""
    db_path = find_contacts_database()
    
    if not db_path:
        console.print("[red]❌ Could not find Contacts database[/red]")
        console.print("\nPossible reasons:")
        console.print("1. You may need Full Disk Access for Terminal")
        console.print("2. The database location may have changed in macOS 26")
        return []
    
    console.print(f"[green]✓[/green] Found Contacts database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        console.print(f"\nFound tables: {[t[0] for t in tables]}")
        
        # Common tables in Contacts database:
        # ZABCDRECORD - main contact records
        # ZABCDCONTACTINDEX - contact index
        # ZABCDPHONENUMBER - phone numbers
        # ZABCDEMAILADDRESS - email addresses
        
        # Try to read contact records
        contacts = []
        
        # Query for basic contact info (table names may vary)
        possible_queries = [
            "SELECT ZFIRSTNAME, ZLASTNAME, ZNICKNAME, ZORGANIZATION FROM ZABCDRECORD WHERE ZFIRSTNAME IS NOT NULL OR ZLASTNAME IS NOT NULL LIMIT 10",
            "SELECT ZFIRSTNAME, ZLASTNAME, ZMIDDLENAME, ZNOTE FROM ZABCDCONTACTINDEX LIMIT 10",
            "SELECT * FROM ZABCDRECORD LIMIT 10"
        ]
        
        for query in possible_queries:
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                if results:
                    console.print(f"\n[green]✓[/green] Query successful: {query[:50]}...")
                    console.print(f"Found {len(results)} records")
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Convert to dictionaries
                    for row in results:
                        contact = dict(zip(columns, row))
                        contacts.append(contact)
                        
                        # Look for nickname fields
                        nickname_fields = ['ZNICKNAME', 'ZMAIDENNAME', 'ZPHONETICFIRSTNAME']
                        for field in nickname_fields:
                            if field in contact and contact[field]:
                                console.print(f"  Found nickname: {contact[field]}")
                    
                    break
            except sqlite3.Error as e:
                console.print(f"[yellow]Query failed: {e}[/yellow]")
                continue
        
        conn.close()
        return contacts
        
    except sqlite3.Error as e:
        console.print(f"[red]❌ Database error: {e}[/red]")
        console.print("\nYou may need to grant Full Disk Access to Terminal:")
        console.print("1. System Settings > Privacy & Security > Full Disk Access")
        console.print("2. Add Terminal (or your IDE)")
        console.print("3. Restart Terminal and try again")
        return []
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        return []

def main():
    console.print("[bold cyan]Avatar-Engine: Direct SQLite Contacts Access[/bold cyan]")
    console.print("Attempting to read Contacts database directly...")
    console.print()
    
    if platform.system() != 'Darwin':
        console.print("[red]This script only works on macOS[/red]")
        return
    
    contacts = read_contacts_sqlite()
    
    if contacts:
        console.print(f"\n[green]Successfully read {len(contacts)} contacts![/green]")
        console.print("\nSample contacts (first 3):")
        for i, contact in enumerate(contacts[:3]):
            console.print(f"\n{i+1}. {contact}")
    else:
        console.print("\n[yellow]Could not read contacts[/yellow]")
        console.print("\nAlternative approaches:")
        console.print("1. Use the AppleScript approach: osascript request_contacts_applescript.scpt")
        console.print("2. Try the app bundle approach: python3 create_app_bundle_for_permission.py")
        console.print("3. Use mock data for testing: python3 test_mock_nicknames.py")

if __name__ == "__main__":
    main()
