"""
Demo main script for Agentic SOC.

Demonstrates workflow execution with mock data and real-time agent interactions.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.data.scenarios import ScenarioManager
from src.data.streaming import MockDataStreamer
from src.orchestration.orchestrator import create_soc_workflow
from src.orchestration.workflows import (
    run_alert_triage_workflow,
    run_scenario_workflow,
    run_threat_hunt_workflow,
)
from src.shared.logging import get_logger

console = Console()
logger = get_logger(__name__, module="demo")


class WorkflowDemo:
    """
    Interactive workflow demonstration.
    """

    def __init__(self):
        """Initialize demo."""
        self.console = Console()
        self.workflow = None
        self.scenario_manager = ScenarioManager()

        logger.info("WorkflowDemo initialized")

    async def setup(self):
        """Setup workflow and agents."""
        self.console.print("\n[bold blue]🔧 Setting up Agentic SOC...[/bold blue]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            progress.add_task("Connecting to Microsoft Foundry...", total=None)
            await asyncio.sleep(0.5)  # Simulated delay

            progress.add_task("Discovering deployed agents...", total=None)
            await asyncio.sleep(0.5)

            task3 = progress.add_task("Creating magentic workflow...", total=None)
            
            try:
                self.workflow = create_soc_workflow()
                await asyncio.sleep(0.5)
                progress.update(task3, completed=True)
            except Exception as e:
                self.console.print(f"\n[red]❌ Setup failed: {e}[/red]")
                logger.error("Workflow setup failed", error=str(e), exc_info=True)
                raise

        self.console.print("\n[bold green]✓ Setup complete[/bold green]\n")

    async def run_scenario_demo(self, scenario_name: str):
        """
        Run a scenario demo.

        Args:
            scenario_name: Name of scenario to run
        """
        # Get scenario
        scenario = self.scenario_manager.get_scenario(scenario_name)
        if not scenario:
            self.console.print(f"[red]❌ Scenario not found: {scenario_name}[/red]")
            return

        self.console.print(f"\n[bold cyan]🎯 Running Scenario: {scenario.name}[/bold cyan]")
        self.console.print(f"[dim]{scenario.description}[/dim]\n")

        # Display scenario info
        info_table = Table(show_header=False, box=None)
        info_table.add_row("Alerts:", str(scenario.get_alert_count()))
        info_table.add_row("Expected Triage:", scenario.metadata.get("expected_triage", "N/A"))
        info_table.add_row("Duration:", f"{scenario.metadata.get('duration_minutes', 'N/A')} minutes")
        self.console.print(Panel(info_table, title="Scenario Info", border_style="blue"))

        # Run workflow
        self.console.print("\n[bold]Starting workflow execution...[/bold]\n")

        event_count = 0
        start_time = datetime.now(timezone.utc)

        async for event in run_scenario_workflow(self.workflow, scenario_name, scenario.alerts):
            event_count += 1
            self._display_event(event)

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        self.console.print(f"\n[bold green]✓ Scenario complete[/bold green]")
        self.console.print(f"[dim]Events: {event_count} | Duration: {duration:.2f}s[/dim]\n")

    async def run_alert_demo(self, dataset: str = "guide", limit: int = 1):
        """
        Run alert triage demo.

        Args:
            dataset: Dataset to use (guide or attack)
            limit: Number of alerts to process
        """
        self.console.print(f"\n[bold cyan]📡 Alert Triage Demo[/bold cyan]")
        self.console.print(f"[dim]Dataset: {dataset.upper()} | Alerts: {limit}[/dim]\n")

        # Stream alerts
        streamer = MockDataStreamer(interval_seconds=0, dataset=dataset)

        alert_count = 0
        async for alert in streamer.stream_alerts(limit=limit):
            alert_count += 1

            self.console.print(f"\n[bold]Alert {alert_count}:[/bold] {alert.alert_name}")
            self.console.print(f"[yellow]Severity: {alert.severity.value}[/yellow]")

            # Run workflow
            event_count = 0
            async for event in run_alert_triage_workflow(self.workflow, alert):
                event_count += 1
                self._display_event(event)

            self.console.print(f"[dim]Events: {event_count}[/dim]\n")

    async def run_hunt_demo(self, query: str):
        """
        Run threat hunting demo.

        Args:
            query: Natural language hunting query
        """
        self.console.print(f"\n[bold cyan]🔍 Threat Hunting Demo[/bold cyan]")
        self.console.print(f"[dim]Query: {query}[/dim]\n")

        event_count = 0
        async for event in run_threat_hunt_workflow(self.workflow, query):
            event_count += 1
            self._display_event(event)

        self.console.print(f"\n[dim]Events: {event_count}[/dim]\n")

    def _display_event(self, event: dict):
        """
        Display workflow event.

        Args:
            event: Event dictionary
        """
        event_type = event.get("type", "unknown")

        if event_type == "workflow_start":
            self.console.print(f"[bold green]▶ Workflow Started[/bold green]")
            self.console.print(f"[dim]ID: {event['execution_id']}[/dim]")

        elif event_type == "workflow_complete":
            duration = event.get("duration_seconds", 0)
            self.console.print(f"\n[bold green]✓ Workflow Complete[/bold green] ({duration:.2f}s)")

        elif event_type.startswith("magentic_"):
            magentic_type = event.get("magentic_type", "unknown")
            agent = event.get("agent", "N/A")

            if magentic_type == "plan_created":
                self.console.print(f"[cyan]📋 Manager created plan[/cyan]")
                self.console.print(f"[dim]{event.get('event_data', '')}[/dim]")

            elif magentic_type == "agent_selected":
                self.console.print(f"[blue]🎯 Selected agent: {agent}[/blue]")

            elif magentic_type == "agent_response":
                self.console.print(f"[green]💬 {agent} responded[/green]")
                response = event.get("event_data", "")
                if len(response) > 200:
                    response = response[:200] + "..."
                self.console.print(f"[dim]{response}[/dim]")

            elif magentic_type == "progress_update":
                self.console.print(f"[yellow]⏳ Progress: {event.get('event_data', '')}[/yellow]")

            elif magentic_type == "workflow_complete":
                self.console.print(f"[green]✅ Workflow complete[/green]")

        elif event_type == "workflow_error":
            self.console.print(f"[red]❌ Error: {event.get('error', 'Unknown error')}[/red]")

        else:
            # Generic event display
            self.console.print(f"[dim]• {event_type}: {event.get('event_data', '')}[/dim]")

    def list_scenarios(self):
        """List available scenarios."""
        scenarios = self.scenario_manager.list_scenarios()

        self.console.print("\n[bold cyan]Available Scenarios:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Alerts", style="yellow")
        table.add_column("Expected Triage", style="green")

        for name in scenarios:
            scenario = self.scenario_manager.get_scenario(name)
            if scenario:
                table.add_row(
                    name,
                    scenario.description[:50] + "..." if len(scenario.description) > 50 else scenario.description,
                    str(scenario.get_alert_count()),
                    scenario.metadata.get("expected_triage", "N/A"),
                )

        self.console.print(table)
        self.console.print()


# =============================================================================
# Entry Points
# =============================================================================


async def main():
    """
    Main demo entry point.

    Usage:
        python -m src.demo.main
    """
    console.print("\n[bold blue]═══════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]    Agentic SOC - Multi-Agent Workflow Demo       [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════[/bold blue]\n")

    demo = WorkflowDemo()

    try:
        # Setup
        await demo.setup()

        # List available scenarios
        demo.list_scenarios()

        # Interactive menu
        console.print("[bold]Select a demo:[/bold]")
        console.print("  1. Run scenario: Brute Force Attack")
        console.print("  2. Run scenario: Phishing Campaign")
        console.print("  3. Run scenario: Ransomware")
        console.print("  4. Run scenario: Mixed Alerts (testing prioritization)")
        console.print("  5. Single alert triage")
        console.print("  6. Threat hunting query")
        console.print()

        choice = console.input("[bold cyan]Choice (1-6):[/bold cyan] ")

        if choice == "1":
            await demo.run_scenario_demo("brute_force")
        elif choice == "2":
            await demo.run_scenario_demo("phishing_campaign")
        elif choice == "3":
            await demo.run_scenario_demo("ransomware")
        elif choice == "4":
            await demo.run_scenario_demo("mixed_alerts")
        elif choice == "5":
            await demo.run_alert_demo(dataset="guide", limit=1)
        elif choice == "6":
            query = console.input("[bold cyan]Enter hunting query:[/bold cyan] ")
            await demo.run_hunt_demo(query)
        else:
            console.print("[yellow]Invalid choice[/yellow]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]Demo failed: {e}[/bold red]\n")
        logger.error("Demo failed", error=str(e), exc_info=True)
        raise


async def quick_demo():
    """
    Quick demo without interactive prompts.

    Usage:
        python -m src.demo.main quick
    """
    console.print("\n[bold blue]🚀 Quick Demo: Brute Force Scenario[/bold blue]\n")

    demo = WorkflowDemo()

    try:
        await demo.setup()
        await demo.run_scenario_demo("brute_force")
    except Exception as e:
        console.print(f"\n[bold red]Demo failed: {e}[/bold red]\n")
        logger.error("Quick demo failed", error=str(e), exc_info=True)
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_demo())
    else:
        asyncio.run(main())
