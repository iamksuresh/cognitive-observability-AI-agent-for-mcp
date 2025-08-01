"""
Trace Visualizer for MCP Component Flows.

Displays beautiful visualizations of request flows through components.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TimeElapsedColumn

from .models import (
    RequestFlow,
    ComponentInteraction,
    TraceEvent,
    TraceAnalysis,
    ComponentType,
    TraceEventType
)

console = Console()


class TraceVisualizer:
    """
    Visualizes MCP component traces with beautiful CLI output.
    
    Shows complete request flows, component interactions, timing,
    and performance analysis in an easy-to-understand format.
    """
    
    def __init__(self):
        """Initialize the trace visualizer."""
        self.component_colors = {
            ComponentType.USER_INTERFACE: "blue",
            ComponentType.MCP_HOST: "green", 
            ComponentType.LLM_ENGINE: "purple",
            ComponentType.MCP_CLIENT: "cyan",
            ComponentType.MCP_SERVER: "yellow",
            ComponentType.EXTERNAL_API: "red",
            ComponentType.AUDIT_AGENT: "magenta",
            ComponentType.FILE_SYSTEM: "white",
            ComponentType.DATABASE: "bright_blue",
            ComponentType.NETWORK: "bright_green"
        }
    
    def display_flow_overview(self, flow: RequestFlow) -> None:
        """Display a high-level overview of the request flow."""
        # Create status color
        status_color = "green" if flow.status == "completed" else "red" if flow.status == "failed" else "yellow"
        
        # Overview panel
        overview_content = [
            f"[bold]Flow ID:[/bold] {flow.flow_id}",
            f"[bold]User Query:[/bold] {flow.user_query}",
            f"[bold]Status:[/bold] [{status_color}]{flow.status.upper()}[/{status_color}]",
            f"[bold]Duration:[/bold] {flow.total_latency_ms or 0}ms",
            f"[bold]Components:[/bold] {flow.component_count}",
            f"[bold]API Calls:[/bold] {flow.api_calls_count}",
            f"[bold]Retries:[/bold] {flow.retry_count}",
            f"[bold]Errors:[/bold] {flow.error_count}"
        ]
        
        if flow.final_response:
            overview_content.append(f"[bold]Response:[/bold] {flow.final_response[:100]}...")
        
        if flow.error_summary:
            overview_content.append(f"[bold red]Error:[/bold red] {flow.error_summary}")
        
        console.print(Panel(
            "\n".join(overview_content),
            title=f"[bold blue]Request Flow Overview[/bold blue]",
            border_style="blue"
        ))
    
    def display_component_flow_diagram(self, flow: RequestFlow) -> None:
        """Display a visual diagram of the component flow."""
        if not flow.interactions:
            console.print("[yellow]No interactions to display[/yellow]")
            return
        
        console.print("\n[bold blue]🔄 Component Flow Diagram[/bold blue]")
        
        # Build the flow diagram
        diagram_lines = []
        seen_components = set()
        
        for i, interaction in enumerate(flow.interactions):
            source = interaction.source_name
            target = interaction.target_name
            operation = interaction.operation
            
            # Get colors for components
            source_color = self.component_colors.get(interaction.source_component, "white")
            target_color = self.component_colors.get(interaction.target_component, "white")
            
            # Create the flow line
            success_indicator = "✅" if interaction.success else "❌"
            latency = f"({interaction.latency_ms}ms)" if interaction.latency_ms else ""
            
            # Add components to seen set
            if source not in seen_components:
                diagram_lines.append(f"   [{source_color}]┌─ {source}[/{source_color}]")
                seen_components.add(source)
            
            # Add the interaction
            arrow = "──>" if interaction.success else "╳─>"
            diagram_lines.append(
                f"   [{source_color}]│[/{source_color}] {success_indicator} "
                f"[dim]{operation}[/dim] {arrow} "
                f"[{target_color}]{target}[/{target_color}] {latency}"
            )
            
            if target not in seen_components:
                diagram_lines.append(f"   [{target_color}]└─ {target}[/{target_color}]")
                seen_components.add(target)
        
        console.print("\n".join(diagram_lines))
    
    def display_interaction_timeline(self, flow: RequestFlow) -> None:
        """Display a detailed timeline of all interactions."""
        if not flow.interactions:
            return
        
        console.print(f"\n[bold green]⏱️  Interaction Timeline[/bold green]")
        
        # Create timeline table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Source", width=15)
        table.add_column("→", justify="center", width=3)
        table.add_column("Target", width=15)
        table.add_column("Operation", width=20)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Status", justify="center", width=8)
        
        # Add interactions to timeline
        for interaction in flow.interactions:
            # Format time relative to flow start
            time_offset = 0
            if interaction.start_time and flow.start_time:
                time_offset = int((interaction.start_time - flow.start_time).total_seconds() * 1000)
            
            time_str = f"+{time_offset}ms"
            duration_str = f"{interaction.latency_ms or 0}ms"
            status_str = "✅ OK" if interaction.success else "❌ ERR"
            status_style = "green" if interaction.success else "red"
            
            # Get component colors
            source_color = self.component_colors.get(interaction.source_component, "white")
            target_color = self.component_colors.get(interaction.target_component, "white")
            
            table.add_row(
                time_str,
                f"[{source_color}]{interaction.source_name}[/{source_color}]",
                "→",
                f"[{target_color}]{interaction.target_name}[/{target_color}]",
                interaction.operation,
                duration_str,
                f"[{status_style}]{status_str}[/{status_style}]"
            )
        
        console.print(table)
    
    def display_detailed_events(self, flow: RequestFlow, interaction_id: Optional[str] = None) -> None:
        """Display detailed events for interactions."""
        interactions_to_show = flow.interactions
        
        if interaction_id:
            interactions_to_show = [i for i in flow.interactions if i.interaction_id == interaction_id]
            if not interactions_to_show:
                console.print(f"[red]Interaction {interaction_id} not found[/red]")
                return
        
        for interaction in interactions_to_show:
            if not interaction.events:
                continue
            
            console.print(f"\n[bold cyan]🔍 Events for {interaction.source_name} → {interaction.target_name}[/bold cyan]")
            
            # Create events table
            events_table = Table(show_header=True, header_style="bold yellow")
            events_table.add_column("Time", style="dim", width=12)
            events_table.add_column("Event", width=20)
            events_table.add_column("Component", width=15)
            events_table.add_column("Description", width=40)
            events_table.add_column("Duration", justify="right", width=10)
            
            for event in interaction.events:
                # Format time
                time_offset = 0
                if event.timestamp and interaction.start_time:
                    time_offset = int((event.timestamp - interaction.start_time).total_seconds() * 1000)
                
                time_str = f"+{time_offset}ms"
                duration_str = f"{event.duration_ms or 0}ms" if event.duration_ms else ""
                
                # Event type styling
                event_style = "green"
                if event.event_type == TraceEventType.ERROR_OCCURRED:
                    event_style = "red"
                elif event.event_type in [TraceEventType.REQUEST_START, TraceEventType.REQUEST_END]:
                    event_style = "blue"
                
                component_color = self.component_colors.get(event.component, "white")
                
                events_table.add_row(
                    time_str,
                    f"[{event_style}]{event.event_type.value}[/{event_style}]",
                    f"[{component_color}]{event.component_name}[/{component_color}]",
                    event.description,
                    duration_str
                )
            
            console.print(events_table)
            
            # Show error details if any
            error_events = [e for e in interaction.events if e.is_error()]
            if error_events:
                console.print(f"\n[bold red]❌ Errors in this interaction:[/bold red]")
                for error_event in error_events:
                    console.print(f"   • {error_event.description}")
                    if error_event.error_message:
                        console.print(f"     [dim]Error: {error_event.error_message}[/dim]")
    
    def display_performance_analysis(self, analysis: TraceAnalysis) -> None:
        """Display performance analysis of a flow."""
        console.print(f"\n[bold magenta]📊 Performance Analysis[/bold magenta]")
        
        # Performance metrics panel
        perf_content = [
            f"[bold]Total Duration:[/bold] {analysis.total_duration_ms}ms",
            f"[bold]Critical Path:[/bold] {analysis.critical_path_duration_ms}ms",
            f"[bold]Network Latency:[/bold] {analysis.network_latency_ms}ms",
            f"[bold]Processing Time:[/bold] {analysis.processing_time_ms}ms",
            "",
            f"[bold]Complexity Score:[/bold] {analysis.complexity_score:.1f}/100",
            f"[bold]Efficiency Score:[/bold] {analysis.efficiency_score:.1f}/100",
            f"[bold]Reliability Score:[/bold] {analysis.reliability_score:.1f}/100"
        ]
        
        console.print(Panel(
            "\n".join(perf_content),
            title="[bold magenta]Performance Metrics[/bold magenta]",
            border_style="magenta"
        ))
        
        # Component performance table
        if analysis.component_performance:
            console.print(f"\n[bold cyan]🔧 Component Performance[/bold cyan]")
            
            comp_table = Table(show_header=True, header_style="bold cyan")
            comp_table.add_column("Component", width=20)
            comp_table.add_column("Calls", justify="right", width=8)
            comp_table.add_column("Total Time", justify="right", width=12)
            comp_table.add_column("Avg Latency", justify="right", width=12)
            comp_table.add_column("Errors", justify="right", width=8)
            comp_table.add_column("Status", justify="center", width=10)
            
            for comp_name, perf in analysis.component_performance.items():
                avg_latency = perf["avg_latency_ms"]
                error_count = perf["error_count"]
                
                # Determine status
                if comp_name in analysis.bottleneck_components:
                    status = "[red]BOTTLENECK[/red]"
                elif comp_name in analysis.efficient_components:
                    status = "[green]EFFICIENT[/green]"
                else:
                    status = "[yellow]NORMAL[/yellow]"
                
                comp_table.add_row(
                    comp_name,
                    str(perf["call_count"]),
                    f"{perf['total_time_ms']:.0f}ms",
                    f"{avg_latency:.0f}ms",
                    str(error_count),
                    status
                )
            
            console.print(comp_table)
        
        # Recommendations
        if analysis.performance_recommendations:
            console.print(f"\n[bold yellow]💡 Performance Recommendations[/bold yellow]")
            for i, rec in enumerate(analysis.performance_recommendations, 1):
                console.print(f"   {i}. {rec}")
    
    def display_error_analysis(self, flow: RequestFlow) -> None:
        """Display detailed error analysis."""
        error_points = flow.get_error_points()
        if not error_points:
            console.print("[green]✅ No errors detected in this flow[/green]")
            return
        
        console.print(f"\n[bold red]❌ Error Analysis ({len(error_points)} errors)[/bold red]")
        
        # Error summary table
        error_table = Table(show_header=True, header_style="bold red")
        error_table.add_column("Component", width=20)
        error_table.add_column("Operation", width=25)
        error_table.add_column("Error Message", width=40)
        error_table.add_column("Time", justify="right", width=12)
        
        for error_interaction in error_points:
            time_offset = 0
            if error_interaction.start_time and flow.start_time:
                time_offset = int((error_interaction.start_time - flow.start_time).total_seconds() * 1000)
            
            error_table.add_row(
                error_interaction.target_name,
                error_interaction.operation,
                error_interaction.error_message or "Unknown error",
                f"+{time_offset}ms"
            )
        
        console.print(error_table)
        
        # Error cascade analysis
        if len(error_points) > 1:
            console.print(f"\n[bold yellow]🔄 Error Cascade Analysis[/bold yellow]")
            console.print("   Error sequence:")
            for i, error in enumerate(error_points, 1):
                console.print(f"      {i}. {error.target_name}: {error.error_message}")
    
    def display_flow_summary_tree(self, flows: List[RequestFlow]) -> None:
        """Display a tree view of multiple flows."""
        if not flows:
            console.print("[yellow]No flows to display[/yellow]")
            return
        
        console.print(f"\n[bold blue]🌳 Flow Summary Tree[/bold blue]")
        
        tree = Tree("[bold blue]Request Flows[/bold blue]")
        
        for flow in flows:
            # Create flow node
            status_icon = "✅" if flow.status == "completed" else "❌" if flow.status == "failed" else "⏳"
            flow_label = f"{status_icon} {flow.user_query[:50]}... ({flow.total_latency_ms or 0}ms)"
            
            flow_node = tree.add(flow_label)
            
            # Add interaction summary
            if flow.interactions:
                interactions_node = flow_node.add(f"[cyan]Interactions ({len(flow.interactions)})[/cyan]")
                
                # Group by component pairs
                component_pairs = {}
                for interaction in flow.interactions:
                    pair_key = f"{interaction.source_name} → {interaction.target_name}"
                    if pair_key not in component_pairs:
                        component_pairs[pair_key] = []
                    component_pairs[pair_key].append(interaction)
                
                for pair_key, interactions in component_pairs.items():
                    success_count = sum(1 for i in interactions if i.success)
                    total_count = len(interactions)
                    avg_latency = sum(i.latency_ms or 0 for i in interactions) / total_count
                    
                    pair_label = f"{pair_key} ({success_count}/{total_count} success, {avg_latency:.0f}ms avg)"
                    interactions_node.add(pair_label)
        
        console.print(tree)
    
    def display_component_legend(self) -> None:
        """Display a legend of component types and colors."""
        console.print(f"\n[bold white]🎨 Component Legend[/bold white]")
        
        legend_table = Table(show_header=False, box=None, padding=(0, 2))
        legend_table.add_column("Icon", width=15)
        legend_table.add_column("Description", width=30)
        
        for comp_type, color in self.component_colors.items():
            icon = f"[{color}]●[/{color}]"
            description = comp_type.value.replace('_', ' ').title()
            legend_table.add_row(icon, description)
        
        console.print(legend_table)
    
    def export_flow_json(self, flow: RequestFlow, filename: Optional[str] = None) -> str:
        """Export flow data to JSON file."""
        from ..core.config import get_config
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trace_flow_{flow.flow_id[:8]}_{timestamp}.json"
        
        config = get_config()
        full_path = config.get_report_path(filename)
        
        # Convert to JSON-serializable format
        flow_data = {
            "flow_metadata": {
                "flow_id": flow.flow_id,
                "correlation_id": flow.correlation_id,
                "user_query": flow.user_query,
                "status": flow.status,
                "start_time": flow.start_time.isoformat(),
                "end_time": flow.end_time.isoformat() if flow.end_time else None,
                "total_latency_ms": flow.total_latency_ms,
                "component_count": flow.component_count,
                "api_calls_count": flow.api_calls_count,
                "retry_count": flow.retry_count,
                "error_count": flow.error_count
            },
            "interactions": [],
            "component_chain": flow.get_component_chain(),
            "critical_path": []
        }
        
        # Add interactions
        for interaction in flow.interactions:
            interaction_data = {
                "interaction_id": interaction.interaction_id,
                "source": {
                    "component": interaction.source_component.value,
                    "name": interaction.source_name
                },
                "target": {
                    "component": interaction.target_component.value,
                    "name": interaction.target_name
                },
                "operation": interaction.operation,
                "protocol": interaction.protocol,
                "method": interaction.method,
                "start_time": interaction.start_time.isoformat(),
                "end_time": interaction.end_time.isoformat() if interaction.end_time else None,
                "latency_ms": interaction.latency_ms,
                "success": interaction.success,
                "error_message": interaction.error_message,
                "request_data": interaction.request_data,
                "response_data": interaction.response_data,
                "events": []
            }
            
            # Add events
            for event in interaction.events:
                event_data = {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "component": event.component.value,
                    "component_name": event.component_name,
                    "description": event.description,
                    "duration_ms": event.duration_ms,
                    "input_data": event.input_data,
                    "output_data": event.output_data,
                    "error_code": event.error_code,
                    "error_message": event.error_message
                }
                interaction_data["events"].append(event_data)
            
            flow_data["interactions"].append(interaction_data)
        
        # Add critical path
        critical_path = flow.get_critical_path()
        flow_data["critical_path"] = [
            {
                "interaction_id": i.interaction_id,
                "source_name": i.source_name,
                "target_name": i.target_name,
                "operation": i.operation,
                "latency_ms": i.latency_ms
            }
            for i in critical_path[:5]  # Top 5 longest interactions
        ]
        
        # Write to file
        with open(full_path, 'w') as f:
            json.dump(flow_data, f, indent=2)
        
        console.print(f"[green]✅ Flow trace exported to: {full_path}[/green]")
        return str(full_path)
    
    def display_complete_trace(self, flow: RequestFlow, include_events: bool = True) -> None:
        """Display a complete trace visualization."""
        self.display_component_legend()
        self.display_flow_overview(flow)
        self.display_component_flow_diagram(flow)
        self.display_interaction_timeline(flow)
        
        if include_events:
            self.display_detailed_events(flow)
        
        self.display_error_analysis(flow)
        
        console.print(f"\n[bold green]🎯 End of trace for: {flow.user_query}[/bold green]") 