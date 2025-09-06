"""
Command Line Interface for Person Entity Deduplication.

This module provides a user-friendly CLI for running deduplication processes,
reviewing merge candidates, and managing the deduplication workflow.

Usage:
    python3 deduplication_cli.py run --interactive
    python3 deduplication_cli.py review --threshold 0.8
    python3 deduplication_cli.py stats
"""

import click
import sys
import json
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.prompt import Confirm, FloatPrompt
import questionary

from person_entity_deduplication import (
    PersonDeduplicationEngine, MergeCandidate, PersonEntity
)
from deduplication_config import get_config, DeduplicationConfig

# Initialize rich console for beautiful output
console = Console()


class DeduplicationCLI:
    """Command Line Interface for person entity deduplication."""
    
    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self.engine = None
        
    def initialize_engine(self):
        """Initialize the deduplication engine with current config."""
        if self.engine is None:
            db_config = self.config.get_database_config()
            self.engine = PersonDeduplicationEngine(
                db_config['uri'],
                db_config['user'], 
                db_config['password']
            )
    
    def run_deduplication(self, interactive: bool = True, auto_merge_threshold: float = None):
        """
        Run the complete deduplication process.
        
        Args:
            interactive: Whether to run in interactive mode
            auto_merge_threshold: Confidence threshold for automatic merging
        """
        console.print("\n[bold blue]🔍 Starting Person Entity Deduplication[/bold blue]\n")
        
        # Initialize engine
        self.initialize_engine()
        
        if auto_merge_threshold is None:
            auto_merge_threshold = self.config.AUTO_MERGE_THRESHOLD
        
        try:
            # Display configuration
            self._display_config_summary(auto_merge_threshold, interactive)
            
            # Run deduplication
            with Progress() as progress:
                task = progress.add_task("[green]Processing entities...", total=100)
                
                results = self.engine.run_deduplication(
                    auto_merge_threshold=auto_merge_threshold,
                    interactive_mode=interactive
                )
                
                progress.update(task, completed=100)
            
            # Display results
            self._display_results(results)
            
            # Handle manual review if needed
            if interactive and results.get('manual_review_candidates'):
                self._handle_manual_review(results['manual_review_candidates'])
                
        except Exception as e:
            console.print(f"[bold red]Error during deduplication: {str(e)}[/bold red]")
            sys.exit(1)
        finally:
            if self.engine:
                self.engine.close()
    
    def review_candidates(self, threshold: float = 0.6):
        """
        Review potential merge candidates without performing merges.
        
        Args:
            threshold: Minimum confidence threshold for candidates to review
        """
        console.print(f"\n[bold yellow]📋 Reviewing Merge Candidates (threshold: {threshold})[/bold yellow]\n")
        
        self.initialize_engine()
        
        try:
            # Get candidates
            candidates = self.engine.matcher.find_potential_duplicates()
            
            if not candidates:
                console.print("[green]✅ No duplicate candidates found![/green]")
                return
            
            # Filter by threshold
            filtered_candidates = [c for c in candidates if c.confidence_score >= threshold]
            
            if not filtered_candidates:
                console.print(f"[yellow]No candidates above threshold {threshold}[/yellow]")
                return
            
            # Display candidates in a table
            self._display_candidates_table(filtered_candidates)
            
            # Allow detailed review
            if questionary.confirm("Would you like to review candidates in detail?").ask():
                self._detailed_candidate_review(filtered_candidates)
                
        except Exception as e:
            console.print(f"[bold red]Error during review: {str(e)}[/bold red]")
            sys.exit(1)
        finally:
            if self.engine:
                self.engine.close()
    
    def show_statistics(self):
        """Display deduplication statistics and database info."""
        console.print("\n[bold green]📊 Deduplication Statistics[/bold green]\n")
        
        self.initialize_engine()
        
        try:
            with self.engine.driver.session() as session:
                # Get entity counts
                person_count = session.run("MATCH (p:Person) RETURN count(p) as count").single()["count"]
                mapping_count = session.run("MATCH (m:EntityMapping) RETURN count(m) as count").single()["count"]
                
                # Get recent merge statistics
                recent_merges = session.run("""
                    MATCH (m:EntityMapping)
                    WHERE m.merge_timestamp > datetime() - duration('P30D')
                    RETURN count(m) as recent_count
                """).single()["recent_count"]
                
                # Create statistics table
                stats_table = Table(title="Database Statistics")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="magenta")
                
                stats_table.add_row("Total Person Entities", str(person_count))
                stats_table.add_row("Total Merge Mappings", str(mapping_count))
                stats_table.add_row("Recent Merges (30 days)", str(recent_merges))
                
                console.print(stats_table)
                
                # Configuration info
                config_panel = Panel(
                    f"Environment: {self.config.__class__.__name__}\n"
                    f"Auto-merge threshold: {self.config.AUTO_MERGE_THRESHOLD}\n"
                    f"Name similarity threshold: {self.config.NAME_SIMILARITY_THRESHOLD}\n"
                    f"Interactive mode: {self.config.INTERACTIVE_MODE}",
                    title="Current Configuration",
                    border_style="blue"
                )
                console.print("\n", config_panel)
                
        except Exception as e:
            console.print(f"[bold red]Error retrieving statistics: {str(e)}[/bold red]")
            sys.exit(1)
        finally:
            if self.engine:
                self.engine.close()
    
    def lookup_mapping(self, original_id: str):
        """Look up canonical entity ID for an original entity ID."""
        console.print(f"\n[bold blue]🔍 Looking up mapping for: {original_id}[/bold blue]\n")
        
        self.initialize_engine()
        
        try:
            canonical_id = self.engine.get_mapping_by_original_id(original_id)
            
            if canonical_id:
                console.print(f"[green]✅ Found mapping:[/green]")
                console.print(f"   Original ID: {original_id}")
                console.print(f"   Canonical ID: {canonical_id}")
            else:
                console.print(f"[yellow]⚠️  No mapping found for: {original_id}[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]Error during lookup: {str(e)}[/bold red]")
            sys.exit(1)
        finally:
            if self.engine:
                self.engine.close()
    
    def _display_config_summary(self, auto_merge_threshold: float, interactive: bool):
        """Display configuration summary before processing."""
        config_info = f"""
        Auto-merge threshold: {auto_merge_threshold}
        Interactive mode: {interactive}
        Name similarity threshold: {self.config.NAME_SIMILARITY_THRESHOLD}
        Database: {self.config.NEO4J_URI}
        """
        
        panel = Panel(config_info.strip(), title="Configuration", border_style="green")
        console.print(panel)
    
    def _display_results(self, results: Dict):
        """Display deduplication results in a formatted way."""
        status = results.get('status', 'unknown')
        candidates_found = results.get('candidates_found', 0)
        auto_merges = results.get('auto_merges', 0)
        manual_review_count = results.get('manual_review_count', 0)
        
        # Create results table
        results_table = Table(title="Deduplication Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", style="magenta")
        
        results_table.add_row("Status", status.title())
        results_table.add_row("Candidates Found", str(candidates_found))
        results_table.add_row("Auto-merged", str(auto_merges))
        results_table.add_row("Manual Review Required", str(manual_review_count))
        
        console.print("\n", results_table)
        
        # Success message
        if auto_merges > 0:
            console.print(f"\n[bold green]✅ Successfully merged {auto_merges} duplicate entities![/bold green]")
        
        if manual_review_count > 0:
            console.print(f"\n[bold yellow]⚠️  {manual_review_count} candidates require manual review[/bold yellow]")
    
    def _display_candidates_table(self, candidates: List[MergeCandidate]):
        """Display candidates in a formatted table."""
        table = Table(title="Merge Candidates")
        table.add_column("ID", style="dim")
        table.add_column("Entity 1", style="cyan")
        table.add_column("Entity 2", style="cyan")
        table.add_column("Confidence", style="magenta")
        table.add_column("Match Reasons", style="green")
        
        for i, candidate in enumerate(candidates[:20]):  # Limit to first 20
            confidence_str = f"{candidate.confidence_score:.2f}"
            reasons_str = ", ".join(candidate.match_reasons[:2])  # Show first 2 reasons
            
            table.add_row(
                str(i + 1),
                candidate.entity1.name[:30] + "..." if len(candidate.entity1.name) > 30 else candidate.entity1.name,
                candidate.entity2.name[:30] + "..." if len(candidate.entity2.name) > 30 else candidate.entity2.name,
                confidence_str,
                reasons_str
            )
        
        console.print(table)
        
        if len(candidates) > 20:
            console.print(f"\n[dim]... and {len(candidates) - 20} more candidates[/dim]")
    
    def _detailed_candidate_review(self, candidates: List[MergeCandidate]):
        """Allow detailed review of individual candidates."""
        for i, candidate in enumerate(candidates):
            console.print(f"\n[bold]Candidate {i + 1}/{len(candidates)}[/bold]")
            
            # Display detailed candidate info
            self._display_candidate_details(candidate)
            
            # Ask for user decision
            choice = questionary.select(
                "What would you like to do with this candidate?",
                choices=[
                    "Merge these entities",
                    "Skip this candidate", 
                    "Stop reviewing",
                    "Show more details"
                ]
            ).ask()
            
            if choice == "Merge these entities":
                try:
                    canonical_id = self.engine.merger.merge_entities(candidate)
                    console.print(f"[green]✅ Merged successfully! Canonical ID: {canonical_id}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Merge failed: {str(e)}[/red]")
            elif choice == "Stop reviewing":
                break
            elif choice == "Show more details":
                self._display_extended_candidate_details(candidate)
                i -= 1  # Re-review this candidate
    
    def _display_candidate_details(self, candidate: MergeCandidate):
        """Display detailed information about a merge candidate."""
        entity1, entity2 = candidate.entity1, candidate.entity2
        
        details_table = Table()
        details_table.add_column("Property", style="cyan")
        details_table.add_column("Entity 1", style="magenta")
        details_table.add_column("Entity 2", style="yellow")
        
        details_table.add_row("ID", entity1.node_id, entity2.node_id)
        details_table.add_row("Name", entity1.name, entity2.name)
        details_table.add_row("Email", entity1.email or "N/A", entity2.email or "N/A")
        details_table.add_row("Properties", str(len(entity1.properties)), str(len(entity2.properties)))
        details_table.add_row("Relationships", str(len(entity1.relationships)), str(len(entity2.relationships)))
        
        console.print(details_table)
        
        # Show confidence and match reasons
        console.print(f"\n[bold]Confidence Score:[/bold] {candidate.confidence_score:.2f}")
        console.print(f"[bold]Match Reasons:[/bold] {', '.join(candidate.match_reasons)}")
    
    def _display_extended_candidate_details(self, candidate: MergeCandidate):
        """Display extended details including all properties."""
        console.print(f"\n[bold]Extended Details for Merge Candidate[/bold]\n")
        
        # Entity 1 details
        console.print("[bold cyan]Entity 1:[/bold cyan]")
        console.print(f"  ID: {candidate.entity1.node_id}")
        console.print(f"  Name: {candidate.entity1.name}")
        console.print(f"  Email: {candidate.entity1.email}")
        console.print(f"  Properties: {json.dumps(candidate.entity1.properties, indent=2)}")
        console.print(f"  Relationships: {list(candidate.entity1.relationships)}")
        
        console.print("\n[bold yellow]Entity 2:[/bold yellow]")
        console.print(f"  ID: {candidate.entity2.node_id}")
        console.print(f"  Name: {candidate.entity2.name}")
        console.print(f"  Email: {candidate.entity2.email}")
        console.print(f"  Properties: {json.dumps(candidate.entity2.properties, indent=2)}")
        console.print(f"  Relationships: {list(candidate.entity2.relationships)}")
        
        console.print(f"\n[bold green]Match Analysis:[/bold green]")
        console.print(f"  Confidence: {candidate.confidence_score:.3f}")
        console.print(f"  Reasons: {candidate.match_reasons}")
    
    def _handle_manual_review(self, candidates: List[MergeCandidate]):
        """Handle manual review of candidates that require user input."""
        if not questionary.confirm(f"Review {len(candidates)} manual candidates now?").ask():
            console.print("[yellow]Manual review skipped. Run 'review' command later.[/yellow]")
            return
        
        self._detailed_candidate_review(candidates)


# CLI Command Groups
@click.group()
@click.option('--env', default='development', help='Environment (development/production/testing)')
@click.option('--config-file', help='Custom configuration file path')
@click.pass_context
def cli(ctx, env, config_file):
    """Person Entity Deduplication CLI Tool."""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config_file:
        # In a real implementation, you'd load custom config from file
        config = get_config(env)
    else:
        config = get_config(env)
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        console.print("[bold red]Configuration Issues Found:[/bold red]")
        for issue in issues:
            console.print(f"  • {issue}")
        sys.exit(1)
    
    ctx.obj['config'] = config
    ctx.obj['cli'] = DeduplicationCLI(config)


@cli.command()
@click.option('--interactive/--no-interactive', default=True, help='Run in interactive mode')
@click.option('--threshold', type=float, help='Auto-merge confidence threshold')
@click.pass_context
def run(ctx, interactive, threshold):
    """Run the complete deduplication process."""
    cli_instance = ctx.obj['cli']
    cli_instance.run_deduplication(interactive, threshold)


@cli.command()
@click.option('--threshold', default=0.6, type=float, help='Minimum confidence threshold')
@click.pass_context
def review(ctx, threshold):
    """Review potential merge candidates without performing merges."""
    cli_instance = ctx.obj['cli']
    cli_instance.review_candidates(threshold)


@cli.command()
@click.pass_context
def stats(ctx):
    """Display deduplication statistics and database information."""
    cli_instance = ctx.obj['cli']
    cli_instance.show_statistics()


@cli.command()
@click.argument('original_id')
@click.pass_context
def lookup(ctx, original_id):
    """Look up canonical entity ID for an original entity ID."""
    cli_instance = ctx.obj['cli']
    cli_instance.lookup_mapping(original_id)


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate current configuration."""
    config = ctx.obj['config']
    
    console.print("\n[bold blue]🔧 Configuration Validation[/bold blue]\n")
    
    issues = config.validate_config()
    
    if not issues:
        console.print("[bold green]✅ Configuration is valid![/bold green]")
        
        # Display current settings
        settings_table = Table(title="Current Settings")
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Value", style="magenta")
        
        settings_table.add_row("Environment", config.__class__.__name__)
        settings_table.add_row("Auto-merge threshold", str(config.AUTO_MERGE_THRESHOLD))
        settings_table.add_row("Name similarity threshold", str(config.NAME_SIMILARITY_THRESHOLD))
        settings_table.add_row("Interactive mode", str(config.INTERACTIVE_MODE))
        settings_table.add_row("Database URI", config.NEO4J_URI)
        
        console.print(settings_table)
    else:
        console.print("[bold red]❌ Configuration issues found:[/bold red]")
        for issue in issues:
            console.print(f"  • {issue}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
