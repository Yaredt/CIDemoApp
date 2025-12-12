"""
Main entry point for the lead generation system
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

from orchestration.workflow import LeadGenerationWorkflow
from config.settings import get_settings

# Setup rich console
console = Console()

# Setup logging
def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
@click.pass_context
def cli(ctx, log_level):
    """Lead Generation Multi-Agent System"""
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    setup_logging(log_level)


@cli.command()
@click.option("--max-results", default=50, help="Maximum results per agent")
@click.option("--export-format", default="json", help="Export format (json, csv)")
@click.option("--output", default=None, help="Output file path")
@click.pass_context
def run(ctx, max_results, export_format, output):
    """
    Run the lead generation workflow
    """
    console.print("\n[bold blue]🚀 Starting Lead Generation System[/bold blue]\n")

    async def execute():
        # Initialize workflow
        workflow = LeadGenerationWorkflow(config={"max_results": max_results})

        # Execute workflow
        result = await workflow.execute()

        if not result.success:
            console.print(f"[bold red]❌ Workflow failed: {result.error}[/bold red]")
            return 1

        leads = result.leads_found

        # Display results
        console.print(f"\n[bold green]✅ Workflow completed successfully![/bold green]")
        console.print(f"[bold]Total leads found:[/bold] {len(leads)}")
        console.print(f"[bold]Execution time:[/bold] {result.execution_time:.2f}s\n")

        # Display top leads
        if leads:
            display_top_leads(leads[:10])

            # Export leads
            if output:
                export_path = await workflow.export_leads(leads, export_format, output)
                console.print(f"\n[bold green]Exported leads to:[/bold green] {export_path}")

        return 0

    # Run async workflow
    exit_code = asyncio.run(execute())
    sys.exit(exit_code)


@cli.command()
@click.option("--limit", default=10, help="Number of leads to show")
def top(limit):
    """
    Show top ranked leads from database
    """
    async def get_top():
        workflow = LeadGenerationWorkflow()
        leads = await workflow.get_top_leads(limit)

        if not leads:
            console.print("[yellow]No leads found in database[/yellow]")
            return

        display_top_leads(leads)

    asyncio.run(get_top())


@cli.command()
@click.argument("lead_id")
def show(lead_id):
    """
    Show details for a specific lead
    """
    async def show_lead():
        from orchestration.storage import LeadStorage

        storage = LeadStorage()
        lead = await storage.get_lead(lead_id)

        if not lead:
            console.print(f"[red]Lead not found: {lead_id}[/red]")
            return

        # Display lead details
        console.print(f"\n[bold]Lead Details: {lead.company.name}[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("ID", lead.id)
        table.add_row("Company", lead.company.name)
        table.add_row("Industry", lead.company.industry.value)
        table.add_row("Website", str(lead.company.website) if lead.company.website else "N/A")
        table.add_row("Location", lead.company.location or "N/A")
        table.add_row("Employees", str(lead.company.employee_count) if lead.company.employee_count else "N/A")

        if lead.score:
            table.add_row("Overall Score", f"{lead.score.overall_score:.1f}")
            table.add_row("Fit Score", f"{lead.score.fit_score:.1f}")
            table.add_row("Intent Score", f"{lead.score.intent_score:.1f}")
            table.add_row("Timing Score", f"{lead.score.timing_score:.1f}")

        table.add_row("Status", lead.status.value)
        table.add_row("Buying Signals", ", ".join([s.value for s in lead.buying_signals]))
        table.add_row("Contacts", str(len(lead.contacts)))
        table.add_row("Created", lead.created_at.strftime("%Y-%m-%d %H:%M"))

        console.print(table)

        await storage.close()

    asyncio.run(show_lead())


@cli.command()
def config():
    """
    Show current configuration
    """
    settings = get_settings()

    console.print("\n[bold]Configuration Settings[/bold]\n")

    table = Table(show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Environment", settings.environment)
    table.add_row("Debug Mode", str(settings.debug))
    table.add_row("Azure OpenAI Endpoint", settings.azure_openai_endpoint)
    table.add_row("Azure OpenAI Deployment", settings.azure_openai_deployment)
    table.add_row("Cosmos Database", settings.cosmos_database)
    table.add_row("Max Results Per Agent", str(settings.max_results_per_agent))
    table.add_row("Min Employee Count", str(settings.min_employee_count))
    table.add_row("Target Industries", ", ".join(settings.target_industries))

    # API Keys status
    table.add_row("Serper API Key", "✓ Configured" if settings.serper_api_key else "✗ Not configured")
    table.add_row("Hunter.io API Key", "✓ Configured" if settings.hunter_api_key else "✗ Not configured")
    table.add_row("Clearbit API Key", "✓ Configured" if settings.clearbit_api_key else "✗ Not configured")
    table.add_row("SAM.gov API Key", "✓ Configured" if settings.sam_gov_api_key else "✗ Not configured")

    console.print(table)


def display_top_leads(leads):
    """Display top leads in a table"""
    console.print("\n[bold]Top Ranked Leads[/bold]\n")

    table = Table()
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Company", style="bold")
    table.add_column("Industry")
    table.add_column("Score", justify="right")
    table.add_column("Signals", justify="center")
    table.add_column("Status")

    for i, lead in enumerate(leads, 1):
        score = f"{lead.score.overall_score:.1f}" if lead.score else "N/A"
        signals = str(len(lead.buying_signals))

        table.add_row(
            str(i),
            lead.company.name,
            lead.company.industry.value,
            score,
            signals,
            lead.status.value
        )

    console.print(table)


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == "__main__":
    main()
