#!/usr/bin/env python3
"""
Test nickname extraction with mock data (no Contacts access required)
Last Updated: September 29, 2025
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime
from rich.console import Console
from rich.table import Table

from models.graph_models import Person, Nickname, NicknameSource, NicknameType

console = Console()

def create_mock_persons():
    """Create mock persons with various nickname types for testing"""
    persons = []
    
    # Person 1: Robert Smith with multiple nicknames
    person1 = Person(
        id="mock_001",
        full_name="Robert Smith",
        first_name="Robert",
        last_name="Smith",
        email=["robert.smith@example.com", "bob@work.com"],
        phone=["+1-555-0100"],
        organization="Tech Solutions Inc",
        job_title="Senior Developer"
    )
    
    person1.add_nickname(Nickname(
        name="Bob",
        source=NicknameSource.ADDRESS_BOOK,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=1.0,
        frequency=50
    ))
    
    person1.add_nickname(Nickname(
        name="Rob",
        source=NicknameSource.CONVERSATION,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=0.9,
        frequency=30
    ))
    
    person1.add_nickname(Nickname(
        name="Bobby",
        source=NicknameSource.INFERRED,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=0.7,
        frequency=10
    ))
    
    person1.add_nickname(Nickname(
        name="RS",
        source=NicknameSource.INFERRED,
        nickname_type=NicknameType.INITIALS,
        confidence=0.6,
        frequency=5
    ))
    
    persons.append(person1)
    
    # Person 2: Elizabeth Johnson
    person2 = Person(
        id="mock_002",
        full_name="Elizabeth Johnson",
        first_name="Elizabeth",
        last_name="Johnson",
        email=["liz@example.com"],
        phone=["+1-555-0101"],
        organization="Design Co",
        job_title="Creative Director"
    )
    
    person2.add_nickname(Nickname(
        name="Liz",
        source=NicknameSource.ADDRESS_BOOK,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=1.0,
        frequency=40
    ))
    
    person2.add_nickname(Nickname(
        name="Beth",
        source=NicknameSource.CONVERSATION,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=0.8,
        frequency=20
    ))
    
    person2.add_nickname(Nickname(
        name="Lizzie",
        source=NicknameSource.SELF_REFERENCE,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=0.95,
        frequency=15
    ))
    
    persons.append(person2)
    
    # Person 3: Michael Chen
    person3 = Person(
        id="mock_003",
        full_name="Michael Chen",
        first_name="Michael",
        last_name="Chen",
        middle_name="Wei",
        email=["mchen@university.edu"],
        phone=["+1-555-0102"],
        organization="State University",
        job_title="Professor"
    )
    
    person3.add_nickname(Nickname(
        name="Mike",
        source=NicknameSource.ADDRESS_BOOK,
        nickname_type=NicknameType.DIMINUTIVE,
        confidence=1.0,
        frequency=60
    ))
    
    person3.add_nickname(Nickname(
        name="Professor Chen",
        source=NicknameSource.CONVERSATION,
        nickname_type=NicknameType.PROFESSIONAL,
        confidence=0.9,
        frequency=25
    ))
    
    person3.add_nickname(Nickname(
        name="MWC",
        source=NicknameSource.INFERRED,
        nickname_type=NicknameType.INITIALS,
        confidence=0.5,
        frequency=3
    ))
    
    persons.append(person3)
    
    return persons


def display_persons_table(persons):
    """Display persons and their nicknames in a table"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Nicknames", style="yellow")
    table.add_column("Types", style="green")
    table.add_column("Email", style="blue")
    table.add_column("Organization", style="white")
    
    for person in persons:
        nicknames = []
        types = []
        for n in person.nicknames:
            nicknames.append(f"{n.name} ({n.confidence:.1f})")
            if n.nickname_type:
                types.append(n.nickname_type.value)
            else:
                types.append("unknown")
        
        nickname_str = "\n".join(nicknames) if nicknames else "-"
        type_str = "\n".join(types) if types else "-"
        
        emails = person.email[0] if person.email else "-"
        
        table.add_row(
            person.full_name,
            nickname_str,
            type_str,
            emails,
            person.organization or "-"
        )
    
    console.print(table)


def main():
    console.print("[bold cyan]Avatar-Engine: Mock Data Test[/bold cyan]")
    console.print("Testing nickname extraction without Contacts access")
    console.print()
    
    # Create mock data
    persons = create_mock_persons()
    
    console.print(f"[green]✓[/green] Created {len(persons)} mock persons")
    
    # Count nicknames
    total_nicknames = sum(len(p.nicknames) for p in persons)
    console.print(f"[green]✓[/green] Total nicknames: {total_nicknames}")
    
    # Display the data
    console.print("\n[bold]Mock Persons and Nicknames:[/bold]\n")
    display_persons_table(persons)
    
    # Show nickname statistics
    console.print("\n[bold]Nickname Statistics:[/bold]")
    
    source_counts = {}
    type_counts = {}
    
    for person in persons:
        for nickname in person.nicknames:
            source = nickname.source.value
            source_counts[source] = source_counts.get(source, 0) + 1
            
            if nickname.nickname_type:
                type_name = nickname.nickname_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
    
    console.print("\nBy Source:")
    for source, count in sorted(source_counts.items()):
        console.print(f"  • {source}: {count}")
    
    console.print("\nBy Type:")
    for type_name, count in sorted(type_counts.items()):
        console.print(f"  • {type_name}: {count}")
    
    console.print("\n[bold green]Mock data test complete![/bold green]")
    console.print("\nTo use real Contacts data:")
    console.print("1. Run: python3 request_contacts_permission.py")
    console.print("2. Grant permission when prompted")
    console.print("3. Run: python3 main.py extract-contacts")


if __name__ == "__main__":
    main()
