"""
Usability Report Generator.

Generates comprehensive usability reports from analyzed MCP interactions.
"""

import statistics
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..core.models import (
    MCPInteraction,
    UsabilityReport,
    SessionSummary,
    CommunicationPatterns,
    BenchmarkingData,
    CognitiveLoadMetrics,
    UsabilityIssue,
    UsabilityRecommendation,
    ConversationContext
)
from ..analyzers.cognitive_analyzer import CognitiveAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive usability reports from MCP interaction data.
    
    Combines cognitive load analysis, communication pattern analysis,
    and benchmarking to create actionable usability insights.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.cognitive_analyzer = CognitiveAnalyzer()
        
    async def generate_comprehensive_report(
        self,
        interactions: List[MCPInteraction],
        session_duration: timedelta,
        server_name: Optional[str] = None
    ) -> UsabilityReport:
        """
        Generate a comprehensive usability report from interactions.
        
        Args:
            interactions: List of MCP interactions to analyze
            session_duration: Duration of the monitoring session
            server_name: Optional server name override
            
        Returns:
            Complete usability report
        """
        try:
            if not interactions:
                logger.warning("No interactions provided for report generation")
                return await self._create_empty_report(server_name or "unknown", session_duration)
            
            # Determine server name from interactions if not provided
            if not server_name:
                server_name = self._determine_primary_server(interactions)
            
            # Generate report components
            session_summary = self._generate_session_summary(interactions, session_duration)
            cognitive_load = await self._generate_cognitive_load_analysis(interactions)
            communication_patterns = self._generate_communication_patterns(interactions)
            detected_issues = await self.cognitive_analyzer.detect_usability_issues(interactions)
            recommendations = await self.cognitive_analyzer.generate_recommendations(
                detected_issues, cognitive_load
            )
            
            # Calculate overall usability score
            overall_score = self._calculate_overall_usability_score(
                cognitive_load, session_summary, communication_patterns, detected_issues
            )
            
            # Generate executive summary
            primary_concerns, key_wins = self._generate_executive_summary(
                detected_issues, communication_patterns, cognitive_load
            )
            
            # Create the comprehensive report
            report = UsabilityReport(
                server_name=server_name,
                analysis_window_hours=round(session_duration.total_seconds() / 3600, 2),  # Convert to hours
                overall_usability_score=overall_score,
                grade=self._calculate_grade(overall_score),
                primary_concerns=primary_concerns,
                key_wins=key_wins,
                session_summary=session_summary,
                cognitive_load=cognitive_load,
                communication_patterns=communication_patterns,
                detected_issues=detected_issues,
                recommendations=recommendations,
                benchmarking=None  # TODO: Implement benchmarking data
            )
            
            logger.info(f"Generated comprehensive report for {server_name}: score {overall_score:.1f}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            # Return empty report as fallback
            return await self._create_empty_report(server_name or "unknown", session_duration)
    
    def _determine_primary_server(self, interactions: List[MCPInteraction]) -> str:
        """Determine the primary server name from interactions."""
        if not interactions:
            return "unknown"
        
        # Count server occurrences
        server_counts = {}
        for interaction in interactions:
            server_name = interaction.server_name
            server_counts[server_name] = server_counts.get(server_name, 0) + 1
        
        # Return most common server
        return max(server_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_session_summary(
        self, 
        interactions: List[MCPInteraction], 
        session_duration: timedelta
    ) -> SessionSummary:
        """Generate session summary statistics."""
        total_sessions = len(interactions)
        successful_completions = sum(1 for i in interactions if i.success)
        
        # Calculate average session duration
        durations = []
        for interaction in interactions:
            if interaction.end_time and interaction.start_time:
                duration = interaction.end_time - interaction.start_time
                durations.append(duration.total_seconds() * 1000)  # Convert to milliseconds
        
        avg_duration_ms = statistics.mean(durations) if durations else 0.0
        
        # Calculate abandonment rate
        abandonment_rate = (total_sessions - successful_completions) / max(total_sessions, 1)
        
        # Identify common abandonment points
        abandonment_points = self._identify_abandonment_points(interactions)
        
        return SessionSummary(
            total_sessions=total_sessions,
            successful_completions=successful_completions,
            avg_session_duration_ms=avg_duration_ms,
            abandonment_rate=abandonment_rate,
            common_abandonment_points=abandonment_points
        )
    
    def _identify_abandonment_points(self, interactions: List[MCPInteraction]) -> List[str]:
        """Identify common points where interactions are abandoned."""
        abandonment_points = []
        
        # Analyze failed interactions
        failed_interactions = [i for i in interactions if not i.success]
        
        # Count abandonment patterns
        abandonment_patterns = {}
        
        for interaction in failed_interactions:
            # Look at the last message to understand where it failed
            if interaction.message_traces:
                last_message = interaction.message_traces[-1]
                
                if last_message.error_code:
                    error_type = f"Error {last_message.error_code}"
                    abandonment_patterns[error_type] = abandonment_patterns.get(error_type, 0) + 1
                elif 'auth' in str(last_message.payload).lower():
                    abandonment_patterns['Authentication'] = abandonment_patterns.get('Authentication', 0) + 1
                else:
                    abandonment_patterns['Unknown'] = abandonment_patterns.get('Unknown', 0) + 1
        
        # Return top 3 abandonment points
        sorted_patterns = sorted(abandonment_patterns.items(), key=lambda x: x[1], reverse=True)
        return [pattern[0] for pattern in sorted_patterns[:3]]
    
    async def _generate_cognitive_load_analysis(self, interactions: List[MCPInteraction]) -> CognitiveLoadMetrics:
        """Generate aggregate cognitive load analysis."""
        if not interactions:
            return CognitiveLoadMetrics(
                overall_score=0.0,
                prompt_complexity=0.0,
                context_switching=0.0,
                retry_frustration=0.0,
                configuration_friction=0.0,
                integration_cognition=0.0
            )
        
        # Analyze each interaction and calculate averages
        cognitive_loads = []
        for interaction in interactions:
            load = await self.cognitive_analyzer.analyze_interaction(interaction)
            cognitive_loads.append(load)
        
        if not cognitive_loads:
            return CognitiveLoadMetrics(
                overall_score=0.0,
                prompt_complexity=0.0,
                context_switching=0.0,
                retry_frustration=0.0,
                configuration_friction=0.0,
                integration_cognition=0.0
            )
        
        # Calculate averages
        avg_overall = statistics.mean(load.overall_score for load in cognitive_loads)
        avg_prompt = statistics.mean(load.prompt_complexity for load in cognitive_loads)
        avg_context = statistics.mean(load.context_switching for load in cognitive_loads)
        avg_retry = statistics.mean(load.retry_frustration for load in cognitive_loads)
        avg_config = statistics.mean(load.configuration_friction for load in cognitive_loads)
        avg_integration = statistics.mean(load.integration_cognition for load in cognitive_loads)
        
        # For breakdown information, use the most recent interaction's breakdown
        # or create aggregated breakdown if needed
        latest_load = cognitive_loads[-1]  # Most recent interaction
        retry_breakdown = getattr(latest_load, 'retry_breakdown', None)
        configuration_breakdown = getattr(latest_load, 'configuration_breakdown', None)
        
        return CognitiveLoadMetrics(
            overall_score=avg_overall,
            prompt_complexity=avg_prompt,
            context_switching=avg_context,
            retry_frustration=avg_retry,
            configuration_friction=avg_config,
            integration_cognition=avg_integration,
            retry_breakdown=retry_breakdown,
            configuration_breakdown=configuration_breakdown
        )
    
    def _generate_communication_patterns(self, interactions: List[MCPInteraction]) -> CommunicationPatterns:
        """Generate communication pattern analysis."""
        if not interactions:
            return CommunicationPatterns(
                avg_response_time_ms=0.0,
                retry_rate=0.0,
                tool_discovery_success_rate=0.0,
                first_attempt_success_rate=0.0,
                avg_parameter_errors=0.0
            )
        
        # Calculate response times
        response_times = []
        for interaction in interactions:
            if interaction.total_latency_ms:
                response_times.append(interaction.total_latency_ms)
        
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        
        # Calculate retry rate
        total_retries = sum(interaction.retry_count for interaction in interactions)
        retry_rate = total_retries / max(len(interactions), 1)
        
        # Calculate first attempt success rate
        first_attempt_successes = sum(
            1 for interaction in interactions 
            if interaction.success and interaction.retry_count == 0
        )
        first_attempt_success_rate = first_attempt_successes / max(len(interactions), 1)
        
        # Calculate tool discovery success rate
        tool_discovery_attempts = 0
        tool_discovery_successes = 0
        
        for interaction in interactions:
            has_tool_list = any(
                message.payload.get('method') == 'tools/list' 
                for message in interaction.message_traces
                if isinstance(message.payload, dict)
            )
            if has_tool_list:
                tool_discovery_attempts += 1
                if interaction.success:
                    tool_discovery_successes += 1
        
        tool_discovery_success_rate = (
            tool_discovery_successes / max(tool_discovery_attempts, 1)
        )
        
        # Calculate parameter errors
        parameter_errors = 0
        for interaction in interactions:
            for message in interaction.message_traces:
                if message.error_code in ['400', '422']:
                    parameter_errors += 1
        
        avg_parameter_errors = parameter_errors / max(len(interactions), 1)
        
        # Identify common confusion triggers and failure points
        confusion_triggers = self._identify_confusion_triggers(interactions)
        failure_points = self._identify_failure_points(interactions)
        
        return CommunicationPatterns(
            avg_response_time_ms=avg_response_time,
            retry_rate=retry_rate,
            confidence_decline=retry_rate > 0.3,  # High retry rate indicates confidence decline
            common_confusion_triggers=confusion_triggers,
            tool_discovery_success_rate=tool_discovery_success_rate,
            first_attempt_success_rate=first_attempt_success_rate,
            avg_parameter_errors=avg_parameter_errors,
            common_failure_points=failure_points
        )
    
    def _identify_confusion_triggers(self, interactions: List[MCPInteraction]) -> List[str]:
        """Identify common triggers for user confusion."""
        triggers = []
        
        # Look for patterns in failed or high-retry interactions
        problematic_interactions = [
            i for i in interactions 
            if not i.success or i.retry_count > 1
        ]
        
        # Count common error patterns
        error_patterns = {}
        for interaction in problematic_interactions:
            query = interaction.user_query.lower()
            
            # Common confusion patterns
            if 'api key' in query or 'token' in query:
                error_patterns['API key setup'] = error_patterns.get('API key setup', 0) + 1
            elif len(query.split()) > 8:
                error_patterns['Complex queries'] = error_patterns.get('Complex queries', 0) + 1
            elif any(word in query for word in ['format', 'syntax', 'parameter']):
                error_patterns['Parameter format'] = error_patterns.get('Parameter format', 0) + 1
        
        # Return top triggers
        sorted_patterns = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
        return [pattern[0] for pattern in sorted_patterns[:3]]
    
    def _identify_failure_points(self, interactions: List[MCPInteraction]) -> List[str]:
        """Identify common points where interactions fail."""
        failure_points = []
        
        failed_interactions = [i for i in interactions if not i.success]
        
        # Analyze where failures occur
        failure_patterns = {}
        for interaction in failed_interactions:
            for message in interaction.message_traces:
                if message.error_code:
                    if message.error_code in ['401', '403']:
                        failure_patterns['Authentication'] = failure_patterns.get('Authentication', 0) + 1
                    elif message.error_code in ['400', '422']:
                        failure_patterns['Invalid parameters'] = failure_patterns.get('Invalid parameters', 0) + 1
                    elif message.error_code in ['404']:
                        failure_patterns['Resource not found'] = failure_patterns.get('Resource not found', 0) + 1
                    elif message.error_code in ['429']:
                        failure_patterns['Rate limiting'] = failure_patterns.get('Rate limiting', 0) + 1
                    else:
                        failure_patterns['Server error'] = failure_patterns.get('Server error', 0) + 1
                    break
        
        # Return top failure points
        sorted_patterns = sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)
        return [pattern[0] for pattern in sorted_patterns[:3]]
    
    def _calculate_overall_usability_score(
        self,
        cognitive_load: CognitiveLoadMetrics,
        session_summary: SessionSummary,
        communication_patterns: CommunicationPatterns,
        detected_issues: List[UsabilityIssue]
    ) -> float:
        """Calculate overall usability score."""
        # Start with base score
        base_score = 100.0
        
        # Subtract for cognitive load (higher cognitive load = lower usability)
        cognitive_penalty = cognitive_load.overall_score * 0.4
        base_score -= cognitive_penalty
        
        # Subtract for low success rate
        success_rate = session_summary.successful_completions / max(session_summary.total_sessions, 1)
        success_penalty = (1.0 - success_rate) * 30
        base_score -= success_penalty
        
        # Subtract for high abandonment rate
        abandonment_penalty = session_summary.abandonment_rate * 20
        base_score -= abandonment_penalty
        
        # Subtract for detected issues
        for issue in detected_issues:
            if issue.severity.value == 'critical':
                base_score -= 15
            elif issue.severity.value == 'high':
                base_score -= 10
            elif issue.severity.value == 'medium':
                base_score -= 5
            else:
                base_score -= 2
        
        # Add bonus for good communication patterns
        if communication_patterns.first_attempt_success_rate > 0.8:
            base_score += 5
        
        if communication_patterns.retry_rate < 0.1:
            base_score += 5
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, base_score))
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from numerical score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_executive_summary(
        self,
        detected_issues: List[UsabilityIssue],
        communication_patterns: CommunicationPatterns,
        cognitive_load: CognitiveLoadMetrics
    ) -> tuple[List[str], List[str]]:
        """Generate executive summary with primary concerns and key wins."""
        primary_concerns = []
        key_wins = []
        
        # Primary concerns from issues
        for issue in detected_issues[:3]:  # Top 3 issues
            primary_concerns.append(issue.description)
        
        # Add cognitive load concerns
        if cognitive_load.overall_score > 80:
            primary_concerns.append("High cognitive load affecting user experience")
        
        # Add communication pattern concerns
        if communication_patterns.retry_rate > 0.3:
            primary_concerns.append("High retry rate indicates user confusion")
        
        # Key wins from good metrics
        if communication_patterns.first_attempt_success_rate > 0.8:
            key_wins.append("High first-attempt success rate")
        
        if cognitive_load.overall_score < 40:
            key_wins.append("Low cognitive load provides smooth user experience")
        
        if communication_patterns.avg_response_time_ms < 1000:
            key_wins.append("Fast response times")
        
        if not detected_issues:
            key_wins.append("No critical usability issues detected")
        
        # Ensure we have at least some content
        if not primary_concerns:
            primary_concerns.append("No major usability issues identified")
        
        if not key_wins:
            key_wins.append("Basic functionality works as expected")
        
        return primary_concerns, key_wins
    
    async def _create_empty_report(self, server_name: str, session_duration: Optional[timedelta] = None) -> UsabilityReport:
        """Create an empty report for cases with no interactions."""
        from ..core.models import SessionSummary, CommunicationPatterns
        
        # Default to 24 hours if no session duration provided
        analysis_hours = 24.0 if not session_duration else round(session_duration.total_seconds() / 3600, 2)
        
        return UsabilityReport(
            server_name=server_name,
            analysis_window_hours=analysis_hours,
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
    
    async def export_report_json(self, report: UsabilityReport, filename: Optional[str] = None) -> str:
        """Export the usability report to a JSON file."""
        from ..core.config import get_config
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"usability_report_{timestamp}.json"
        
        config = get_config()
        full_path = config.get_report_path(filename)
        
        # Convert to JSON-serializable format
        report_data = report.model_dump()
        
        # Write to file
        with open(full_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Usability report exported to: {full_path}")
        return str(full_path) 

    async def generate_enhanced_trace_report(
        self,
        interactions: List[MCPInteraction],
        include_conversation_context: bool = True
    ) -> Dict[str, Any]:
        """
        Generate an enhanced trace report that includes actual user prompts.
        
        Args:
            interactions: List of MCP interactions
            include_conversation_context: Whether to include conversation context
            
        Returns:
            Enhanced trace report with user prompts
        """
        try:
            enhanced_interactions = []
            
            for interaction in interactions:
                enhanced_interaction = {
                    "flow_metadata": {
                        "flow_id": f"flow_{abs(hash(interaction.session_id)) % 100000}",
                        "status": "completed" if interaction.success else "failed",
                        "total_latency_ms": interaction.total_latency_ms or 0,
                        "component_count": len(interaction.message_traces),
                        "start_time": interaction.start_time.isoformat(),
                        "end_time": (interaction.end_time or interaction.start_time).isoformat()
                    },
                    "component_interactions": [],
                    "raw_mcp_messages": []
                }
                
                # Enhanced user query with actual prompt
                if include_conversation_context and interaction.conversation_context:
                    enhanced_interaction["flow_metadata"]["user_query"] = interaction.conversation_context.user_prompt
                    enhanced_interaction["flow_metadata"]["user_intent"] = interaction.conversation_context.user_intent
                    enhanced_interaction["flow_metadata"]["complexity_level"] = interaction.conversation_context.complexity_level
                    enhanced_interaction["flow_metadata"]["conversation_context"] = {
                        "conversation_id": interaction.conversation_context.conversation_id,
                        "host_interface": interaction.conversation_context.host_interface,
                        "tools_available": interaction.conversation_context.tools_available,
                        "preceding_messages": interaction.conversation_context.preceding_messages[-3:]  # Last 3 messages
                    }
                else:
                    # Fallback to extracted query
                    enhanced_interaction["flow_metadata"]["user_query"] = interaction.user_query
                
                # Process message traces
                for trace in interaction.message_traces:
                    component_interaction = {
                        "source": {"component": "llm_engine", "name": "Claude/GPT"},
                        "target": {"component": "mcp_client", "name": "MCP Client"},
                        "operation": trace.payload.get("method", "unknown"),
                        "latency_ms": trace.latency_ms,
                        "success": trace.error_code is None,
                        "request_data": {
                            "timestamp": trace.timestamp.isoformat(),
                            "protocol": trace.protocol.value,
                            "payload_summary": str(trace.payload)[:200] + "..." if len(str(trace.payload)) > 200 else str(trace.payload)
                        }
                    }
                    enhanced_interaction["component_interactions"].append(component_interaction)
                    
                    # Raw message
                    raw_message = {
                        "timestamp": trace.timestamp.isoformat(),
                        "direction": trace.direction.value,
                        "protocol": trace.protocol.value,
                        "payload": trace.payload
                    }
                    enhanced_interaction["raw_mcp_messages"].append(raw_message)
                
                enhanced_interactions.append(enhanced_interaction)
            
            # Generate summary
            total_messages = sum(len(interaction.message_traces) for interaction in interactions)
            user_interactions = len([i for i in interactions if i.conversation_context])
            
            enhanced_report = {
                "comprehensive_trace_report": {
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "total_messages_processed": total_messages,
                    "distinct_interactions": len(interactions),
                    "user_interactions_with_context": user_interactions,
                    "data_source": "enhanced_mcp_capture_with_conversation"
                },
                "interactions": enhanced_interactions,
                "conversation_summary": {
                    "total_user_prompts": user_interactions,
                    "intent_distribution": self._analyze_intent_distribution(interactions),
                    "complexity_distribution": self._analyze_complexity_distribution(interactions),
                    "conversation_patterns": self._analyze_conversation_patterns(interactions)
                }
            }
            
            return enhanced_report
            
        except Exception as e:
            logger.error(f"Error generating enhanced trace report: {e}")
            return {"error": f"Failed to generate enhanced trace report: {e}"}
    
    def _analyze_intent_distribution(self, interactions: List[MCPInteraction]) -> Dict[str, int]:
        """Analyze the distribution of user intents."""
        intent_counts = {}
        
        for interaction in interactions:
            if interaction.conversation_context and interaction.conversation_context.user_intent:
                intent = interaction.conversation_context.user_intent
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return intent_counts
    
    def _analyze_complexity_distribution(self, interactions: List[MCPInteraction]) -> Dict[str, int]:
        """Analyze the distribution of query complexity levels."""
        complexity_counts = {}
        
        for interaction in interactions:
            if interaction.conversation_context and interaction.conversation_context.complexity_level:
                complexity = interaction.conversation_context.complexity_level
                complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        return complexity_counts
    
    def _analyze_conversation_patterns(self, interactions: List[MCPInteraction]) -> Dict[str, Any]:
        """Analyze conversation patterns and user behavior."""
        patterns = {
            "avg_prompt_length": 0,
            "most_common_tools": {},
            "conversation_flow": [],
            "multi_turn_conversations": 0
        }
        
        try:
            # Calculate average prompt length
            prompts = [
                interaction.conversation_context.user_prompt 
                for interaction in interactions 
                if interaction.conversation_context
            ]
            
            if prompts:
                patterns["avg_prompt_length"] = sum(len(prompt.split()) for prompt in prompts) / len(prompts)
            
            # Analyze tool usage
            for interaction in interactions:
                for trace in interaction.message_traces:
                    if trace.payload and isinstance(trace.payload, dict):
                        method = trace.payload.get("method")
                        if method:
                            patterns["most_common_tools"][method] = patterns["most_common_tools"].get(method, 0) + 1
            
            # Conversation flow analysis
            conversations = {}
            for interaction in interactions:
                if interaction.conversation_context:
                    conv_id = interaction.conversation_context.conversation_id
                    conversations.setdefault(conv_id, []).append(interaction.conversation_context.user_prompt)
            
            patterns["multi_turn_conversations"] = len([conv for conv in conversations.values() if len(conv) > 1])
            
        except Exception as e:
            logger.error(f"Error analyzing conversation patterns: {e}")
        
        return patterns 