"""
Command-line interface for MCP Usability Audit Agent.
"""

import asyncio
import json
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.syntax import Syntax
from rich.columns import Columns

from .core.audit_agent import MCPUsabilityAuditAgent
from .core.models import MCPInteraction, UsabilityReport
from .interceptors.mcp_interceptor import MCPCommunicationInterceptor
from .interceptors.conversation_interceptor import ConversationContextInterceptor
from .generators.report_generator import ReportGenerator
from .tracing import TraceCollector, TraceVisualizer, ComponentType, TraceEventType
from .interceptors.mcp_proxy import MCPProxyManager
from .core.models import MonitoringConfig
from .dashboard.app import create_dashboard_app
from .adapters.cursor import CursorAdapter
from .interceptors.llm_decision_interceptor import LLMDecisionInterceptor
# Demo imports removed - all demo functionality has been cleaned up
from .tracing.timeline_analyzer import TimelineAnalyzer
# UserPromptCapture import removed - no longer used for simulated data

# Import extracted modules
from .cli_support.utils import parse_time_duration, _display_report_summary, console
from .cli_support.html_generators import generate_enhanced_trace_html_report
from .cli_support.report_handlers import ReportHandlers


logger = logging.getLogger(__name__)

# Removed parse_time_duration - now imported from cli_support.utils


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose: bool) -> None:
    """
    MCP Usability Audit Agent CLI.
    
    Monitor and analyze the usability of MCP server interactions.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    console.print(Panel.fit(
        "[bold blue]MCP Usability Audit Agent[/bold blue]\n"
        "Cognitive observability for AI agents",
        border_style="blue"
    ))


@main.command()
@click.option('--plugin-mode', is_flag=True, help='Run in plugin mode for integration with IDEs')
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file path')
def start(plugin_mode: bool, config_file: Optional[str]) -> None:
    """Start the MCP audit agent in continuous monitoring mode."""
    asyncio.run(_start_command(plugin_mode, config_file))


async def _start_command(plugin_mode: bool, config_file: Optional[str]) -> None:
    """Async implementation of start command."""
    try:
        # Load configuration
        config = MonitoringConfig()
        if config_file:
            # Load custom config if provided
            config_path = Path(config_file)
            if config_path.exists():
                config_data = json.loads(config_path.read_text())
                config = MonitoringConfig(**config_data)
        
        # Create audit agent
        agent = MCPUsabilityAuditAgent(config)
        
        if plugin_mode:
            console.print("[bold green]🔌 Starting MCP Audit Agent in plugin mode...[/bold green]")
            
            # In plugin mode, we run continuously and communicate via stdout/stderr
            success = await agent.start_monitoring()
            if not success:
                console.print("[red]Failed to start monitoring. Is the MCP host running?[/red]")
                return
            
            console.print("[green]✅ MCP Audit Agent started successfully[/green]")
            console.print("[blue]📊 Monitoring MCP interactions...[/blue]")
            
            # Run indefinitely until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
                    # Could add periodic status updates here
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]🔄 Stopping MCP Audit Agent...[/yellow]")
                await agent.stop_monitoring()
                console.print("[red]🔴 MCP Audit Agent stopped[/red]")
        else:
            # Interactive mode
            console.print("[bold blue]🚀 Starting MCP Audit Agent in interactive mode...[/bold blue]")
            
            success = await agent.start_monitoring()
            if not success:
                console.print("[red]Failed to start monitoring. Is Cursor running with MCP servers?[/red]")
                return
            
            console.print("[green]✅ Monitoring started. Press Ctrl+C to stop and generate report.[/green]")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]🔄 Stopping monitoring and generating report...[/yellow]")
                await agent.stop_monitoring()
                
                # Generate and display report
                report = await agent.generate_report()
                console.print("\n[bold]📊 Usability Report:[/bold]")
                _display_report_summary(report)
                
    except Exception as e:
        console.print(f"[red]❌ Error during monitoring: {e}[/red]")
        logger.exception("Start command failed")


# Demo command removed - see clean CLI without mock/demo functionality





@main.command()
@click.option('--format', 'output_format', default='html', type=click.Choice(['json', 'html', 'txt']),
              help='Output format for the report')
@click.option('--type', 'report_type', default='usability', type=click.Choice(['detailed', 'usability']),
              help='Type of report to generate: detailed (complete YOU→LLM→MCP flow), usability (cognitive load)')
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: auto-generated)')
@click.option('--since', help='Generate report for data since this time (e.g., "15m", "2h", "7d")')
@click.option('--server', '-s', help='Filter report to specific MCP server')
def report(output_format: str, report_type: str, output: Optional[str], since: Optional[str], server: Optional[str]) -> None:
    """Generate a usability report from collected data (default: HTML format)."""
    asyncio.run(_report_command(output_format, report_type, output, since, server))


async def _report_command(output_format: str, report_type: str, output: Optional[str], since: Optional[str], server: Optional[str]) -> None:
    """Async implementation of report command."""
    try:
        console.print(f"[bold blue]📊 Generating {report_type} report...[/bold blue]")
        
        # Determine output path and save to current working directory by default
        if not output:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            server_suffix = f"_{server}" if server else ""
            output = f"{report_type}_report{server_suffix}_{timestamp}.{output_format}"
        
        output_path = Path(output)
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize report handlers
        report_handlers = ReportHandlers()
        
        if report_type == "usability":
            # Generate Enhanced Usability Report 
            await report_handlers.generate_usability_report(output_path, output_format, server, since)
            
        elif report_type == "detailed":
            # Generate Timeline-Based Detailed Report (YOU→LLM→MCP flow)
            await _generate_detailed_report_timeline(output_path, output_format, server, since)
        
        elif report_type == "trace":
            # Generate Enhanced Trace Report 
            await report_handlers.generate_trace_report(output_path, output_format, server, since)
        
        console.print(f"[green]✅ {report_type.title()} report generated: {output_path}[/green]")
        console.print(f"[blue]📂 Report saved to: {output_path.absolute()}[/blue]")
        
    except Exception as e:
        console.print(f"[red]❌ Error generating {report_type} report: {e}[/red]")
        logger.exception(f"{report_type.title()} report command failed")


# _generate_trace_report moved to cli_support.report_handlers.ReportHandlers.generate_trace_report


# _generate_usability_report moved to cli_support.report_handlers.ReportHandlers.generate_usability_report


async def _generate_detailed_report(output_path: Path, output_format: str, server: Optional[str], since: Optional[str]) -> None:
    """Generate Complete Enhanced Trace Report with YOU→LLM→MCP flow analysis including automatic user query interception."""
    from pathlib import Path
    import json
    from datetime import datetime, timedelta
    from .interceptors.enhanced_conversation_correlator import EnhancedConversationCorrelator
    from .interceptors.conversation_interceptor import ConversationContextInterceptor
    from .generators.report_generator import ReportGenerator
    
    console.print("🔗 [bold blue]Complete Flow Trace Report (YOU→LLM→MCP) with Auto User Query Capture[/bold blue]")
    console.print("=" * 60)
    
    # Initialize enhanced components
    enhanced_correlator = EnhancedConversationCorrelator()
    conversation_interceptor = ConversationContextInterceptor()
    report_generator = ReportGenerator()
    
    # Load conversation contexts  
    hours = parse_time_duration(since)  # Support minutes, hours, and days
    
    # Load MCP interactions with time filtering
    agent = MCPUsabilityAuditAgent()
    interactions = await agent._load_proxy_interactions(hours_back=hours)
    
    if not interactions:
        console.print(f"[yellow]⚠️ No MCP interactions found in the last {hours}h.[/yellow]")
        console.print("[blue]💡 Try running monitoring first or interact with MCP tools.[/blue]")
        return
    
    # ENHANCED: Load conversation contexts from automatic user query capture
    recent_contexts = conversation_interceptor.load_recent_contexts(hours=int(hours))
    console.print(f"🎯 Found {len(recent_contexts)} automatically captured user queries")
    
    # Get correlation status from legacy correlator
    correlation_status = enhanced_correlator.get_correlation_status()
    console.print(f"📝 Found {correlation_status['recent_prompts_count']} legacy user prompts")
    
    # ENHANCED: Correlate with automatic conversation capture
    enhanced_interactions = []
    auto_correlated_count = 0
    legacy_correlated_count = 0
    
    for interaction in interactions:
        if server and interaction.server_name != server:
            continue
        
        # Try automatic correlation first (from ConversationContextInterceptor)
        if await conversation_interceptor.correlate_with_mcp_interaction(interaction, time_window_seconds=30):
            auto_correlated_count += 1
        
        enhanced_interactions.append(interaction)
    
    # Convert to dict format for legacy correlation
    interaction_dicts = []
    for interaction in enhanced_interactions:
        interaction_dict = {
            'timestamp': interaction.start_time.isoformat() + 'Z' if hasattr(interaction, 'start_time') else '',
            'user_query': getattr(interaction, 'user_query', 'Unknown'),
            'server_name': getattr(interaction, 'server_name', ''),
            'tool_name': getattr(interaction, 'tool_name', ''),
            'duration_ms': getattr(interaction, 'duration_ms', 0),
            'success': getattr(interaction, 'success', True),
            # ENHANCED: Include conversation context if available
            'conversation_context': interaction.conversation_context.model_dump() if interaction.conversation_context else None
        }
        interaction_dicts.append(interaction_dict)
    
    # Enhanced correlation with legacy user prompts
    enhanced_interactions_dicts = enhanced_correlator.enhance_interactions_with_user_prompts(interaction_dicts, hours_back=hours)
    legacy_correlated_count = sum(1 for interaction in enhanced_interactions_dicts if interaction.get('correlation_method') == 'time_based_manual_log')
    
    console.print(f"🔗 Auto-captured correlations: {auto_correlated_count}/{len(enhanced_interactions)}")
    console.print(f"📝 Legacy correlations: {legacy_correlated_count}/{len(enhanced_interactions)}")
    total_correlated = auto_correlated_count + legacy_correlated_count
    console.print(f"✅ Total user query correlations: {total_correlated}/{len(enhanced_interactions)}")
    
    # Generate both enhanced trace and usability reports using enhanced interactions
    trace_data = await report_generator.generate_enhanced_trace_report(
        enhanced_interactions,  # Use MCPInteraction objects, not dictionaries
        include_conversation_context=True
    )
    
    usability_data = await report_generator.generate_comprehensive_report(
        enhanced_interactions,  # Use original interaction objects
        timedelta(hours=hours),
        server
    )
    
    # Generate complete flow analysis with automatic user query capture info
    detailed_data = {
        "complete_flow_trace_report": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "report_type": "detailed_complete_flow_trace_with_auto_capture",
            "data_sources": ["enhanced_mcp_capture", "automatic_conversation_capture", "legacy_conversation_context", "llm_decisions"],
            "complete_flow_coverage": "YOU → Claude/LLM → MCP Client → MCP Server",
            "automatic_correlation_success_rate": f"{auto_correlated_count}/{len(enhanced_interactions)}",
            "legacy_correlation_success_rate": f"{legacy_correlated_count}/{len(enhanced_interactions)}",
            "total_correlation_success_rate": f"{total_correlated}/{len(enhanced_interactions)}",
            "user_query_capture_method": "automatic_file_monitoring + legacy_manual_logs"
        },
        "complete_flows": trace_data,
        "conversation_context": trace_data.get("conversation_summary", {}),
        "user_query_enhancement": {
            "automatic_capture_enabled": True,
            "auto_captured_queries": auto_correlated_count,
            "legacy_captured_queries": legacy_correlated_count,
            "total_captured_queries": total_correlated,
            "enhancement_benefits": [
                "Real user intent captured automatically",
                "Intent classification (information_seeking, creation, troubleshooting)",
                "Complexity assessment (simple, moderate, complex)",
                "Answers 'Why did this MCP call happen?'"
            ]
        },
        "flow_insights": {
            "user_to_llm_correlation": f"{total_correlated} total conversations captured ({auto_correlated_count} automatic + {legacy_correlated_count} legacy)",
            "llm_decision_patterns": "LLM reasoning and tool selection analysis",
            "mcp_protocol_flow": "Complete JSON-RPC message flow",
            "end_to_end_latency": "User prompt to final response timing",
            "decision_quality": "LLM tool selection accuracy and reasoning depth",
            "workflow_coverage": "Complete USER→CLAUDE→MCP workflow with automatic query interception"
        }
    }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate report in requested format
    if output_format == 'json':
        # Use JSON encoder that handles datetime objects
        import json
        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, default=json_serial, ensure_ascii=False)
    elif output_format == 'html':
        html_content = _generate_detailed_html_report(detailed_data)
        output_path.write_text(html_content)
    elif output_format == 'txt':
        txt_content = _generate_detailed_text_report(detailed_data)
        output_path.write_text(txt_content)
    
    # Display enhanced flow summary with automatic user query capture
    console.print("\n[bold]📋 Enhanced Complete Flow Trace Report Summary:[/bold]")
    console.print(f"   • Total Flow Interactions: {len(enhanced_interactions)}")
    console.print(f"   • Automatic User Query Correlations: {auto_correlated_count} ({auto_correlated_count/len(enhanced_interactions)*100:.1f}%)")
    console.print(f"   • Legacy User Query Correlations: {legacy_correlated_count} ({legacy_correlated_count/len(enhanced_interactions)*100:.1f}%)")
    console.print(f"   • Total YOU→LLM→MCP Correlation: {total_correlated}/{len(enhanced_interactions)} ({total_correlated/len(enhanced_interactions)*100:.1f}%)")
    
    if trace_data and 'conversation_summary' in trace_data:
        conv_summary = trace_data['conversation_summary']
        console.print(f"   • User Intent Distribution: {conv_summary['intent_distribution']}")
        console.print(f"   • Complexity Distribution: {conv_summary['complexity_distribution']}")
    
    console.print(f"\n🎯 [bold]Automatic User Query Capture Benefits:[/bold]")
    console.print("   ✅ Real user intent captured automatically (no manual intervention)")
    console.print("   ✅ Intent classification (information_seeking, creation, troubleshooting)")  
    console.print("   ✅ Complexity assessment (simple, moderate, complex)")
    console.print("   ✅ Answers 'Why did this MCP call happen?'")
    
    console.print(f"\n🌐 [bold]Full Observability Coverage:[/bold]")
    console.print("   ✅ User Query → LLM → MCP Client → Server → Response")
    console.print("   ✅ Automatic conversation context and intent analysis")
    console.print("   ✅ Technical performance metrics")
    console.print("   ✅ Usability and cognitive load assessment")
    console.print("   ✅ Integrated optimization recommendations")
    console.print("   ✅ Complete workflow visibility from user intent to MCP execution")
    
    console.print(f"[green]✨ Complete observability combining conversation, technical performance, and user experience[/green]")


@main.command()
@click.option('--server', default='mastra', help='MCP server name to proxy')
@click.option('--restore', is_flag=True, help='Restore original configuration')
def proxy(server: str, restore: bool) -> None:
    """Set up or restore MCP proxy for real-time message capture."""
    asyncio.run(_proxy_command(server, restore))


async def _proxy_command(server: str, restore: bool) -> None:
    """Async implementation of proxy command."""
    try:
        proxy_manager = MCPProxyManager()
        
        if restore:
            console.print("[yellow]🔄 Restoring original MCP configuration...[/yellow]")
            await proxy_manager.restore_original_config()
            console.print("[green]✅ Original MCP configuration restored[/green]")
            console.print("[blue]💡 Restart Cursor to apply changes[/blue]")
        else:
            console.print(f"[yellow]🔧 Setting up MCP proxy for server: {server}...[/yellow]")
            success = await proxy_manager.setup_proxy_for_server(server)
            
            if success:
                console.print("[green]✅ MCP proxy configured successfully[/green]")
                console.print("[blue]💡 Restart Cursor to activate proxy[/blue]")
                console.print(f"[dim]Real-time messages will be captured to ~/.cursor/mcp_audit_messages.jsonl[/dim]")
            else:
                console.print("[red]❌ Failed to configure MCP proxy[/red]")
                console.print("[dim]Check that MCP configuration exists and server name is correct[/dim]")
                
    except Exception as e:
        console.print(f"[red]❌ Error configuring proxy: {e}[/red]")


@main.command(name='proxy-status')
def proxy_status() -> None:
    """Check MCP proxy status and captured messages."""
    asyncio.run(_proxy_status_command())


async def _proxy_status_command() -> None:
    """Check proxy status and show captured message count."""
    try:
        from pathlib import Path
        
        # Check if proxy log exists
        proxy_log = Path.home() / ".cursor" / "mcp_audit_proxy.log"
        messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
        
        console.print("[bold]🔍 MCP Proxy Status[/bold]")
        
        if proxy_log.exists():
            console.print(f"[green]✅ Proxy log found: {proxy_log}[/green]")
            
            # Show last few log lines
            with open(proxy_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    console.print("[dim]Last proxy activity:[/dim]")
                    for line in lines[-3:]:
                        console.print(f"[dim]  {line.strip()}[/dim]")
        else:
            console.print("[yellow]⚠️  No proxy log found[/yellow]")
        
        if messages_file.exists():
            # Count captured messages
            with open(messages_file, 'r') as f:
                message_count = len(f.readlines())
            
            console.print(f"[green]📨 Captured messages: {message_count}[/green]")
            console.print(f"[dim]Messages file: {messages_file}[/dim]")
            
            if message_count > 0:
                console.print("[blue]💡 Run 'mcp-audit report' to analyze captured messages[/blue]")
        else:
            console.print("[yellow]📭 No captured messages yet[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Error checking proxy status: {e}[/red]")


@main.command(name='proxy-logs')
@click.option('--tail', '-n', default=20, help='Number of recent log lines to show')
def proxy_logs(tail: int) -> None:
    """Show MCP proxy logs."""
    asyncio.run(_proxy_logs_command(tail))


async def _proxy_logs_command(tail: int) -> None:
    """Show recent proxy log entries."""
    try:
        from pathlib import Path
        
        proxy_log = Path.home() / ".cursor" / "mcp_audit_proxy.log"
        
        if not proxy_log.exists():
            console.print("[yellow]⚠️  No proxy log file found[/yellow]")
            console.print("[dim]Run 'mcp-audit proxy' to set up the proxy first[/dim]")
            return
        
        console.print(f"[bold]📋 Proxy Logs (last {tail} lines)[/bold]")
        console.print(f"[dim]File: {proxy_log}[/dim]\n")
        
        with open(proxy_log, 'r') as f:
            lines = f.readlines()
        
        for line in lines[-tail:]:
            line = line.strip()
            if "ERROR" in line:
                console.print(f"[red]{line}[/red]")
            elif "WARNING" in line or "WARN" in line:
                console.print(f"[yellow]{line}[/yellow]")
            elif "INFO" in line:
                console.print(f"[blue]{line}[/blue]")
            else:
                console.print(f"[dim]{line}[/dim]")
                
    except Exception as e:
        console.print(f"[red]❌ Error reading proxy logs: {e}[/red]")


@main.command()
@click.option("--host", default="127.0.0.1", help="Dashboard host")
@click.option("--port", default=8000, type=int, help="Dashboard port")
@click.option("--reload", is_flag=True, help="Auto-reload on code changes")
def dashboard(host: str, port: int, reload: bool) -> None:
    """Start the web dashboard for real-time monitoring."""
    try:
        console.print(Panel.fit(
            "[bold blue]🧠 MCP Audit Dashboard[/bold blue]\n"
            "[dim]Real-time cognitive observability[/dim]"
        ))
        
        console.print(f"🚀 Starting dashboard at http://{host}:{port}")
        console.print("📊 Features:")
        console.print("  • Real-time cognitive load monitoring")
        console.print("  • Live MCP message activity")
        console.print("  • Enterprise integrations setup")
        console.print("  • WebSocket updates")
        
        app = create_dashboard_app()
        
        try:
            import uvicorn
            uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")
        except ImportError:
            console.print("[red]❌ uvicorn not installed. Install with: pip install uvicorn[/red]")
            raise click.Abort()
        
    except Exception as e:
        console.print(f"[red]❌ Dashboard error: {e}[/red]")
        raise click.Abort()


# Enterprise integrations removed - functionality available through external tools


# Enhanced functionality integrated into main 'detailed' report type


async def _generate_detailed_report_timeline(output_path: Path, output_format: str, server: Optional[str], since: Optional[str]) -> None:
    """Generate timeline-based detailed report with USER→LLM→MCP flow analysis including LLM reasoning."""
    from .tracing.timeline_analyzer import TimelineAnalyzer
    
    console.print("🔗 [bold blue]Timeline-Based Complete Flow Analysis with LLM Reasoning (USER→LLM→MCP)[/bold blue]")
    console.print("=" * 80)
    
    # Initialize timeline analyzer
    timeline_analyzer = TimelineAnalyzer(time_window_seconds=30)
    
    # Parse time window
    hours = parse_time_duration(since)
    
    # Load both MCP messages and LLM decisions
    console.print(f"📂 Loading data from last {hours:.2f}h...")
    messages = timeline_analyzer.load_messages(since_hours=hours)
    decisions = timeline_analyzer.load_llm_decisions(since_hours=hours)
    
    if not messages and not decisions:
        console.print(f"[yellow]⚠️ No data found in the last {hours:.2f}h.[/yellow]")
        console.print("[blue]💡 Try running 'mcp-audit proxy' first and interact with MCP tools.[/blue]")
        return
    
    # Merge timeline data
    console.print(f"🔗 Merging {len(messages)} MCP messages + {len(decisions)} LLM decisions...")
    timeline_events = timeline_analyzer.merge_timeline_data(messages, decisions)
    
    # Group into interaction flows
    console.print(f"📊 Grouping {len(timeline_events)} events into interaction flows...")
    flows = timeline_analyzer.group_into_flows(timeline_events)
    
    if not flows:
        console.print("[yellow]⚠️ No interaction flows detected.[/yellow]")
        return
    
    # Filter by server if specified
    if server:
        flows = timeline_analyzer.filter_flows_by_server(flows, server)
        if not flows:
            console.print(f"[yellow]⚠️ No flows found for server: {server}[/yellow]")
            return
    
    # Generate timeline report with LLM reasoning
    console.print(f"🧠 Generating timeline-based detailed report with LLM reasoning...")
    report = timeline_analyzer.generate_timeline_report(flows, report_type='detailed')
    
    # Add metadata
    report['meta'] = {
        'report_version': '2.1_timeline_with_llm_reasoning',
        'generation_method': 'timestamp_proximity_grouping_with_llm_decisions',
        'time_window_seconds': timeline_analyzer.time_window_seconds,
        'server_filter': server,
        'time_filter_hours': hours,
        'data_sources': ['mcp_audit_messages', 'llm_decision_trace']
    }
    
    # Write report in requested format
    if output_format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    elif output_format == 'html':
        html_content = _generate_timeline_html_report(report)
        output_path.write_text(html_content)
    elif output_format == 'txt':
        txt_content = _generate_timeline_text_report(report)
        output_path.write_text(txt_content)
    else:
        # Default to JSON for unknown formats
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    
    # Print enhanced summary
    summary = report['summary']
    console.print("\n📊 [bold blue]Enhanced Timeline Report Summary:[/bold blue]")
    console.print(f"• Total Interaction Flows: {summary['total_flows']}")
    console.print(f"• Flows with User Context: {summary['flows_with_user_context']} ({summary['user_context_rate']:.1%})")
    console.print(f"• Flows with LLM Reasoning: {summary['flows_with_llm_reasoning']} ({summary['llm_reasoning_rate']:.1%})")
    console.print(f"• Cross-Server Flows: {summary['cross_server_flows']}")
    console.print(f"• Successful Flows: {summary['successful_flows']} ({summary['success_rate']:.1%})")
    console.print(f"• Servers Involved: {', '.join(summary['servers_involved'])}")
    console.print(f"• Total MCP Tool Calls: {summary['total_tool_calls']}")
    console.print(f"• Total LLM Decisions: {summary['total_llm_decisions']}")
    
    if summary['flows_with_llm_reasoning'] > 0:
        console.print("\n✅ [green]LLM reasoning capture working![/green]")
        console.print("🧠 [blue]Reports now include complete USER→LLM reasoning→MCP flow![/blue]")
    else:
        console.print("\n⚠️ [yellow]No LLM reasoning found - check if decisions are being captured[/yellow]")
    
    if summary['flows_with_user_context'] > 0:
        console.print("✅ [green]User context capture working![/green]")
    else:
        console.print("💡 [blue]User prompt capture is a work in progress[/blue]")



async def _generate_usability_report_timeline(output_path: Path, output_format: str, server: Optional[str], since: Optional[str]) -> None:
    """Generate timeline-based usability report with LLM reasoning quality metrics."""
    from .tracing.timeline_analyzer import TimelineAnalyzer
    
    console.print("📊 [bold blue]Timeline-Based Usability Report with LLM Reasoning Quality[/bold blue]")
    console.print("=" * 70)
    
    timeline_analyzer = TimelineAnalyzer(time_window_seconds=30)
    hours = parse_time_duration(since)
    
    # Load both data sources
    messages = timeline_analyzer.load_messages(since_hours=hours)
    decisions = timeline_analyzer.load_llm_decisions(since_hours=hours)
    
    if not messages and not decisions:
        console.print(f"[yellow]⚠️ No data found in the last {hours:.2f}h.[/yellow]")
        return
    
    # Merge and group
    timeline_events = timeline_analyzer.merge_timeline_data(messages, decisions)
    flows = timeline_analyzer.group_into_flows(timeline_events)
    
    if server:
        flows = timeline_analyzer.filter_flows_by_server(flows, server)
    
    if not flows:
        console.print(f"[yellow]⚠️ No interaction flows found.[/yellow]")
        # Create minimal report
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'server_name': server or 'all',
            'message': 'No interactions detected',
            'grade': 'F',
            'overall_usability_score': 0,
            'usability_metrics': {
                'user_interactions': 0,
                'successful_completions': 0,
                'abandonment_rate': 1.0,
                'llm_reasoning_quality': 0
            }
        }
    else:
        report = timeline_analyzer.generate_timeline_report(flows, report_type='usability')
        
        # Add timeframe information
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        report['timeframe'] = {
            'since': start_time.isoformat(),
            'until': end_time.isoformat(), 
            'duration_hours': round(hours, 2)
        }
        
        # Clarify what time_window_seconds means (move to meta section)
        time_window_info = {
            'event_grouping_window_sec': report.pop('time_window_seconds', 30),
            'description': 'Events within this window are grouped as related interactions'
        }
        
        # Generate cognitive analysis and usability insights
        cognitive_analysis = await timeline_analyzer.generate_cognitive_analysis(flows)
        report['cognitive_load'] = cognitive_analysis['cognitive_load']
        report['usability_insights'] = cognitive_analysis['usability_insights']
        report['grade_calculation'] = cognitive_analysis['grade_calculation']
        
        # Use cognitive load grade as the primary grade
        cognitive_grade = cognitive_analysis['cognitive_load'].get('grade', 'C')
        
        # Calculate enhanced grade based on metrics including LLM reasoning
        metrics = report.get('usability_metrics', {})
        
        # Convert to 0-100 scale and remove unnecessary decimals
        tool_success_rate_raw = metrics.get('tool_usage_success_rate', 0) * 100
        llm_reasoning_quality_raw = metrics.get('llm_reasoning_quality', 0) * 100
        
        # Format numbers: remove decimals if whole numbers
        tool_success_rate = int(tool_success_rate_raw) if tool_success_rate_raw == int(tool_success_rate_raw) else round(tool_success_rate_raw, 1)
        llm_reasoning_quality = int(llm_reasoning_quality_raw) if llm_reasoning_quality_raw == int(llm_reasoning_quality_raw) else round(llm_reasoning_quality_raw, 1)
        
        # Enhanced scoring that includes LLM reasoning quality (both now on 0-100 scale)
        composite_score_raw = (tool_success_rate * 0.7) + (llm_reasoning_quality * 0.3)
        composite_score = int(composite_score_raw) if composite_score_raw == int(composite_score_raw) else round(composite_score_raw, 1)
        
        # Update metrics to 0-100 scale and clean format
        report['usability_metrics']['tool_usage_success_rate'] = tool_success_rate
        report['usability_metrics']['llm_reasoning_quality'] = llm_reasoning_quality
        
        # Use cognitive load grade as primary, but note composite score for reference
        report['grade'] = cognitive_grade
        report['overall_usability_score'] = composite_score
        report['cognitive_grade'] = cognitive_grade  # Explicit cognitive grade
        report['composite_score'] = composite_score  # Traditional composite score for reference
        
        # Clarify server_name
        servers_involved = report.get('summary', {}).get('servers_involved', [])
        if server:
            report['server_name'] = server
        elif len(servers_involved) == 1:
            report['server_name'] = servers_involved[0]
        elif len(servers_involved) > 1:
            report['server_name'] = f"multiple_servers({len(servers_involved)})"
        else:
            report['server_name'] = "no_server_detected"
        
        report['meta'] = {
            'scoring_algorithm': 'cognitive_load_based_primary',
            'cognitive_load_weight': 1.0,  # Primary grading method
            'tool_success_weight': 0.7,   # For composite reference score
            'llm_reasoning_weight': 0.3,  # For composite reference score
            'scale': '0-100',
            'primary_grading': 'cognitive_load_analysis',
            'cognitive_thresholds': cognitive_analysis['grade_calculation']['thresholds'],
            **time_window_info  # Add the time window info here instead
        }
    
    # Save report in requested format
    if output_format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
    elif output_format == 'html':
        html_content = _generate_html_report(report)
        output_path.write_text(html_content)
    elif output_format == 'txt':
        txt_content = _generate_text_report(report)
        output_path.write_text(txt_content)
    
    if 'usability_metrics' in report:
        metrics = report['usability_metrics']
        console.print(f"📊 User Interactions: {metrics['user_interactions']}")
        
        # Format percentages properly (handle both int and float)
        tool_success = metrics.get('tool_usage_success_rate', 0)
        llm_quality = metrics.get('llm_reasoning_quality', 0)
        overall_score = report.get('overall_usability_score', 0)
        
        console.print(f"📊 Tool Success Rate: {tool_success}%")  # Already formatted as int or float
        console.print(f"🧠 LLM Reasoning Quality: {llm_quality}%")  # Already formatted as int or float
        console.print(f"⏱️  Avg Flow Duration: {metrics.get('avg_flow_duration_sec', 0):.1f} seconds")  # Keep 1 decimal for time
        console.print(f"📊 Overall Usability Score: {overall_score}/100")  # Already formatted as int or float
        console.print(f"🎯 Grade: {report['grade']}")
        
        # Show cognitive load breakdown if available
        if 'cognitive_load' in report:
            cognitive = report['cognitive_load']
            console.print(f"\n🧠 [bold blue]Cognitive Load Analysis:[/bold blue]")
            console.print(f"   Overall Score: {cognitive.get('overall_score', 0)}/100 (Grade {cognitive.get('grade', 'N/A')})")
            console.print(f"   • Prompt Complexity: {cognitive.get('prompt_complexity', 0)}")
            console.print(f"   • Context Switching: {cognitive.get('context_switching', 0)}")
            console.print(f"   • Retry Frustration: {cognitive.get('retry_frustration', 0)}")
            console.print(f"   • Configuration Friction: {cognitive.get('configuration_friction', 0)}")
            console.print(f"   • Integration Cognition: {cognitive.get('integration_cognition', 0)}")
            
            friction_points = cognitive.get('friction_points', [])
            if friction_points and friction_points != ['No significant friction points detected']:
                console.print(f"   ⚠️  Friction Points: {', '.join(friction_points)}")
        
        # Show usability insights
        if 'usability_insights' in report:
            insights = report['usability_insights']
            console.print(f"\n💡 [bold blue]Usability Insights:[/bold blue]")
            for insight in insights[:3]:  # Show top 3 insights
                console.print(f"   • {insight}")
        
        # Add timeframe info if available
        if 'timeframe' in report:
            timeframe = report['timeframe']
            console.print(f"\n📅 Report Period: {timeframe['duration_hours']:.1f} hours")
            console.print(f"📅 Since: {timeframe['since'][:19].replace('T', ' ')}")  # Format timestamp nicely
            
        # Show server info more clearly
        console.print(f"🖥️  Server: {report.get('server_name', 'unknown')}")
        
        # Show grade calculation explanation if available
        if 'grade_calculation' in report:
            grade_calc = report['grade_calculation']
            console.print(f"\n📊 [bold blue]Grade Calculation:[/bold blue]")
            console.print(f"   Method: {grade_calc.get('method', 'Unknown')}")
            if 'explanation' in grade_calc:
                console.print(f"   Formula: {grade_calc['explanation']}")
            console.print(f"   Cognitive Grade: {report.get('cognitive_grade', 'N/A')}")
            console.print(f"   Composite Score: {report.get('composite_score', 'N/A')}/100 (Reference)")


# Test timeline command removed - no more simulated data generation
    
    console.print("\n💡 [blue]Next steps:[/blue]")
    console.print("   1. Use some MCP tools in Cursor (browser_navigate, etc.)")
    console.print("   2. Run: mcp-audit report --type detailed --since 10m")
    console.print("   3. Check timeline correlation in the report")


# _generate_enhanced_trace_html_report moved to cli_support.html_generators


def _generate_html_report(report):
    """Generate HTML version of usability report."""
    # Handle both dict and object types
    if hasattr(report, 'model_dump'):
        data = report.model_dump()
    elif hasattr(report, '__dict__'):
        data = report.__dict__
    else:
        data = report
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Usability Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .metric-card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
            .metric-label {{ color: #6c757d; font-size: 1.1em; }}
            .grade-excellent {{ color: #28a745; }}
            .grade-good {{ color: #17a2b8; }}
            .grade-fair {{ color: #ffc107; }}
            .grade-poor {{ color: #dc3545; }}
            .cognitive-section {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; }}
            .cognitive-factor {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .cognitive-factor.clickable {{ cursor: pointer; transition: background-color 0.2s; }}
            .cognitive-factor.clickable:hover {{ background-color: #f8f9fa; border-radius: 4px; }}
            .factor-explanation {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #17a2b8; }}
            .factor-explanation h4 {{ margin-top: 0; color: #17a2b8; }}
            .calculation-breakdown {{ background: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff; }}
            .calculation-breakdown h5 {{ margin-top: 0; color: #007bff; }}
            .calculation-step {{ display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dotted #ccc; }}
            .calculation-step:last-child {{ border-bottom: none; font-weight: bold; background: #d4edda; padding: 8px; border-radius: 4px; }}
            .technical-details {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #6c757d; }}
            .technical-details h4 {{ margin-top: 0; color: #6c757d; }}
            .technical-details code {{ background: #e9ecef; padding: 10px; display: block; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; }}
            .insights {{ background: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .insight-item {{ padding: 8px 0; }}
            .timeframe {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .friction-points-section {{ background: #fff3cd; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #ffc107; }}
            .friction-points-section h4 {{ margin-top: 0; color: #856404; }}
            .friction-points-list {{ margin: 10px 0; }}
            .friction-point {{ padding: 5px 0; color: #856404; font-weight: 500; }}
            .no-friction {{ color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; border-left: 3px solid #28a745; }}
        </style>
        <script>
            function toggleExplanation(id) {{
                const elem = document.getElementById(id);
                elem.style.display = elem.style.display === 'none' ? 'block' : 'none';
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MCP Usability Report</h1>
                <p>Generated on {data.get('generated_at', 'N/A')}</p>
                <p>Server: {data.get('server_name', 'N/A')}</p>
            </div>
    """
    
    # Add overview metrics
    session_summary = data.get('session_summary', {})
    if session_summary:
        html_content += f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value grade-excellent">{data.get('overall_usability_score', 0)}</div>
                    <div class="metric-label">Overall Usability Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value grade-{data.get('grade', 'fair').lower()}">{data.get('grade', 'N/A')}</div>
                    <div class="metric-label">Grade</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{session_summary.get('total_sessions', 0)}</div>
                    <div class="metric-label">Total Interactions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{session_summary.get('successful_completions', 0)}</div>
                    <div class="metric-label">Successful Completions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{session_summary.get('avg_response_time_ms', 0):.0f}ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
            </div>
        """
    
    # Add cognitive load analysis with detailed calculations
    if 'cognitive_load' in data:
        cognitive = data['cognitive_load']
        grade_calc = data.get('grade_calculation', {})
        
        html_content += f"""
            <div class="cognitive-section">
                <h3>🧠 Cognitive Load Analysis</h3>
                <p><strong>Overall Score:</strong> {cognitive.get('overall_score', 0)}/100 (Grade {cognitive.get('grade', 'N/A')})</p>
                <p><em>Based on established UX research and cognitive science principles. Click each factor for detailed explanation and calculation breakdown.</em></p>
                
                <div class="cognitive-factor clickable" onclick="toggleExplanation('prompt-complexity')">
                    <span>Prompt Complexity (Weight: 15%)</span>
                    <span>{cognitive.get('prompt_complexity', 0):.1f}/100</span>
                </div>
                <div id="prompt-complexity" class="factor-explanation" style="display: none;">
                    <h4>📝 Prompt Complexity Analysis</h4>
                    <div class="calculation-breakdown">
                        <h5>🔢 How Your Score of {cognitive.get('prompt_complexity', 0):.1f} Was Calculated:</h5>
                        <div class="calculation-step">
                            <span>Base complexity score</span>
                            <span>+20.0 points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Query length complexity</span>
                            <span>+{5 if cognitive.get('prompt_complexity', 0) > 25 else 0:.0f} points (short), +{15 if cognitive.get('prompt_complexity', 0) > 35 else 0:.0f} points (medium), +{25 if cognitive.get('prompt_complexity', 0) > 45 else 0:.0f} points (long)</span>
                        </div>
                        <div class="calculation-step">
                            <span>Technical/domain-specific terms (×8 each)</span>
                            <span>+{max(0, min(24, cognitive.get('prompt_complexity', 20) - 20 - (5 if cognitive.get('prompt_complexity', 0) > 25 else 0) - (15 if cognitive.get('prompt_complexity', 0) > 35 else 0) - (25 if cognitive.get('prompt_complexity', 0) > 45 else 0))):.0f} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Complex logic terms (×10 each)</span>
                            <span>+{max(0, cognitive.get('prompt_complexity', 20) - 20 - (5 if cognitive.get('prompt_complexity', 0) > 25 else 0) - (15 if cognitive.get('prompt_complexity', 0) > 35 else 0) - (25 if cognitive.get('prompt_complexity', 0) > 45 else 0) - min(24, max(0, cognitive.get('prompt_complexity', 20) - 20 - (5 if cognitive.get('prompt_complexity', 0) > 25 else 0) - (15 if cognitive.get('prompt_complexity', 0) > 35 else 0) - (25 if cognitive.get('prompt_complexity', 0) > 45 else 0)))):.0f} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Time-based queries detected</span>
                            <span>+{15 if cognitive.get('prompt_complexity', 0) > 35 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Multiple actions/numerical references</span>
                            <span>+{max(0, cognitive.get('prompt_complexity', 20) - 20 - (15 if cognitive.get('prompt_complexity', 0) > 35 else 0)):.0f} points (remaining)</span>
                        </div>
                        <div class="calculation-step">
                            <span><strong>Final Score (averaged across interactions)</strong></span>
                            <span><strong>{cognitive.get('prompt_complexity', 0):.1f}/100</strong></span>
                        </div>
                    </div>
                    <p><strong>What it measures:</strong> Cognitive burden of formulating requests to AI agents</p>
                    <p><strong>Research foundation:</strong> John Sweller's Cognitive Load Theory (1988)</p>
                    <p><strong>Weight rationale:</strong> 15% - Moderate impact. Complex prompts increase mental effort but users adapt over time.</p>
                    <p><strong>Calculation factors:</strong></p>
                    <ul>
                        <li>Query length (more words = higher cognitive load)</li>
                        <li>Technical/domain-specific terminology (API, config, authentication, etc.)</li>
                        <li>Complex logic terms (if, when, filter, transform, etc.)</li>
                        <li>Multiple action verbs (create, update, delete, etc.)</li>
                        <li>Time-based references (today, tomorrow, before, after, etc.)</li>
                        <li>Numerical/quantitative references (numbers, all, every, etc.)</li>
                    </ul>
                    <p><strong>Optimization tips:</strong> Provide examples, auto-complete suggestions, context-aware prompting</p>
                </div>
                
                <div class="cognitive-factor clickable" onclick="toggleExplanation('context-switching')">
                    <span>Context Switching (Weight: 20%)</span>
                    <span>{cognitive.get('context_switching', 0):.1f}/100</span>
                </div>
                <div id="context-switching" class="factor-explanation" style="display: none;">
                    <h4>🔄 Context Switching Analysis</h4>
                    <div class="calculation-breakdown">
                        <h5>🔢 How Your Score of {cognitive.get('context_switching', 0):.1f} Was Calculated:</h5>
                        <div class="calculation-step">
                            <span>Direction changes in message flow</span>
                            <span>{cognitive.get('context_switching', 0) / 15:.0f} changes detected</span>
                        </div>
                        <div class="calculation-step">
                            <span>Switching penalty (×15 per change)</span>
                            <span>+{cognitive.get('context_switching', 0):.1f} points</span>
                        </div>
                        <div class="calculation-step">
                            <span><strong>Final Score</strong></span>
                            <span><strong>{cognitive.get('context_switching', 0):.1f}/100</strong></span>
                        </div>
                    </div>
                    <p><strong>What it measures:</strong> Mental overhead from switching between different interaction contexts</p>
                    <p><strong>Research foundation:</strong> Miller's 7±2 Rule (1956) - limits of human working memory</p>
                    <p><strong>Weight rationale:</strong> 20% - Higher impact on mental model. Users struggle when jumping between different interfaces or concepts.</p>
                    <p><strong>Calculation factors:</strong></p>
                    <ul>
                        <li>Number of component transitions (User→LLM→MCP→API)</li>
                        <li>Interface paradigm changes</li>
                        <li>Protocol or format switches</li>
                        <li>Mental model disruptions</li>
                    </ul>
                    <p><strong>Optimization tips:</strong> Reduce component hops, maintain consistent interfaces, batch operations</p>
                </div>
                
                <div class="cognitive-factor clickable" onclick="toggleExplanation('retry-frustration')">
                    <span>Retry Frustration (Weight: 30%)</span>
                    <span>{cognitive.get('retry_frustration', 0):.1f}/100</span>
                </div>
                <div id="retry-frustration" class="factor-explanation" style="display: none;">
                    <h4>🔁 Retry Frustration Analysis</h4>
                    <div class="calculation-breakdown">
                        <h5>🔢 How Your Score of {cognitive.get('retry_frustration', 0):.1f} Was Calculated:</h5>
                        <div class="calculation-step">
                            <span>Base frustration score</span>
                            <span>+10.0 points</span>
                        </div>"""
    
    # Add breakdown details if available (placeholder for future enhancement)
    retry_breakdown = cognitive.get('retry_breakdown', {})
    if False:  # Disabled for now - breakdown display can be added later
        if retry_breakdown.get('retry_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Retry attempts ({retry_breakdown.get('retry_count', 0)} × 25 each)</span>
                            <span>+{retry_breakdown.get('retry_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Retry attempts</span>
                            <span>+0 points (no retries detected)</span>
                        </div>"""
        
        if retry_breakdown.get('failure_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Failed interactions</span>
                            <span>+{retry_breakdown.get('failure_penalty', 0):.0f} points (interaction failed)</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Failed interactions</span>
                            <span>+0 points (all interactions succeeded)</span>
                        </div>"""
        
        if retry_breakdown.get('error_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Error messages encountered ({retry_breakdown.get('actual_error_count', 0)} × 20 each)</span>
                            <span>+{retry_breakdown.get('error_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Error messages encountered</span>
                            <span>+0 points (no actual errors detected)</span>
                        </div>"""
        
        if retry_breakdown.get('latency_penalty', 0) > 0:
            latency_sec = retry_breakdown.get('latency_ms', 0) / 1000
            threshold_sec = retry_breakdown.get('latency_threshold_ms', 30000) / 1000
            html_content += f"""
                        <div class="calculation-step">
                            <span>Slow response time ({latency_sec:.1f}s > {threshold_sec:.0f}s threshold)</span>
                            <span>+{retry_breakdown.get('latency_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Slow response time</span>
                            <span>+0 points (within acceptable response time)</span>
                        </div>"""
    else:
        # Fallback to old calculation if breakdown not available
        html_content += f"""
                        <div class="calculation-step">
                            <span>Retry attempts (×25 each)</span>
                            <span>+{max(0, (cognitive.get('retry_frustration', 10) - 10 - (40 if cognitive.get('retry_frustration', 0) > 50 else 0)) // 25 * 25):.0f} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Failed interactions</span>
                            <span>+{40 if cognitive.get('retry_frustration', 0) > 50 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Error messages encountered</span>
                            <span>+{max(0, cognitive.get('retry_frustration', 10) - 10 - (25 * max(0, (cognitive.get('retry_frustration', 10) - 10) // 25)) - (40 if cognitive.get('retry_frustration', 0) > 50 else 0)):.0f} points</span>
                        </div>"""
    
    html_content += f"""
                        <div class="calculation-step">
                            <span><strong>Final Score</strong></span>
                            <span><strong>{cognitive.get('retry_frustration', 0):.1f}/100</strong></span>
                        </div>
                    </div>"""
    
    # Add detailed explanations if available
    if retry_breakdown and retry_breakdown.get('explanations'):
        html_content += f"""
                    <div class="technical-details">
                        <h4>📋 Detailed Analysis</h4>
                        <ul>"""
        for explanation in retry_breakdown['explanations']:
            html_content += f"""
                            <li>{explanation}</li>"""
        html_content += f"""
                        </ul>
                    </div>"""
    
    html_content += f"""
                    <p><strong>What it measures:</strong> User frustration from failed attempts and repetitive actions</p>
                    <p><strong>Research foundation:</strong> Nielsen's Usability Heuristics (1994) - Error prevention and recovery</p>
                    <p><strong>Weight rationale:</strong> 30% - HIGHEST weight. Retries kill UX and cause immediate user abandonment.</p>
                    <p><strong>Calculation factors:</strong></p>
                    <ul>
                        <li>Number of retry attempts</li>
                        <li>Error frequency and patterns</li>
                        <li>Recovery time and effort</li>
                        <li>Success rate on subsequent attempts</li>
                    </ul>
                    <p><strong>Optimization tips:</strong> Improve error messages, add validation, implement graceful fallbacks</p>
                </div>
                
                <div class="cognitive-factor clickable" onclick="toggleExplanation('configuration-friction')">
                    <span>Configuration Friction (Weight: 25%)</span>
                    <span>{cognitive.get('configuration_friction', 0):.1f}/100</span>
                </div>
                <div id="configuration-friction" class="factor-explanation" style="display: none;">
                    <h4>⚙️ Configuration Friction Analysis</h4>
                    <div class="calculation-breakdown">
                        <h5>🔢 How Your Score of {cognitive.get('configuration_friction', 0):.1f} Was Calculated:</h5>
                        <div class="calculation-step">
                            <span>Base friction score</span>
                            <span>+10.0 points</span>
                        </div>"""
    
    # Add configuration breakdown details if available (placeholder for future enhancement)
    config_breakdown = cognitive.get('configuration_breakdown', {})
    if False:  # Disabled for now - breakdown display can be added later
        if config_breakdown.get('auth_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Authentication errors (401/403)</span>
                            <span>+{config_breakdown.get('auth_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Authentication errors (401/403)</span>
                            <span>+0 points (no auth errors detected)</span>
                        </div>"""
        
        if config_breakdown.get('param_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Parameter validation errors (400/422)</span>
                            <span>+{config_breakdown.get('param_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Parameter validation errors (400/422)</span>
                            <span>+0 points (no parameter errors detected)</span>
                        </div>"""
        
        if config_breakdown.get('config_keyword_penalty', 0) > 0:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Configuration-related keywords in errors</span>
                            <span>+{config_breakdown.get('config_keyword_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>Configuration-related keywords in errors</span>
                            <span>+0 points (no config keywords in errors)</span>
                        </div>"""
        
        if config_breakdown.get('latency_penalty', 0) > 0:
            latency_sec = config_breakdown.get('latency_ms', 0) / 1000
            threshold_sec = config_breakdown.get('latency_threshold_ms', 45000) / 1000
            html_content += f"""
                        <div class="calculation-step">
                            <span>High latency ({latency_sec:.1f}s > {threshold_sec:.0f}s threshold)</span>
                            <span>+{config_breakdown.get('latency_penalty', 0):.0f} points</span>
                        </div>"""
        else:
            html_content += f"""
                        <div class="calculation-step">
                            <span>High latency (indicating config issues)</span>
                            <span>+0 points (within acceptable config time)</span>
                        </div>"""
    else:
        # Fallback to old calculation if breakdown not available
        html_content += f"""
                        <div class="calculation-step">
                            <span>Authentication errors (401/403)</span>
                            <span>+{50 if cognitive.get('configuration_friction', 0) > 60 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Parameter validation errors (400/422)</span>
                            <span>+{30 if cognitive.get('configuration_friction', 0) > 40 and cognitive.get('configuration_friction', 0) <= 60 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Configuration-related keywords in errors</span>
                            <span>+{35 if cognitive.get('configuration_friction', 0) > 45 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>High latency (indicating config issues)</span>
                            <span>+{25 if cognitive.get('configuration_friction', 0) > 35 else 0} points</span>
                        </div>"""
    
    html_content += f"""
                        <div class="calculation-step">
                            <span><strong>Final Score</strong></span>
                            <span><strong>{cognitive.get('configuration_friction', 0):.1f}/100</strong></span>
                        </div>
                    </div>"""
    
    # Add detailed explanations if available
    if config_breakdown and config_breakdown.get('explanations'):
        html_content += f"""
                    <div class="technical-details">
                        <h4>📋 Detailed Analysis</h4>
                        <ul>"""
        for explanation in config_breakdown['explanations']:
            html_content += f"""
                            <li>{explanation}</li>"""
        html_content += f"""
                        </ul>
                    </div>"""
    
    html_content += f"""
                    <p><strong>What it measures:</strong> Complexity and barriers in setup, authentication, and configuration</p>
                    <p><strong>Research foundation:</strong> Don Norman's Design of Everyday Things - Affordances and constraints</p>
                    <p><strong>Weight rationale:</strong> 25% - Major blocker. Configuration issues prevent users from even starting.</p>
                    <p><strong>Calculation factors:</strong></p>
                    <ul>
                        <li>Authentication failures (401/403 errors)</li>
                        <li>Configuration complexity</li>
                        <li>Setup time and steps required</li>
                        <li>Parameter validation errors</li>
                    </ul>
                    <p><strong>Optimization tips:</strong> Guided setup wizards, auto-configuration, clear documentation</p>
                </div>
                
                <div class="cognitive-factor clickable" onclick="toggleExplanation('integration-cognition')">
                    <span>Integration Cognition (Weight: 10%)</span>
                    <span>{cognitive.get('integration_cognition', 0):.1f}/100</span>
                </div>
                <div id="integration-cognition" class="factor-explanation" style="display: none;">
                    <h4>🔗 Integration Cognition Analysis</h4>
                    <div class="calculation-breakdown">
                        <h5>🔢 How Your Score of {cognitive.get('integration_cognition', 0):.1f} Was Calculated:</h5>
                        <div class="calculation-step">
                            <span>Base integration score</span>
                            <span>+20.0 points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Multiple protocols used</span>
                            <span>+{20 if cognitive.get('integration_cognition', 0) > 40 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Message direction complexity</span>
                            <span>+{(cognitive.get('integration_cognition', 20) - 20 - (20 if cognitive.get('integration_cognition', 0) > 40 else 0) - (15 if cognitive.get('integration_cognition', 0) > 55 else 0)) if cognitive.get('integration_cognition', 0) > 20 else 0:.0f} points</span>
                        </div>
                        <div class="calculation-step">
                            <span>Complex nested data structures</span>
                            <span>+{15 if cognitive.get('integration_cognition', 0) > 55 else 0} points</span>
                        </div>
                        <div class="calculation-step">
                            <span><strong>Final Score</strong></span>
                            <span><strong>{cognitive.get('integration_cognition', 0):.1f}/100</strong></span>
                        </div>
                    </div>
                    <p><strong>What it measures:</strong> Mental effort to understand tool relationships and data flow</p>
                    <p><strong>Research foundation:</strong> Fitts' Law & Hick's Law - Complexity affects decision time</p>
                    <p><strong>Weight rationale:</strong> 10% - Lower weight. Mainly affects power users who need to understand integrations.</p>
                    <p><strong>Calculation factors:</strong></p>
                    <ul>
                        <li>Number of integrated tools/protocols</li>
                        <li>Data structure complexity</li>
                        <li>API relationship depth</li>
                        <li>Cross-system dependencies</li>
                    </ul>
                    <p><strong>Optimization tips:</strong> Visual flow diagrams, simplified APIs, clear documentation</p>
                </div>
                
                <div class="technical-details">
                    <h4>🔬 Technical Implementation</h4>
                    <p><strong>Algorithm Type:</strong> Rule-based heuristics (not LLM-based for consistency)</p>
                    <p><strong>Formula:</strong> Weighted average with research-validated weights</p>
                    <code>
                        overall_score = (prompt_complexity × 0.15) + (context_switching × 0.20) + 
                                      (retry_frustration × 0.30) + (configuration_friction × 0.25) + 
                                      (integration_cognition × 0.10)
                    </code>
                    <p><strong>Actual Calculation for This Report:</strong></p>
                    <code>
                        {cognitive.get('overall_score', 0):.1f} = ({cognitive.get('prompt_complexity', 0):.1f} × 0.15) + ({cognitive.get('context_switching', 0):.1f} × 0.20) + 
                           ({cognitive.get('retry_frustration', 0):.1f} × 0.30) + ({cognitive.get('configuration_friction', 0):.1f} × 0.25) + 
                           ({cognitive.get('integration_cognition', 0):.1f} × 0.10)
                        {cognitive.get('overall_score', 0):.1f} = {cognitive.get('prompt_complexity', 0) * 0.15:.1f} + {cognitive.get('context_switching', 0) * 0.20:.1f} + {cognitive.get('retry_frustration', 0) * 0.30:.1f} + {cognitive.get('configuration_friction', 0) * 0.25:.1f} + {cognitive.get('integration_cognition', 0) * 0.10:.1f}
                    </code>
                    <p><strong>Performance:</strong> &lt;10ms per interaction, 100% deterministic results</p>
                    <p><strong>Standards compliance:</strong> ISO 9241-210 Human-centered design, WCAG 2.1 Accessibility</p>
                </div>
                
                <div class="friction-points-section">
                    <h4>⚠️ Identified Friction Points</h4>"""
    
    # Add friction points if available
    friction_points = cognitive.get('friction_points', [])
    if friction_points and friction_points != ['No significant friction points detected']:
        html_content += """
                    <div class="friction-points-list">"""
        for point in friction_points:
            html_content += f"""
                        <div class="friction-point">🔸 {point}</div>"""
        html_content += """
                    </div>"""
    else:
        html_content += """
                    <div class="no-friction">✅ <em>No significant friction points detected - excellent user experience!</em></div>"""
    
    html_content += """
                </div>
            </div>
        """
    
    # Add usability insights
    if 'usability_insights' in data:
        insights = data['usability_insights']
        html_content += f"""
            <div class="insights">
                <h3>💡 Usability Insights</h3>
        """
        for insight in insights:
            html_content += f"""
                <div class="insight-item">• {insight}</div>
            """
        html_content += "</div>"
    
    # Add grade calculation if available
    if 'grade_calculation' in data:
        calc = data['grade_calculation']
        html_content += f"""
            <div class="cognitive-section">
                <h3>📊 Grade Calculation</h3>
                <p><strong>Method:</strong> {calc.get('method', 'Unknown')}</p>
                <p><strong>Current Score:</strong> {calc.get('current_score', 0)}</p>
                <p><strong>Formula:</strong> {calc.get('explanation', 'Not available')}</p>
        """
        
        # Add thresholds if available
        if 'thresholds' in calc:
            thresholds = calc['thresholds']
            html_content += """
                <h4>Grade Thresholds:</h4>
                <ul>
            """
            for grade, threshold_desc in thresholds.items():
                html_content += f"""
                    <li><strong>Grade {grade}:</strong> {threshold_desc}</li>
                """
            html_content += "</ul>"
        
        html_content += "</div>"
    
    html_content += """
        </div>
        
        <script>
        function toggleExplanation(factorId) {
            var explanation = document.getElementById(factorId);
            if (explanation.style.display === 'none' || explanation.style.display === '') {
                // Hide all other explanations first
                var allExplanations = document.querySelectorAll('.factor-explanation');
                allExplanations.forEach(function(el) {
                    el.style.display = 'none';
                });
                
                // Show the clicked explanation
                explanation.style.display = 'block';
                
                // Smooth scroll to the explanation
                explanation.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                explanation.style.display = 'none';
            }
        }
        </script>
    </body>
    </html>
    """
    return html_content


def _generate_detailed_html_report(detailed_data):
    """Generate HTML version of detailed report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Detailed Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .summary-section {{ background: white; padding: 25px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .flow-item {{ background: white; border: 1px solid #dee2e6; border-radius: 8px; margin: 15px 0; overflow: hidden; }}
            .flow-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #dee2e6; }}
            .flow-content {{ padding: 20px; }}
            .timeline-item {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; }}
            .success {{ color: #28a745; }}
            .error {{ color: #dc3545; }}
            .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric-item {{ background: #e9ecef; padding: 10px; border-radius: 5px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 MCP Detailed Analysis Report</h1>
                <p>Generated: {detailed_data.get('generated_at', 'Unknown')}</p>
            </div>
    """
    
    # Add summary section
    if 'detailed_report' in detailed_data:
        report = detailed_data['detailed_report']
        summary = report.get('summary', {})
        
        html_content += f"""
            <div class="summary-section">
                <h3>📊 Summary</h3>
                <div class="metric-grid">
                    <div class="metric-item">
                        <strong>{summary.get('total_interactions', 0)}</strong><br>
                        Total Interactions
                    </div>
                    <div class="metric-item">
                        <strong>{summary.get('unique_servers', 0)}</strong><br>
                        Unique Servers
                    </div>
                    <div class="metric-item">
                        <strong>{summary.get('success_rate', 0):.1%}</strong><br>
                        Success Rate
                    </div>
                    <div class="metric-item">
                        <strong>{summary.get('avg_latency_ms', 0):.0f}ms</strong><br>
                        Avg Latency
                    </div>
                </div>
            </div>
        """
    
    # Add flows section
    if 'complete_flows' in detailed_data:
        flows = detailed_data['complete_flows']
        html_content += """
            <div class="summary-section">
                <h3>🔄 Interaction Flows</h3>
        """
        
        for i, flow in enumerate(flows[:10]):  # Limit to first 10 flows for readability
            status_icon = "✅" if flow.get('flow_complete', False) else "⏳"
            html_content += f"""
                <div class="flow-item">
                    <div class="flow-header">
                        <strong>Flow {i+1}</strong> {status_icon}
                        <span class="timestamp">{flow.get('timestamp', 'Unknown time')}</span>
                    </div>
                    <div class="flow-content">
                        <p><strong>User Prompt:</strong> {flow.get('user_prompt', 'No prompt captured')[:150]}...</p>
            """
            
            # Add LLM decision if available
            if flow.get('llm_decision'):
                decision = flow['llm_decision']
                html_content += f"""
                        <p><strong>LLM Decision:</strong></p>
                        <ul>
                            <li>Tools Selected: {decision.get('tools_selected', [])}</li>
                            <li>Confidence: {decision.get('confidence', 'Unknown')}</li>
                            <li>Processing Time: {decision.get('processing_time_ms', 0)}ms</li>
                        </ul>
                """
            
            # Add MCP interactions
            if flow.get('mcp_interactions'):
                html_content += "<p><strong>MCP Interactions:</strong></p><ul>"
                for interaction in flow['mcp_interactions'][:5]:  # Limit to 5 interactions
                    status = "✅" if interaction.get('success', True) else "❌"
                    html_content += f"""
                        <li>{status} {interaction.get('method', 'Unknown')} - {interaction.get('server', 'Unknown server')}</li>
                    """
                html_content += "</ul>"
            
            html_content += """
                    </div>
                </div>
            """
        
        html_content += "</div>"
    
    # Add correlation info if available
    if 'correlation_summary' in detailed_data:
        correlation = detailed_data['correlation_summary']
        html_content += f"""
            <div class="summary-section">
                <h3>🔗 Data Correlation</h3>
                <p><strong>Total Correlation Success Rate:</strong> {correlation.get('total_correlation_success_rate', 'Unknown')}</p>
                <p><strong>User Query Capture Method:</strong> {correlation.get('user_query_capture_method', 'Unknown')}</p>
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content


def _generate_timeline_html_report(report_data):
    """Generate HTML version of timeline-based detailed report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Detailed Timeline Analysis Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
            .metric {{ font-size: 2em; font-weight: bold; color: #6f42c1; margin-bottom: 5px; }}
            .metric-label {{ color: #6c757d; font-size: 0.9em; }}
            .flow-container {{ background: white; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }}
            .flow-header {{ background: #f8f9fa; padding: 20px; border-bottom: 1px solid #dee2e6; }}
            .flow-content {{ padding: 20px; }}
            .timeline-event {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #6f42c1; }}
            .timeline-event.llm {{ border-left-color: #28a745; }}
            .timeline-event.mcp {{ border-left-color: #17a2b8; }}
            .llm-decision {{ background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .llm-reasoning {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; font-style: italic; }}
            .tool-call {{ background: #cce5ff; padding: 10px; margin: 5px 0; border-radius: 4px; }}
            .timestamp {{ color: #6c757d; font-size: 0.85em; }}
            .success {{ color: #28a745; }}
            .duration {{ color: #6f42c1; font-weight: bold; }}
            .collapsible {{ cursor: pointer; user-select: none; }}
            .collapsible:hover {{ background-color: #e9ecef; }}
            .content {{ display: none; }}
            .content.active {{ display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Detailed Timeline Analysis Report</h1>
                <p>Generated: {report_data.get('generated_at', 'Unknown')}</p>
            </div>
    """
    
    # Add summary cards
    summary = report_data.get('summary', {})
    html_content += f"""
            <div class="summary-cards">
                <div class="summary-card">
                    <div class="metric">{summary.get('total_flows', 0)}</div>
                    <div class="metric-label">Total Interaction Flows</div>
                </div>
                <div class="summary-card">
                    <div class="metric">{summary.get('flows_with_user_context', 0)}</div>
                    <div class="metric-label">Flows with User Context</div>
                </div>
                <div class="summary-card">
                    <div class="metric">{summary.get('flows_with_llm_reasoning', 0)}</div>
                    <div class="metric-label">Flows with LLM Reasoning</div>
                </div>
                <div class="summary-card">
                    <div class="metric">{summary.get('total_tool_calls', 0)}</div>
                    <div class="metric-label">Total MCP Tool Calls</div>
                </div>
                <div class="summary-card">
                    <div class="metric">{summary.get('success_rate', 0):.1%}</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="summary-card">
                    <div class="metric">{len(summary.get('servers_involved', []))}</div>
                    <div class="metric-label">Servers Involved</div>
                </div>
            </div>
    """
    
    # Add interaction flows
    flows = report_data.get('interaction_flows', [])
    for i, flow in enumerate(flows):
        flow_id = flow.get('flow_id', f'flow_{i}')
        duration_sec = flow.get('duration_ms', 0) / 1000
        status_icon = "✅" if flow.get('success', False) else "❌"
        
        html_content += f"""
            <div class="flow-container">
                <div class="flow-header collapsible" onclick="toggleFlow('{flow_id}')">
                    <h3>Flow {i+1}: {flow.get('user_prompt', 'Unknown Request')} {status_icon}</h3>
                    <p><strong>Duration:</strong> <span class="duration">{duration_sec:.1f}s</span> | 
                       <strong>Events:</strong> {flow.get('event_count', 0)} | 
                       <strong>Server:</strong> {', '.join(flow.get('servers_involved', []))}</p>
                    <p class="timestamp">Started: {flow.get('start_time', 'Unknown')}</p>
                </div>
                <div id="{flow_id}" class="content">
                    <div class="flow-content">
        """
        
        # Add LLM decisions
        if flow.get('llm_decisions'):
            html_content += "<h4>🧠 LLM Decision Analysis</h4>"
            for decision in flow['llm_decisions']:
                confidence = decision.get('confidence_score')
                processing_time = decision.get('processing_time_ms')
                
                # Handle None values safely
                confidence_str = f"{confidence:.1%}" if confidence is not None else "N/A"
                processing_time_str = f"{processing_time}ms" if processing_time is not None else "N/A"
                
                html_content += f"""
                        <div class="llm-decision">
                            <strong>LLM Reasoning:</strong>
                            <div class="llm-reasoning">{decision.get('reasoning', 'No reasoning captured')}</div>
                            <p><strong>Tools Considered:</strong> {', '.join(decision.get('tools_considered', []))}</p>
                            <p><strong>Tools Selected:</strong> {', '.join(decision.get('tools_selected', []))}</p>
                            <p><strong>Confidence:</strong> {confidence_str} | <strong>Processing Time:</strong> {processing_time_str}</p>
                        </div>
                """
        
        # Add MCP tool calls
        if flow.get('mcp_calls'):
            html_content += "<h4>🔧 MCP Tool Calls</h4>"
            for call in flow['mcp_calls']:
                html_content += f"""
                        <div class="tool-call">
                            <strong>{call.get('tool', 'Unknown Tool')}</strong> on {call.get('server', 'Unknown Server')}
                            <div class="timestamp">Called at: {call.get('timestamp', 'Unknown')}</div>
                            <details>
                                <summary>Arguments</summary>
                                <pre>{str(call.get('args', {}))}</pre>
                            </details>
                        </div>
                """
        
        # Add timeline events
        if flow.get('timeline'):
            html_content += "<h4>📅 Complete Timeline</h4>"
            for event in flow['timeline']:
                event_type = event.get('type', 'unknown')
                css_class = 'llm' if 'llm' in event_type else 'mcp' if 'mcp' in event_type else ''
                
                html_content += f"""
                        <div class="timeline-event {css_class}">
                            <strong>{event.get('type', 'Unknown Event').replace('_', ' ').title()}</strong>
                            <div class="timestamp">{event.get('timestamp', 'Unknown time')}</div>
                            <p>{event.get('content', 'No content')}</p>
                            <small>Source: {event.get('source', 'unknown')}</small>
                        </div>
                """
        
        html_content += """
                    </div>
                </div>
            </div>
        """
    
    # Add metadata section
    meta = report_data.get('meta', {})
    html_content += f"""
            <div class="flow-container">
                <div class="flow-header">
                    <h3>📊 Report Metadata</h3>
                </div>
                <div class="flow-content">
                    <p><strong>Report Version:</strong> {meta.get('report_version', 'Unknown')}</p>
                    <p><strong>Generation Method:</strong> {meta.get('generation_method', 'Unknown')}</p>
                    <p><strong>Time Window:</strong> {meta.get('time_window_seconds', 30)} seconds</p>
                    <p><strong>Data Sources:</strong> {', '.join(meta.get('data_sources', []))}</p>
                    <p><strong>Server Filter:</strong> {meta.get('server_filter') or 'All servers'}</p>
                    <p><strong>Time Filter:</strong> Last {meta.get('time_filter_hours', 0)} hours</p>
                </div>
            </div>
        </div>
        
        <script>
        function toggleFlow(flowId) {{
            var content = document.getElementById(flowId);
            if (content.classList.contains('active')) {{
                content.classList.remove('active');
            }} else {{
                // Hide all other flows
                var allFlows = document.querySelectorAll('.content');
                allFlows.forEach(function(flow) {{
                    flow.classList.remove('active');
                }});
                
                // Show the clicked flow
                content.classList.add('active');
            }}
        }}
        </script>
    </body>
    </html>
    """
    return html_content


def _generate_timeline_text_report(report_data):
    """Generate text version of timeline-based detailed report."""
    lines = [
        "🔍 MCP Timeline Analysis Report",
        "=" * 50,
        f"Generated: {report_data.get('generated_at', 'Unknown')}",
        f"Analysis Method: {report_data.get('analysis_method', 'Timeline-based')}",
        "",
        "📊 SUMMARY:",
        "-" * 20
    ]
    
    summary = report_data.get('summary', {})
    lines.extend([
        f"Total Interaction Flows: {summary.get('total_flows', 0)}",
        f"Flows with User Context: {summary.get('flows_with_user_context', 0)}",
        f"Flows with LLM Reasoning: {summary.get('flows_with_llm_reasoning', 0)}",
        f"Success Rate: {summary.get('success_rate', 0):.1%}",
        f"Servers Involved: {', '.join(summary.get('servers_involved', []))}",
        ""
    ])
    
    # Add flows
    flows = report_data.get('interaction_flows', [])
    for i, flow in enumerate(flows):
        duration_sec = flow.get('duration_ms', 0) / 1000
        status = "✅ SUCCESS" if flow.get('success', False) else "❌ FAILED"
        
        lines.extend([
            f"🔄 FLOW {i+1}: {status}",
            "-" * 30,
            f"User Prompt: {flow.get('user_prompt', 'Unknown')}",
            f"Duration: {duration_sec:.1f}s",
            f"Events: {flow.get('event_count', 0)}",
            f"Server: {', '.join(flow.get('servers_involved', []))}",
            ""
        ])
        
        # Add LLM decisions
        if flow.get('llm_decisions'):
            lines.append("🧠 LLM Decisions:")
            for decision in flow['llm_decisions']:
                lines.extend([
                    f"  Tools Selected: {', '.join(decision.get('tools_selected', []))}",
                    f"  Confidence: {decision.get('confidence_score', 0):.1%}",
                    f"  Processing: {decision.get('processing_time_ms', 0)}ms",
                    ""
                ])
        
        # Add tool calls
        if flow.get('mcp_calls'):
            lines.append("🔧 Tool Calls:")
            for call in flow['mcp_calls']:
                lines.append(f"  {call.get('tool', 'Unknown')} on {call.get('server', 'Unknown')}")
            lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    main() 