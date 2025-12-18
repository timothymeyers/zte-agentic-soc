"""
CLI commands for Agentic SOC demo.

Provides command-line interface for deploying agents and running workflows.
"""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.deployment.deploy_agents import (
    AGENT_DEFINITIONS,
    deploy_all_agents,
    list_deployed_agents,
    cleanup_agents,
)
from src.shared.logging import get_logger

app = typer.Typer(
    name="***-soc",
    help="Agentic SOC - AI-powered Security Operations Center",
    add_completion=False,
)

console = Console()
logger = get_logger(__name__, module="cli")


# =============================================================================
# Deployment Commands
# =============================================================================


@app.command()
def deploy(
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Comma-separated list of agents to deploy (manager,triage,hunting,response,intelligence). Default: all",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force redeployment even if agents already exist",
    ),
):
    """
    Deploy AI agents to Microsoft Foundry.

    Examples:
        # Deploy only manager agent
        ***-soc deploy --agents manager

        # Deploy multiple agents
        ***-soc deploy --agents manager,triage

        # Deploy all agents
        ***-soc deploy
    """
    console.print("\n[bold blue]🚀 Deploying Agents to Microsoft Foundry[/bold blue]\n")

    # Parse agent list
    agent_keys = None
    if agents:
        agent_keys = [a.strip() for a in agents.split(",")]
        # Validate agent keys
        invalid = [k for k in agent_keys if k not in AGENT_DEFINITIONS]
        if invalid:
            console.print(f"[red]❌ Invalid agent keys: {', '.join(invalid)}[/red]")
            console.print(f"[yellow]Valid keys: {', '.join(AGENT_DEFINITIONS.keys())}[/yellow]")
            raise typer.Exit(code=1)

    try:
        # Run deployment
        deployed = asyncio.run(deploy_all_agents(agent_keys))

        # Display results
        table = Table(title="Deployed Agents", show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("ID", style="yellow")
        table.add_column("Model", style="blue")

        for key, agent in deployed.items():
            table.add_column(
                key.upper(),
                agent.name,
                agent.id[:16] + "...",
                agent.model,
            )

        console.print(table)
        console.print("\n[bold green]✓ Deployment Complete[/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]❌ Deployment failed: {e}[/bold red]\n")
        logger.error("Deployment failed", error=str(e), exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def list_agents():
    """
    List all deployed agents in Microsoft Foundry.

    Example:
        ***-soc list-agents
    """
    console.print("\n[bold blue]📋 Listing Deployed Agents[/bold blue]\n")

    try:
        # List agents
        agents = asyncio.run(list_deployed_agents())

        if not agents:
            console.print("[yellow]No agents deployed yet.[/yellow]\n")
            return

        # Display results
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="yellow")
        table.add_column("Model", style="green")
        table.add_column("Description", style="blue")

        for agent in agents:
            table.add_row(
                agent.name,
                agent.id[:16] + "...",
                agent.model,
                agent.description[:50] + "..." if len(agent.description) > 50 else agent.description,
            )

        console.print(table)
        console.print(f"\n[bold green]✓ Found {len(agents)} agents[/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]❌ Failed to list agents: {e}[/bold red]\n")
        logger.error("List agents failed", error=str(e), exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def cleanup(
    agents: str = typer.Argument(
        ...,
        help="Comma-separated list of agent names to delete",
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """
    Delete deployed agents from Microsoft Foundry.

    Example:
        ***-soc cleanup SOC_Manager,AlertTriageAgent
    """
    agent_names = [a.strip() for a in agents.split(",")]

    console.print("\n[bold yellow]⚠️  Agent Cleanup[/bold yellow]\n")
    console.print(f"Agents to delete: {', '.join(agent_names)}\n")

    if not confirm:
        proceed = typer.confirm("Are you sure you want to delete these agents?")
        if not proceed:
            console.print("[yellow]Cleanup cancelled.[/yellow]\n")
            raise typer.Exit(code=0)

    try:
        # Cleanup agents
        deleted_count = asyncio.run(cleanup_agents(agent_names))

        console.print(f"\n[bold green]✓ Deleted {deleted_count} agents[/bold green]\n")

    except Exception as e:
        console.print(f"\n[bold red]❌ Cleanup failed: {e}[/bold red]\n")
        logger.error("Cleanup failed", error=str(e), exc_info=True)
        raise typer.Exit(code=1)


# =============================================================================
# Workflow Commands (Phase 3B - to be implemented)
# =============================================================================


@app.command()
def run_workflow(
    scenario: str = typer.Argument(
        ...,
        help="Scenario name to run (brute_force, phishing_campaign, ransomware, lateral_movement, mixed_alerts)",
    ),
):
    """
    Run a demo workflow with a curated scenario.

    Examples:
        asoc run-workflow brute_force
        asoc run-workflow phishing_campaign
        asoc run-workflow mixed_alerts
    """
    from src.demo.main import WorkflowDemo

    console.print(f"\n[bold blue]🎯 Running Workflow: {scenario}[/bold blue]\n")

    try:
        demo = WorkflowDemo()

        # Run setup and scenario
        async def run():
            await demo.setup()
            await demo.run_scenario_demo(scenario)

        asyncio.run(run())

    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow interrupted by user[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]❌ Workflow failed: {e}[/bold red]\n")
        logger.error("Workflow execution failed", error=str(e), exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def stream_alerts(
    dataset: str = typer.Option(
        "guide",
        "--dataset",
        "-d",
        help="Dataset to stream from (guide or attack)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Number of alerts to stream",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        "-i",
        help="Interval between alerts in seconds",
    ),
):
    """
    Stream mock security alerts with triage workflow.

    Examples:
        asoc stream-alerts --dataset guide --limit 5
        asoc stream-alerts --dataset attack --limit 3 --interval 0.5
    """
    from src.demo.main import WorkflowDemo

    console.print(f"\n[bold blue]📡 Streaming Alerts from {dataset.upper()} Dataset[/bold blue]\n")

    try:
        demo = WorkflowDemo()

        # Run setup and alert demo
        async def run():
            await demo.setup()
            await demo.run_alert_demo(dataset=dataset, limit=limit)

        asyncio.run(run())

    except KeyboardInterrupt:
        console.print("\n[yellow]Streaming interrupted by user[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]❌ Streaming failed: {e}[/bold red]\n")
        logger.error("Alert streaming failed", error=str(e), exc_info=True)
        raise typer.Exit(code=1)


# =============================================================================
# Information Commands
# =============================================================================


@app.command()
def list_scenarios():
    """
    List available demo scenarios.

    Example:
        asoc list-scenarios
    """
    from src.data.scenarios import ScenarioManager

    manager = ScenarioManager()
    scenarios = manager.list_scenarios()

    console.print("\n[bold cyan]📋 Available Scenarios[/bold cyan]\n")

    from rich.table import Table

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Alerts", style="yellow")
    table.add_column("Expected Triage", style="green")

    for name in scenarios:
        scenario = manager.get_scenario(name)
        if scenario:
            summary = scenario.get_summary()
            table.add_row(
                name,
                summary["description"][:60] + "..." if len(summary["description"]) > 60 else summary["description"],
                str(summary["alert_count"]),
                summary["metadata"].get("expected_triage", "N/A"),
            )

    console.print(table)
    console.print()


@app.command()
def version():
    """
    Show version information.
    """
    console.print("\n[bold cyan]Agentic SOC - MVP v0.1.0[/bold cyan]")
    console.print("AI-powered Security Operations Center\n")
    console.print("Phase 1-2: Setup & Foundational ✓")
    console.print("Phase 3A: Infrastructure Deployment ✓")
    console.print("Phase 3B: Runtime Orchestration ✓")
    console.print()


@app.command()
def info():
    """
    Show system information and configuration.
    """
    import os

    console.print("\n[bold cyan]System Information[/bold cyan]\n")

    # Environment configuration
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Configuration", style="cyan")
    table.add_column("Value", style="yellow")

    config_items = [
        ("Environment", os.getenv("ENVIRONMENT", "development")),
        ("Log Level", os.getenv("LOG_LEVEL", "INFO")),
        ("Project Endpoint", os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT", "Not set")[:50] + "..."),
        ("Model Deployment", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "Not set")),
        ("Resource Group", os.getenv("AZURE_RESOURCE_GROUP", "Not set")),
    ]

    for key, value in config_items:
        table.add_row(key, value)

    console.print(table)
    console.print()


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """
    Main CLI entry point.
    """
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]\n")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
        logger.error("CLI error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
