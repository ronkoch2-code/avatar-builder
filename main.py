#!/usr/bin/env python3
"""
Avatar-Engine Main CLI
Nickname extraction and management system
Last Updated: September 29, 2025
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.graph_models import Person, Nickname, NicknameSource
from extractors.address_book_extractor import AddressBookExtractor
from extractors.nickname_inference import NicknameInferenceEngine
from database.graph_builder import GraphBuilder

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Avatar-Engine: Advanced nickname extraction and management"""
    if debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file for extracted data')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Output format')
@click.option('--mock', is_flag=True, help='Use mock data instead of real contacts')
@click.pass_context
def extract_contacts(ctx, output, format, mock):
    """Extract contacts and nicknames from macOS Address Book"""
    if mock:
        console.print("[bold yellow]Using mock data for testing[/bold yellow]")
    console.print("[bold cyan]Extracting contacts from Address Book...[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Extracting contacts...", total=None)
        
        try:
            # Initialize extractor
            extractor = AddressBookExtractor(mock_mode=mock)
            
            # Extract contacts
            persons = extractor.extract_all_contacts()
            
            progress.update(task, completed=True)
            
            console.print(f"[green]✓[/green] Extracted {len(persons)} contacts")
            
            # Display summary
            total_nicknames = sum(len(p.nicknames) for p in persons)
            console.print(f"[green]✓[/green] Found {total_nicknames} total nicknames")
            
            # Save to file if requested
            if output:
                save_data(persons, output, format)
                console.print(f"[green]✓[/green] Saved to {output}")
            
            # Display sample
            if persons and not output:
                display_persons_table(persons[:5])
                if len(persons) > 5:
                    console.print(f"\n... and {len(persons) - 5} more contacts")
            
            return persons
            
        except Exception as e:
            logger.error(f"Failed to extract contacts: {e}")
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@cli.command()
@click.option('--neo4j-uri', envvar='NEO4J_URI', default='bolt://localhost:7687', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USERNAME', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
@click.option('--clear', is_flag=True, help='Clear existing graph before importing')
@click.pass_context
def import_to_graph(ctx, neo4j_uri, neo4j_user, neo4j_password, clear):
    """Import contacts and nicknames to Neo4j graph"""
    if not neo4j_password:
        neo4j_password = click.prompt('Neo4j password', hide_input=True)
    
    console.print("[bold cyan]Importing to Neo4j graph...[/bold cyan]")
    
    try:
        # Initialize graph builder
        graph = GraphBuilder(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        if clear:
            if click.confirm("This will delete all existing data. Continue?"):
                graph.clear_graph()
                console.print("[yellow]Graph cleared[/yellow]")
        
        # Extract contacts
        extractor = AddressBookExtractor()
        persons = extractor.extract_all_contacts()
        
        # Import to graph
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Importing {len(persons)} persons...", 
                total=len(persons)
            )
            
            for person in persons:
                graph.create_person(person)
                progress.update(task, advance=1)
        
        # Display statistics
        stats = graph.get_statistics()
        console.print(f"[green]✓[/green] Graph statistics:")
        console.print(f"  • Persons: {stats['persons']}")
        console.print(f"  • Nicknames: {stats['nicknames']}")
        console.print(f"  • Relationships: {stats['relationships']}")
        
        graph.close()
        
    except Exception as e:
        logger.error(f"Failed to import to graph: {e}")
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('messages_file', type=click.Path(exists=True))
@click.option('--neo4j-uri', envvar='NEO4J_URI', default='bolt://localhost:7687', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USERNAME', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
@click.pass_context
def analyze_conversation(ctx, messages_file, neo4j_uri, neo4j_user, neo4j_password):
    """Analyze conversation to infer nicknames"""
    if not neo4j_password:
        neo4j_password = click.prompt('Neo4j password', hide_input=True)
    
    console.print(f"[bold cyan]Analyzing conversation: {messages_file}[/bold cyan]")
    
    try:
        # Load messages
        with open(messages_file, 'r') as f:
            messages = json.load(f)
        
        console.print(f"Loaded {len(messages)} messages")
        
        # Initialize components
        graph = GraphBuilder(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        inference_engine = NicknameInferenceEngine()
        
        # Get known persons from graph
        stats = graph.get_statistics()
        known_persons = []  # Would need to implement a method to retrieve all persons
        
        # Analyze conversation
        inferred_nicknames = inference_engine.analyze_conversation(
            messages,
            known_persons
        )
        
        # Display results
        console.print(f"\n[green]✓[/green] Inferred nicknames:")
        for person_id, nicknames in inferred_nicknames.items():
            console.print(f"\n[bold]{person_id}:[/bold]")
            for nickname in nicknames:
                console.print(
                    f"  • {nickname.name} "
                    f"(confidence: {nickname.confidence:.2f}, "
                    f"source: {nickname.source.value})"
                )
        
        # Add to graph if confirmed
        if inferred_nicknames and click.confirm("\nAdd inferred nicknames to graph?"):
            for person_id, nicknames in inferred_nicknames.items():
                for nickname in nicknames:
                    graph.add_nickname_to_person(person_id, nickname)
            
            console.print("[green]✓[/green] Nicknames added to graph")
        
        graph.close()
        
    except Exception as e:
        logger.error(f"Failed to analyze conversation: {e}")
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('nickname')
@click.option('--neo4j-uri', envvar='NEO4J_URI', default='bolt://localhost:7687', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USERNAME', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
@click.pass_context
def find_person(ctx, nickname, neo4j_uri, neo4j_user, neo4j_password):
    """Find person by nickname"""
    if not neo4j_password:
        neo4j_password = click.prompt('Neo4j password', hide_input=True)
    
    try:
        graph = GraphBuilder(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        results = graph.find_person_by_nickname(nickname)
        
        if results:
            console.print(f"\n[green]Found {len(results)} person(s) with nickname '{nickname}':[/green]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Person", style="cyan")
            table.add_column("Confidence", justify="center")
            table.add_column("Source", style="yellow")
            
            for result in results:
                person = result['person']
                table.add_row(
                    person.get('full_name', 'Unknown'),
                    f"{result['confidence']:.2f}",
                    result['source']
                )
            
            console.print(table)
        else:
            console.print(f"[yellow]No person found with nickname '{nickname}'[/yellow]")
        
        graph.close()
        
    except Exception as e:
        logger.error(f"Failed to find person: {e}")
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--neo4j-uri', envvar='NEO4J_URI', default='bolt://localhost:7687', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USERNAME', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
@click.option('--format', '-f', type=click.Choice(['cypher', 'json']), default='json', help='Export format')
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file')
@click.pass_context
def export_graph(ctx, neo4j_uri, neo4j_user, neo4j_password, format, output):
    """Export graph data"""
    if not neo4j_password:
        neo4j_password = click.prompt('Neo4j password', hide_input=True)
    
    try:
        graph = GraphBuilder(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        console.print(f"[bold cyan]Exporting graph as {format}...[/bold cyan]")
        
        data = graph.export_graph(format=format)
        
        with open(output, 'w') as f:
            f.write(data)
        
        console.print(f"[green]✓[/green] Graph exported to {output}")
        
        graph.close()
        
    except Exception as e:
        logger.error(f"Failed to export graph: {e}")
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


def display_persons_table(persons: List[Person]):
    """Display persons in a table"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Nicknames", style="yellow")
    table.add_column("Email", style="green")
    table.add_column("Organization", style="blue")
    
    for person in persons:
        nicknames = ", ".join([n.name for n in person.nicknames[:3]])
        if len(person.nicknames) > 3:
            nicknames += f" (+{len(person.nicknames) - 3} more)"
        
        emails = ", ".join(person.email[:1]) if person.email else ""
        if len(person.email) > 1:
            emails += f" (+{len(person.email) - 1} more)"
        
        table.add_row(
            person.full_name,
            nicknames or "-",
            emails or "-",
            person.organization or "-"
        )
    
    console.print(table)


def save_data(persons: List[Person], output_path: str, format: str):
    """Save persons data to file"""
    if format == 'json':
        data = [
            {
                'full_name': p.full_name,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'nicknames': [
                    {
                        'name': n.name,
                        'source': n.source.value,
                        'confidence': n.confidence,
                        'type': n.nickname_type.value if n.nickname_type else None
                    } for n in p.nicknames
                ],
                'email': p.email,
                'phone': p.phone,
                'organization': p.organization
            } for p in persons
        ]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    elif format == 'csv':
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Full Name', 'First Name', 'Last Name', 
                'Primary Nickname', 'All Nicknames', 
                'Email', 'Organization'
            ])
            
            for p in persons:
                nicknames = "; ".join([n.name for n in p.nicknames])
                emails = "; ".join(p.email)
                
                writer.writerow([
                    p.full_name,
                    p.first_name or '',
                    p.last_name or '',
                    p.primary_nickname or '',
                    nicknames,
                    emails,
                    p.organization or ''
                ])


if __name__ == '__main__':
    cli()
