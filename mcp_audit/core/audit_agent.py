"""
Core MCP Usability Audit Agent.

The main orchestrator for monitoring MCP interactions and generating usability insights.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..adapters.base import HostAdapter
from ..adapters.cursor import CursorAdapter
from ..interceptors.mcp_interceptor import MCPCommunicationInterceptor
from ..analyzers.cognitive_analyzer import CognitiveAnalyzer
from ..generators.report_generator import ReportGenerator
from ..integrations.manager import IntegrationManager
from .models import (
    MCPInteraction,
    UsabilityReport,
    UsabilityInsights,
    MonitoringConfig,
    HostInfo,
    CognitiveLoadMetrics,
)

logger = logging.getLogger(__name__)


class MCPUsabilityAuditAgent:
    """
    Main MCP Usability Audit Agent.
    
    Orchestrates monitoring of MCP communications, cognitive load analysis,
    and generation of usability insights and reports.
    """
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        """Initialize the audit agent with optional configuration."""
        self.config = config or MonitoringConfig()
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        
        # Core components
        self.host_adapter: Optional[HostAdapter] = None
        self.interceptor = MCPCommunicationInterceptor()
        self.cognitive_analyzer = CognitiveAnalyzer()
        self.report_generator = ReportGenerator()
        self.integration_manager = IntegrationManager()
        
        # Data storage
        self.interactions: List[MCPInteraction] = []
        self.current_insights: Optional[UsabilityInsights] = None
        
        # State tracking
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info(f"MCPUsabilityAuditAgent initialized with session ID: {self.session_id}")
    
    async def auto_detect_host(self) -> Optional[HostAdapter]:
        """Auto-detect the MCP host environment and create appropriate adapter."""
        try:
            # Try to detect Cursor first (since that's our primary target)
            cursor_adapter = CursorAdapter()
            if await cursor_adapter.detect_environment():
                logger.info("Detected Cursor environment")
                return cursor_adapter
            
            # TODO: Add other host adapters here
            # windsurf_adapter = WindsurfAdapter()
            # claude_desktop_adapter = ClaudeDesktopAdapter()
            
            logger.warning("No supported MCP host detected")
            return None
            
        except Exception as e:
            logger.error(f"Error during host detection: {e}")
            return None
    
    async def start_monitoring(self, auto_detect: bool = True) -> bool:
        """
        Start monitoring MCP communications.
        
        Args:
            auto_detect: Whether to auto-detect the MCP host environment
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if self.is_monitoring:
            logger.warning("Monitoring is already active")
            return True
        
        try:
            # Detect or use configured host adapter
            if auto_detect:
                self.host_adapter = await self.auto_detect_host()
                if not self.host_adapter:
                    logger.error("Failed to detect supported MCP host")
                    return False
            
            if not self.host_adapter:
                logger.error("No host adapter available")
                return False
            
            # Initialize the host adapter
            await self.host_adapter.initialize()
            
            # Set up the interceptor with the host adapter
            await self.interceptor.setup(self.host_adapter)
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.is_monitoring = True
            
            logger.info("MCP monitoring started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring MCP communications."""
        if not self.is_monitoring:
            return
        
        try:
            self.is_monitoring = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self.interceptor:
                await self.interceptor.cleanup()
            
            if self.host_adapter:
                await self.host_adapter.cleanup()
            
            logger.info("MCP monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that processes MCP interactions."""
        logger.info("Starting monitoring loop")
        
        try:
            while self.is_monitoring:
                # Get new interactions from the interceptor
                new_interactions = await self.interceptor.get_recent_interactions()
                
                # Process each new interaction
                for interaction in new_interactions:
                    await self._process_interaction(interaction)
                
                # Brief pause to avoid excessive CPU usage
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
    
    async def _process_interaction(self, interaction: MCPInteraction) -> None:
        """Process a single MCP interaction and update insights."""
        try:
            # Store the interaction
            self.interactions.append(interaction)
            
            # Analyze cognitive load for this interaction
            cognitive_load = await self.cognitive_analyzer.analyze_interaction(interaction)
            
            # Generate real-time insights
            self.current_insights = await self._generate_current_insights(
                interaction, cognitive_load
            )
            
            # Log high cognitive load situations
            if cognitive_load.overall_score > self.config.cognitive_load_threshold:
                logger.warning(
                    f"High cognitive load detected: {cognitive_load.overall_score:.1f} "
                    f"for server '{interaction.server_name}'"
                )
            
        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
    
    async def _generate_current_insights(
        self, 
        interaction: MCPInteraction, 
        cognitive_load: CognitiveLoadMetrics
    ) -> UsabilityInsights:
        """Generate current usability insights based on latest interaction."""
        # Detect usability issues
        detected_issues = await self.cognitive_analyzer.detect_usability_issues([interaction])
        
        # Generate recommendations
        recommendations = await self.cognitive_analyzer.generate_recommendations(
            detected_issues, cognitive_load
        )
        
        # Create timeline entry
        timeline_entry = {
            "timestamp": interaction.start_time.isoformat(),
            "description": f"MCP call to {interaction.server_name}",
            "cognitive_load": cognitive_load.overall_score,
            "success": interaction.success,
            "issues": [issue.type.value for issue in detected_issues]
        }
        
        return UsabilityInsights(
            cognitive_load=cognitive_load,
            current_interaction=interaction,
            detected_issues=detected_issues,
            recommendations=[rec.recommendation for rec in recommendations],
            interaction_timeline=[timeline_entry]
        )
    
    async def generate_report(self, server_name: Optional[str] = None, hours_back: Optional[float] = None) -> UsabilityReport:
        """
        Generate a comprehensive usability report.
        
        Args:
            server_name: Filter interactions for specific server (optional)
            hours_back: Only include interactions from the last N hours (optional)
            
        Returns:
            Complete usability report
        """
        try:
            # Load captured proxy messages if available
            proxy_interactions = await self._load_proxy_interactions(hours_back=hours_back)
            
            # If hours_back is specified, only use proxy interactions (filtered by time)
            # Otherwise, combine with session interactions
            if hours_back is not None:
                all_interactions = proxy_interactions  # Only time-filtered data
            else:
                all_interactions = self.interactions + proxy_interactions  # All data
            
            # Filter interactions if server_name specified
            filtered_interactions = all_interactions
            if server_name:
                filtered_interactions = [
                    i for i in all_interactions 
                    if i.server_name == server_name
                ]
            
            if not filtered_interactions:
                logger.warning(f"No interactions found for server: {server_name}")
                # Return empty report structure
                return await self._create_empty_report(server_name or "unknown")
            
            # Generate comprehensive report
            report = await self.report_generator.generate_comprehensive_report(
                interactions=filtered_interactions,
                session_duration=datetime.utcnow() - self.start_time
            )
            
            logger.info(f"Generated usability report for {len(filtered_interactions)} interactions ({len(proxy_interactions)} from proxy)")
            
            # Send data to configured integrations
            await self._send_to_integrations(report, filtered_interactions)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    async def _load_proxy_interactions(self, hours_back: Optional[float] = None) -> List[MCPInteraction]:
        """Load interactions captured by the MCP proxy.
        
        Args:
            hours_back: Only load interactions from the last N hours. If None, load all.
        """
        try:
            from pathlib import Path
            import json
            from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol
            
            messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
            if not messages_file.exists():
                return []

            # Calculate cutoff time if hours_back is specified
            cutoff_time = None
            if hours_back is not None:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            # Group messages by session/interaction
            message_groups = {}
            total_messages = 0
            filtered_messages = 0
            
            with open(messages_file, 'r') as f:
                for line in f:
                    try:
                        message_data = json.loads(line.strip())
                        total_messages += 1
                        
                        # Parse timestamp
                        message_timestamp = datetime.fromisoformat(message_data['timestamp'].replace('Z', '+00:00'))
                        
                        # Apply time filter if specified
                        if cutoff_time and message_timestamp.replace(tzinfo=None) < cutoff_time:
                            continue
                        
                        filtered_messages += 1
                        
                        # Create MCPMessageTrace from the raw message
                        trace = MCPMessageTrace(
                            direction=MCPMessageDirection(message_data['direction']),
                            protocol=MCPProtocol(message_data['protocol']),
                            payload=message_data['payload'],
                            timestamp=message_timestamp.replace(tzinfo=None),
                            latency_ms=message_data.get('latency_ms'),
                            error_code=message_data.get('error_code')
                        )
                        
                        # Group by method or create unique interaction ID
                        method = message_data['payload'].get('method', 'Unknown')
                        interaction_id = f"{method}_{message_data['timestamp']}"
                        
                        if interaction_id not in message_groups:
                            message_groups[interaction_id] = {
                                'method': method,
                                'timestamp': trace.timestamp,
                                'traces': []
                            }
                        
                        message_groups[interaction_id]['traces'].append(trace)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Skipping invalid proxy message: {e}")
                        continue

            # Convert grouped messages to MCPInteraction objects
            interactions = []
            for interaction_id, group in message_groups.items():
                # ✅ NEW: Try to find conversation context for this interaction
                conversation_context = self._find_conversation_context_for_group(group)
                logger.debug(f"🔗 Creating interaction for {group['method']}, context: {conversation_context is not None}")
                
                interaction = MCPInteraction(
                    session_id=f"flow_{abs(hash(interaction_id)) % 100000}",
                    server_name="mastra",
                    user_query=group['method'],
                    start_time=group['timestamp'],
                    end_time=group['timestamp'],  # Single timestamp for now
                    success=True,  # Assume success if no error
                    total_latency_ms=0,
                    retry_count=0,
                    message_traces=group['traces'],  # PRESERVE the raw message traces!
                    user_context={"captured_method": group['method']},
                    conversation_context=conversation_context  # ✅ NEW: Attach conversation context!
                )
                
                logger.debug(f"🔗 Created interaction, final context: {interaction.conversation_context is not None}")
                
                interactions.append(interaction)
            
            if hours_back is not None:
                logger.info(f"Loaded {len(interactions)} interactions from proxy (filtered {filtered_messages}/{total_messages} messages from last {hours_back}h)")
            else:
                logger.info(f"Loaded {len(interactions)} interactions from proxy")
            return interactions
            
        except Exception as e:
            logger.error(f"Error loading proxy interactions: {e}")
            return []
    
    def _find_conversation_context_for_group(self, group: Dict[str, Any]):
        """Find matching conversation context for a message group."""
        try:
            from pathlib import Path
            import json
            from datetime import datetime, timedelta
            from ..core.models import ConversationContext
            
            context_file = Path.home() / ".cursor" / "mcp_conversation_context.jsonl"
            if not context_file.exists():
                logger.debug(f"🔍 No conversation context file found: {context_file}")
                return None
            
            logger.debug(f"🔍 Looking for conversation context for group: {group.get('method', 'unknown')}")
            
            # Look for conversation context within 30 seconds of the MCP interaction
            group_time = group['timestamp']
            time_window = timedelta(seconds=30)
            
            tool_name = None
            # Try to extract tool name from traces
            for trace in group['traces']:
                if hasattr(trace, 'payload') and trace.payload:
                    payload = trace.payload
                elif isinstance(trace, dict) and 'payload' in trace:
                    payload = trace['payload']
                else:
                    continue
                
                if isinstance(payload, dict) and payload.get('method') == 'tools/call':
                    params = payload.get('params', {})
                    tool_name = params.get('name')
                    logger.debug(f"🔍 Found tool call: {tool_name}")
                    break
            
            if not tool_name:
                logger.debug(f"🔍 No tool call found in group traces")
                return None
            
            # Read conversation contexts and find matching ones
            with open(context_file, 'r') as f:
                for line in f:
                    try:
                        ctx_data = json.loads(line.strip())
                        ctx_time = datetime.fromisoformat(ctx_data['timestamp'].replace('Z', '+00:00'))
                        
                        # Check if this context is within time window and has matching tool
                        time_diff = abs((ctx_time - group_time).total_seconds())
                        has_tool = tool_name in ctx_data.get('tools_available', [])
                        
                        logger.debug(f"🔍 Checking context: time_diff={time_diff:.1f}s, has_tool={has_tool}, tool={tool_name}")
                        
                        if (time_diff <= time_window.total_seconds() and has_tool):
                            logger.info(f"✅ Found matching conversation context: '{ctx_data['user_prompt']}' → {tool_name}")
                            
                            # Create ConversationContext object
                            return ConversationContext(
                                user_prompt=ctx_data['user_prompt'],
                                conversation_id=ctx_data['conversation_id'],
                                message_timestamp=ctx_time,
                                user_intent=ctx_data.get('user_intent', 'general'),
                                complexity_level=ctx_data.get('complexity_level', 'simple'),
                                tools_available=ctx_data.get('tools_available', []),
                                host_interface=ctx_data.get('host_interface', 'cursor')
                            )
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        continue
            
            logger.debug(f"🔍 No matching conversation context found for tool: {tool_name}")
            return None
            
        except Exception as e:
            logger.debug(f"Error finding conversation context: {e}")
            return None
    
    async def _create_empty_report(self, server_name: str) -> UsabilityReport:
        """Create an empty report structure for servers with no interactions."""
        from .models import SessionSummary, CommunicationPatterns
        
        return UsabilityReport(
            server_name=server_name,
            overall_usability_score=0.0,
            grade="F",
            primary_concerns=["No interactions detected"],
            key_wins=[],
            session_summary=SessionSummary(
                total_sessions=0,
                successful_completions=0,
                avg_session_duration_ms=0.0,
                abandonment_rate=1.0
            ),
            cognitive_load=CognitiveLoadMetrics(
                overall_score=0.0,
                prompt_complexity=0.0,
                context_switching=0.0,
                retry_frustration=0.0,
                configuration_friction=0.0,
                integration_cognition=0.0
            ),
            communication_patterns=CommunicationPatterns(
                avg_response_time_ms=0.0,
                retry_rate=0.0,
                tool_discovery_success_rate=0.0,
                first_attempt_success_rate=0.0,
                avg_parameter_errors=0.0
            )
        )
    
    async def get_current_insights(self) -> Optional[UsabilityInsights]:
        """Get the most recent usability insights."""
        return self.current_insights
    
    async def get_interaction_count(self, server_name: Optional[str] = None) -> int:
        """Get the count of interactions, optionally filtered by server."""
        if server_name:
            return len([i for i in self.interactions if i.server_name == server_name])
        return len(self.interactions)
    
    async def get_monitored_servers(self) -> List[str]:
        """Get list of servers that have been monitored."""
        return list(set(interaction.server_name for interaction in self.interactions))
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current monitoring session."""
        duration = datetime.utcnow() - self.start_time
        
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "is_monitoring": self.is_monitoring,
            "total_interactions": len(self.interactions),
            "monitored_servers": len(set(i.server_name for i in self.interactions)),
            "host_adapter": self.host_adapter.__class__.__name__ if self.host_adapter else None
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_monitoring()
        return self
    
    async def _send_to_integrations(self, report: UsabilityReport, interactions: List[MCPInteraction]) -> None:
        """Send report and interaction data to configured integrations."""
        try:
            if not self.integration_manager.integrations:
                logger.debug("No integrations configured, skipping data export")
                return
            
            logger.info(f"📤 Sending data to {len(self.integration_manager.integrations)} integrations...")
            
            # Send usability report
            report_results = await self.integration_manager.send_usability_report(report)
            
            # Send interaction traces
            trace_results = await self.integration_manager.send_interactions(interactions)
            
            # Send cognitive metrics
            cognitive_metrics = {
                "server": report.server_name,
                "overall_score": report.cognitive_load.overall_score,
                "prompt_complexity_score": report.cognitive_load.prompt_complexity,
                "context_switching_score": report.cognitive_load.context_switching,
                "retry_frustration_score": report.cognitive_load.retry_frustration,
                "configuration_friction_score": report.cognitive_load.configuration_friction,
                "integration_cognition_score": report.cognitive_load.integration_cognition,
                "usability_score": report.overall_usability_score,
                "grade": report.grade,
                "interaction_count": len(interactions)
            }
            metrics_results = await self.integration_manager.send_cognitive_metrics(cognitive_metrics)
            
            # Log results
            for platform, success in report_results.items():
                if success:
                    logger.info(f"✅ Sent usability report to {platform}")
                else:
                    logger.warning(f"⚠️ Failed to send usability report to {platform}")
            
            for platform, success in trace_results.items():
                if success:
                    logger.info(f"✅ Sent {len(interactions)} interactions to {platform}")
                else:
                    logger.warning(f"⚠️ Failed to send interactions to {platform}")
            
        except Exception as e:
            logger.error(f"Error sending data to integrations: {e}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_monitoring() 