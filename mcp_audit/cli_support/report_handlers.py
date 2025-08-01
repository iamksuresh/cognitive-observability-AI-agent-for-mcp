"""
Report generation handlers extracted from the main CLI.
These handle the core business logic for generating different types of reports.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from ..core.audit_agent import MCPUsabilityAuditAgent
from ..interceptors.enhanced_conversation_correlator import EnhancedConversationCorrelator
from ..interceptors.conversation_interceptor import ConversationContextInterceptor
from ..generators.report_generator import ReportGenerator
from ..tracing.timeline_analyzer import TimelineAnalyzer
from .utils import console, parse_time_duration
from .html_generators import generate_enhanced_trace_html_report


class ReportHandlers:
    """Handles all report generation operations extracted from CLI."""
    
    def __init__(self):
        self.agent = MCPUsabilityAuditAgent()
        self.timeline_analyzer = TimelineAnalyzer(time_window_seconds=30)
        self.enhanced_correlator = EnhancedConversationCorrelator()
        self.conversation_interceptor = ConversationContextInterceptor()
        self.report_generator = ReportGenerator()
    
    async def generate_trace_report(self, output_path: Path, output_format: str, server: Optional[str], since: Optional[str]) -> None:
        """Generate Enhanced Component Trace Report with conversation context."""
        console.print("🔍 [bold blue]Comprehensive MCP Trace Report Generator[/bold blue]")
        console.print("=" * 60)
        
        # Load MCP interactions from proxy with time filtering
        hours = parse_time_duration(since)  # Support minutes, hours, and days
        agent = MCPUsabilityAuditAgent()
        interactions = await agent._load_proxy_interactions(hours_back=hours)
        
        if not interactions:
            console.print("[yellow]⚠️ No captured MCP interactions found.[/yellow]")
            console.print("[blue]💡 Start the proxy and interact with MCP tools first.[/blue]")
            
            # Generate empty report instead of returning early
            enhanced_interactions = []
            correlated_count = 0
            
            # Create minimal report for empty state
            report_data = {
                "comprehensive_trace_report": {
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "total_messages_processed": 0,
                    "distinct_interactions": 0,
                    "user_interactions_with_context": 0,
                    "data_source": "enhanced_mcp_capture_with_conversation",
                    "includes_full_component_flow": True,
                    "correlation_success_rate": "0/0",
                    "status": "no_interactions_found"
                },
                "interactions": [],
                "conversation_summary": {
                    "total_user_prompts": 0,
                    "intent_distribution": {},
                    "complexity_distribution": {},
                    "conversation_patterns": {
                        "avg_prompt_length": 0,
                        "most_common_tools": {},
                        "conversation_flow": [],
                        "multi_turn_conversations": 0
                    }
                }
            }
        else:
            console.print(f"✅ Loaded {len(interactions)} total MCP interactions")
            
            # Load conversation contexts
            hours = parse_time_duration(since)  # Support minutes, hours, and days
            
            # Get correlation status
            correlation_status = self.enhanced_correlator.get_correlation_status()
            console.print(f"📝 Found {correlation_status['recent_prompts_count']} user prompts from last {hours}h")
            if correlation_status['latest_prompt']:
                console.print(f"🔹 Latest prompt: \"{correlation_status['latest_prompt'][:50]}...\"")
            
            # Filter by server if specified
            filtered_interactions = []
            for interaction in interactions:
                if server and interaction.server_name != server:
                    continue
                filtered_interactions.append(interaction)
            
            # Use filtered interactions
            enhanced_interactions = filtered_interactions
            
            # Enhanced correlation with user prompts using MCPInteraction objects directly
            console.print("🔗 Correlating user prompts with MCP interactions...")
            
            # Load recent contexts
            recent_contexts = self.conversation_interceptor.load_recent_contexts(hours=int(hours))
            
            # Correlate each interaction
            correlated_count = 0
            for interaction in enhanced_interactions:
                if await self.conversation_interceptor.correlate_with_mcp_interaction(interaction, time_window_seconds=30):
                    correlated_count += 1
            
            if server:
                console.print(f"🎯 Filtered to {len(enhanced_interactions)} interactions for server: {server}")
            
            console.print(f"🔗 Correlated {correlated_count}/{len(enhanced_interactions)} interactions with user prompts")
            
            # Generate enhanced trace report with MCPInteraction objects
            console.print("📊 Generating trace report with raw MCP messages and user queries...")
            
            report_data = await self.report_generator.generate_enhanced_trace_report(
                enhanced_interactions, 
                include_conversation_context=True
            )
            
            # Update report to include trace flow metadata
            if "comprehensive_trace_report" in report_data:
                report_data["comprehensive_trace_report"]["includes_full_component_flow"] = True
                report_data["comprehensive_trace_report"]["correlation_success_rate"] = f"{correlated_count}/{len(enhanced_interactions)}"
                report_data["comprehensive_trace_report"]["raw_user_queries_captured"] = correlated_count
                report_data["comprehensive_trace_report"]["report_type"] = "raw_traces_with_user_queries"
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        elif output_format == 'html':
            html_content = generate_enhanced_trace_html_report(report_data)
            output_path.write_text(html_content)
        elif output_format == 'txt':
            txt_content = self._generate_trace_text_report(report_data)
            output_path.write_text(txt_content)
        
        # Display enhanced summary
        console.print(f"\n📊 [bold]Enhanced Trace Report Summary:[/bold]")
        
        # Check if report generation was successful
        if "error" in report_data:
            console.print(f"[red]❌ Error generating trace report: {report_data['error']}[/red]")
            return
        
        if "comprehensive_trace_report" in report_data:
            trace_report = report_data["comprehensive_trace_report"]
            console.print(f"   • Total MCP Messages: {trace_report.get('total_messages_processed', 0)}")
            console.print(f"   • User Interactions: {trace_report.get('distinct_interactions', 0)}")
            console.print(f"   • With Conversation Context: {trace_report.get('user_interactions_with_context', 0)}")
            console.print(f"   • Raw User Queries Captured: {trace_report.get('raw_user_queries_captured', 0)}")
        
        # Fix division by zero error
        if len(enhanced_interactions) > 0:
            correlation_pct = correlated_count/len(enhanced_interactions)*100
            console.print(f"   • Correlation Success: {correlated_count}/{len(enhanced_interactions)} ({correlation_pct:.1f}%)")
        else:
            console.print(f"   • Correlation Success: 0/0 (N/A - no interactions)")
        
        if 'conversation_summary' in report_data:
            conv_summary = report_data['conversation_summary']
            console.print(f"\n💬 [bold]Conversation Insights:[/bold]")
            console.print(f"   • Intent Distribution: {conv_summary['intent_distribution']}")
            console.print(f"   • Complexity Distribution: {conv_summary['complexity_distribution']}")
            
            if conv_summary['conversation_patterns']['avg_prompt_length'] > 0:
                console.print(f"   • Average Prompt Length: {conv_summary['conversation_patterns']['avg_prompt_length']:.1f} words")
            
            console.print(f"\n🔄 [bold]Component Flow Coverage:[/bold]")
            console.print("   ✅ User Query → LLM → MCP Client → Server → Response")
            console.print("   ✅ Full conversation context included")
            console.print("   ✅ Intent and complexity analysis")
            console.print("   ✅ Tool correlation mapping")
    
    def _generate_trace_text_report(self, report_data):
        """Helper method for text report generation."""
        # This will be implemented when we extract the text generation functions
        return f"Trace Report Generated: {report_data.get('generated_at', 'Unknown')}"
    
    async def generate_usability_report(self, output_path: Path, output_format: str, server: Optional[str], since: Optional[str]) -> None:
        """Generate Enhanced Usability Analysis Report with conversation context."""
        from datetime import timedelta, datetime
        
        console.print("🧠 [bold blue]Enhanced Usability Analysis Report[/bold blue]")
        console.print("=" * 60)
        
        # Load MCP interactions with time filtering
        hours = parse_time_duration(since)  # Support minutes, hours, and days
        agent = MCPUsabilityAuditAgent()
        interactions = await agent._load_proxy_interactions(hours_back=hours)
        
        if not interactions:
            console.print(f"[yellow]⚠️ No MCP interactions found in the last {hours}h.[/yellow]")
            console.print("[blue]💡 Try running monitoring first or interact with MCP tools.[/blue]")
            
            # Generate empty report instead of returning early
            enhanced_interactions = []
            
            # Create minimal usability report for empty state
            report = {
                "session_summary": {
                    "total_interactions": 0,
                    "successful_interactions": 0,
                    "average_latency_ms": 0,
                    "success_rate": 0.0
                },
                "cognitive_load": {
                    "overall_score": 0,
                    "complexity_score": 0,
                    "effort_score": 0
                },
                "overall_usability_score": 0.0,
                "grade": "N/A",
                "status": "no_interactions_found",
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        else:
            # Load conversation contexts
            hours = parse_time_duration(since)  # Support minutes, hours, and days
            
            recent_contexts = self.conversation_interceptor.load_recent_contexts(hours=hours)
            console.print(f"📝 Found {len(recent_contexts)} conversation contexts")
            
            # Correlate conversations with interactions
            enhanced_interactions = []
            for interaction in interactions:
                if server and interaction.server_name != server:
                    continue
                await self.conversation_interceptor.correlate_with_mcp_interaction(interaction, time_window_seconds=30)
                enhanced_interactions.append(interaction)
            
            # Generate enhanced usability report
            report = await self.report_generator.generate_comprehensive_report(
                enhanced_interactions,
                timedelta(hours=hours),
                server
            )
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate report in requested format
        if output_format == 'json':
            if hasattr(report, 'model_dump_json'):
                output_path.write_text(report.model_dump_json(indent=2))
            else:
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        elif output_format == 'html':
            html_content = self._generate_html_report(report)
            output_path.write_text(html_content)
        elif output_format == 'txt':
            txt_content = self._generate_text_report(report)
            output_path.write_text(txt_content)
        
        # Display enhanced summary
        console.print("\\n[bold]📋 Enhanced Usability Report Summary:[/bold]")
        console.print(f"   • Interactions Analyzed: {len(enhanced_interactions)}")
        console.print(f"   • Conversation Context: {len([i for i in enhanced_interactions if i.conversation_context])}")
        if hasattr(report, 'session_summary'):
            from .utils import _display_report_summary
            _display_report_summary(report)
            
    def _generate_html_report(self, report):
        """Helper method for HTML report generation."""
        # This will be implemented when we extract the HTML generation functions
        return f"<html><body>HTML Report Generated for: {report}</body></html>"
        
    def _generate_text_report(self, report):
        """Helper method for text report generation."""
        # This will be implemented when we extract the text generation functions
        return f"Text Report Generated for: {report}"