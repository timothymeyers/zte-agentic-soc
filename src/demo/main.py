"""
Demo main script for Agentic SOC.

Demonstrates workflow execution with mock data and real-time agent interactions.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
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


# =============================================================================
# Utility Functions
# =============================================================================


def _strip_markdown_codeblock(text: str) -> str:
    """Remove markdown code block markers from text."""
    if not text.startswith("```"):
        return text
    
    lines = text.split("\n")
    if len(lines) > 2:
        return "\n".join(lines[1:-1]).strip()
    return text[3:].strip() if text.startswith("```") else text


def _format_json(data: Any, max_length: int = 2000) -> Optional[str]:
    """
    Attempt to format data as JSON. Returns None if not JSON-serializable.
    
    Args:
        data: Data to format (dict, str, or other)
        max_length: Maximum length before truncating
        
    Returns:
        Formatted JSON string or None
    """
    try:
        if isinstance(data, dict):
            json_str = json.dumps(data, indent=2)
        elif isinstance(data, str) and data.strip().startswith("{"):
            json_str = json.dumps(json.loads(data), indent=2)
        else:
            return None
        
        if len(json_str) > max_length:
            return json_str[:max_length] + "\n... (truncated)"
        return json_str
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _format_event_data(data: Any, max_length: int = 500) -> str:
    """Format event data as text, with smart truncation."""
    if not data:
        return ""
    
    text = str(data)
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


class WorkflowDemo:
    """
    Interactive workflow demonstration.
    """

    def __init__(self):
        """Initialize demo."""
        self.console = Console()
        self.workflow = None
        self.scenario_manager = ScenarioManager()
        self.last_event_type = None
        self.agent_buffer = {}  # {agent_name: accumulated_text}

        logger.info("WorkflowDemo initialized")

    def _print_output(self, text: str):
        """Write text directly to stdout, bypassing Rich rendering."""
        import sys
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    def _flush_agent_buffer(self):
        """Flush buffered agent output and clear buffer."""
        import sys
        for agent, text in self.agent_buffer.items():
            if text:
                text = _strip_markdown_codeblock(text)
                if text.strip():
                    sys.stdout.write(text + "\n")
                    sys.stdout.flush()
        self.agent_buffer = {}

    def _print_scenario_header(self, title: str, description: str = ""):
        """Print a formatted demo header with title and optional description."""
        self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
        if description:
            self.console.print(f"[dim]{description}[/dim]\n")

    def _print_scenario_info(self, scenario):
        """Print scenario metadata in a formatted table."""
        info_table = Table(show_header=False, box=None)
        info_table.add_row("Alerts:", str(scenario.get_alert_count()))
        info_table.add_row("Expected Triage:", scenario.metadata.get("expected_triage", "N/A"))
        info_table.add_row("Duration:", f"{scenario.metadata.get('duration_minutes', 'N/A')} minutes")
        self.console.print(Panel(info_table, title="Scenario Info", border_style="blue"))
        self.console.print("\n[bold]Starting workflow execution...[/bold]\n")

    def _print_demo_stats(self, demo_type: str, event_count: int, duration: float = 0.0):
        """Print demo completion stats."""
        self.console.print(f"\n[bold green]✓ {demo_type} complete[/bold green]")
        if duration > 0:
            self.console.print(f"[dim]Events: {event_count} | Duration: {duration:.2f}s[/dim]\n")
        else:
            self.console.print(f"[dim]Events: {event_count}[/dim]\n")


    def _display_magentic_event(self, event: dict, event_type: str):
        """Display magentic orchestrator events."""
        magentic_type = event.get("magentic_type", "unknown")
        agent = event.get("agent", "N/A")
        event_data = event.get("event_data", "")

        handlers = {
            "plan_created": lambda: self._show_plan(event_data),
            "agent_selected": lambda: self.console.print(f"[blue]🎯 Selected agent: {agent}[/blue]"),
            "agent_response": lambda: self._show_agent_response(agent, event_data),
            "progress_update": lambda: self.console.print(f"[yellow]⏳ Progress: {event_data}[/yellow]"),
            "workflow_complete": lambda: self.console.print(f"[green]✅ Workflow complete[/green]"),
        }

        handler = handlers.get(magentic_type)
        if handler:
            handler()
        
        self.last_event_type = event_type

    def _show_plan(self, data: str):
        """Display manager's plan."""
        self.console.print(f"[cyan]📋 Manager created plan[/cyan]")
        if data:
            formatted = _format_event_data(data, max_length=300)
            self.console.print(f"[dim]{formatted}[/dim]")

    def _show_agent_response(self, agent: str, response: Any):
        """Display agent response with smart JSON formatting."""
        if self.last_event_type != "magentic_agent_response":
            self.console.print(f"[green]💬 {agent} responded[/green]")
        
        if not response:
            return
        
        # Try JSON formatting first
        json_str = _format_json(response)
        if json_str:
            if len(json_str) > 150:
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                self.console.print(syntax)
            else:
                self.console.print(f"[dim]{json_str}[/dim]")
        else:
            # Fallback to plain text
            formatted = _format_event_data(response, max_length=300)
            self.console.print(f"[dim]{formatted}[/dim]")

    def _display_agent_event(self, event: dict):
        """Buffer and display agent streaming events."""
        event_data = event.get("event_data", "")
        agent = event.get("agent", "Unknown")
        
        if not event_data:
            return
        
        # Show header for new agent
        if agent not in self.agent_buffer:
            self.console.print(f"[blue]🤖 {agent}:[/blue]")
            self.agent_buffer[agent] = ""
        
        # Accumulate and flush when buffer is large
        self.agent_buffer[agent] += str(event_data)
        if len(self.agent_buffer[agent]) > 2000:
            text = _strip_markdown_codeblock(self.agent_buffer[agent])
            self._print_output(text)
            self.agent_buffer[agent] = ""
        
        self.last_event_type = "agent_event"

    def _display_event(self, event: dict):
        """
        Display workflow event based on type.

        Args:
            event: Event dictionary
        """
        event_type = event.get("type", "unknown")

        # Event type handlers
        if event_type == "workflow_start":
            self._flush_agent_buffer()
            self.console.print(f"[bold green]▶ Workflow Started[/bold green]")
            self.console.print(f"[dim]ID: {event['execution_id']}[/dim]")
            self.last_event_type = event_type

        elif event_type == "workflow_complete":
            self._flush_agent_buffer()
            duration = event.get("duration_seconds", 0)
            self.console.print(f"\n[bold green]✓ Workflow Complete[/bold green] ({duration:.2f}s)")
            self.last_event_type = event_type

        elif event_type.startswith("magentic_"):
            self._display_magentic_event(event, event_type)

        elif event_type == "workflow_error":
            self.console.print(f"[red]❌ Error: {event.get('error', 'Unknown error')}[/red]")
            self.last_event_type = event_type

        elif event_type == "agent_event":
            self._display_agent_event(event)

        else:
            # Generic event display
            event_data = event.get("event_data", "")
            if event_data and event_type != self.last_event_type:
                formatted = _format_event_data(event_data, max_length=300)
                self.console.print(f"[dim]• {event_type}: {formatted}[/dim]")
                self.last_event_type = event_type
            elif not event_data and event_type != self.last_event_type:
                self.console.print(f"[dim]• {event_type}[/dim]")
                self.last_event_type = event_type

    async def setup(self):
        """Setup workflow and agents."""
        self.console.print("\n[bold blue]🔧 Setting up Agentic SOC...[/bold blue]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            progress.add_task("Connecting to Microsoft Foundry...", total=None)
            #await asyncio.sleep(0.5)

            progress.add_task("Discovering deployed agents...", total=None)
            await asyncio.sleep(0.5)

            task3 = progress.add_task("Creating magentic workflow...", total=None)
            
            try:
                self.workflow = await create_soc_workflow()
                #await asyncio.sleep(0.5)
                progress.update(task3, completed=True)
            except Exception as e:
                self.console.print(f"\n[red]❌ Setup failed: {e}[/red]")
                logger.error("Workflow setup failed", error=str(e), exc_info=True)
                raise

        self.console.print("\n[bold green]✓ Setup complete[/bold green]\n")

    async def run_scenario_demo(self, scenario_name: str):
        """
        Run a scenario demo with full event streaming and timing.
        
        Args:
            scenario_name: Name of the scenario to run (e.g., 'brute_force')
        """
        scenario = self.scenario_manager.get_scenario(scenario_name)
        if not scenario:
            self.console.print(f"[red]❌ Scenario not found: {scenario_name}[/red]")
            return

        self._print_scenario_header(f"🎯 Running Scenario: {scenario.name}", scenario.description)
        self._print_scenario_info(scenario)

        event_count = 0
        start_time = datetime.now(timezone.utc)

        async for event in run_scenario_workflow(self.workflow, scenario_name, scenario.alerts):
            event_count += 1
            self._display_event(event)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        self._print_demo_stats("Scenario", event_count, duration)

    async def run_alert_demo(self, dataset: str = "guide", limit: int = 1):
        """
        Run alert triage demo with mock data.
        
        Args:
            dataset: Dataset name (default: 'guide')
            limit: Number of alerts to process (default: 1)
        """
        self.console.print(f"\n[bold cyan]📡 Alert Triage Demo[/bold cyan]")
        self.console.print(f"[dim]Dataset: {dataset.upper()} | Alerts: {limit}[/dim]\n")

        streamer = MockDataStreamer(interval_seconds=0, dataset=dataset)

        alert_count = 0
        async for alert in streamer.stream_alerts(limit=limit):
            alert_count += 1
            self.console.print(f"\n[bold]Alert {alert_count}:[/bold] {alert.alert_name}")
            self.console.print(f"[yellow]Severity: {alert.severity.value}[/yellow]")

            event_count = 0
            async for event in run_alert_triage_workflow(self.workflow, alert):
                event_count += 1
                self._display_event(event)

            self.console.print(f"[dim]Events: {event_count}[/dim]\n")

    async def run_hunt_demo(self, query: str):
        """
        Run threat hunting demo with event streaming.
        
        Args:
            query: Threat hunting query
        """
        self._print_scenario_header("🔍 Threat Hunting Demo", f"Query: {query}")

        event_count = 0
        async for event in run_threat_hunt_workflow(self.workflow, query):
            event_count += 1
            self._display_event(event)

        self._print_demo_stats("Hunt", event_count)

    def list_scenarios(self):
        """Display available scenarios in a formatted table."""
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
                description = scenario.description
                if len(description) > 50:
                    description = description[:50] + "..."
                table.add_row(
                    name,
                    description,
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
