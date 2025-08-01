"""
Timeline-based analysis for MCP audit messages.
Replaces complex correlation logic with simple timestamp-based grouping.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TimelineAnalyzer:
    """Analyzes MCP audit messages using timeline-based grouping instead of correlation."""
    
    def __init__(self, time_window_seconds: int = 30):
        """
        Initialize timeline analyzer.
        
        Args:
            time_window_seconds: Messages within this time window are considered related
        """
        self.time_window_seconds = time_window_seconds
    
    def load_messages(self, since_hours: Optional[float] = None) -> List[Dict[str, Any]]:
        """Load messages from the audit file."""
        try:
            messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
            
            if not messages_file.exists():
                logger.warning(f"Messages file not found: {messages_file}")
                return []
            
            messages = []
            cutoff_time = None
            
            if since_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)
            
            with open(messages_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        message = json.loads(line.strip())
                        
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                        
                        # Filter by time if specified
                        if cutoff_time and timestamp < cutoff_time:
                            continue
                        
                        message['parsed_timestamp'] = timestamp
                        message['source'] = 'mcp_audit'
                        messages.append(message)
                        
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.debug(f"Skipping invalid message line: {e}")
                        continue
            
            # Sort by timestamp
            messages.sort(key=lambda m: m['parsed_timestamp'])
            logger.info(f"Loaded {len(messages)} MCP messages for timeline analysis")
            
            return messages
            
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            return []
    
    def load_llm_decisions(self, since_hours: Optional[float] = None) -> List[Dict[str, Any]]:
        """Load LLM decision traces from the decision trace file."""
        try:
            decisions_file = Path.home() / ".cursor" / "llm_decision_trace.jsonl"
            
            if not decisions_file.exists():
                logger.warning(f"LLM decisions file not found: {decisions_file}")
                return []
            
            decisions = []
            cutoff_time = None
            
            if since_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)
            
            with open(decisions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        decision = json.loads(line.strip())
                        
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(decision['timestamp'].replace('Z', '+00:00'))
                        
                        # Filter by time if specified
                        if cutoff_time and timestamp < cutoff_time:
                            continue
                        
                        decision['parsed_timestamp'] = timestamp
                        decision['source'] = 'llm_decision'
                        decisions.append(decision)
                        
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.debug(f"Skipping invalid decision line: {e}")
                        continue
            
            # Sort by timestamp
            decisions.sort(key=lambda d: d['parsed_timestamp'])
            logger.info(f"Loaded {len(decisions)} LLM decisions for timeline analysis")
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error loading LLM decisions: {e}")
            return []
    
    def merge_timeline_data(self, messages: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge MCP messages and LLM decisions into a unified timeline."""
        # Combine both data sources
        all_events = messages + decisions
        
        # Sort by timestamp
        all_events.sort(key=lambda e: e['parsed_timestamp'])
        
        logger.info(f"Merged timeline: {len(messages)} MCP messages + {len(decisions)} LLM decisions = {len(all_events)} total events")
        
        return all_events
    
    def group_into_flows(self, timeline_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group timeline events into interaction flows based on timestamp proximity."""
        if not timeline_events:
            return []
        
        flows = []
        current_flow = []
        
        for event in timeline_events:
            # Start new flow if time gap is too large or this is the first event
            if not current_flow or self._time_gap_seconds(current_flow[-1], event) > self.time_window_seconds:
                # Finalize previous flow
                if current_flow:
                    flows.append(self._create_flow_summary(current_flow))
                
                # Start new flow
                current_flow = [event]
            else:
                # Add to current flow
                current_flow.append(event)
        
        # Don't forget the last flow
        if current_flow:
            flows.append(self._create_flow_summary(current_flow))
        
        logger.info(f"Grouped {len(timeline_events)} events into {len(flows)} interaction flows")
        return flows
    
    def _time_gap_seconds(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> float:
        """Calculate time gap between two events in seconds."""
        time1 = event1['parsed_timestamp']
        time2 = event2['parsed_timestamp']
        return (time2 - time1).total_seconds()
    
    def _create_flow_summary(self, flow_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of an interaction flow with LLM reasoning."""
        if not flow_events:
            return {}
        
        start_time = flow_events[0]['parsed_timestamp']
        end_time = flow_events[-1]['parsed_timestamp']
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Extract user prompts and LLM reasoning
        user_prompt = None
        user_timestamp = None
        llm_reasoning = None
        llm_decisions = []
        
        # Extract MCP tool calls
        mcp_calls = []
        servers_involved = set()
        
        for event in flow_events:
            if event.get('source') == 'llm_decision':
                # LLM decision event
                llm_decisions.append({
                    'timestamp': event['parsed_timestamp'].isoformat(),
                    'user_prompt': event.get('user_prompt', ''),
                    'reasoning': event.get('llm_reasoning', ''),
                    'tools_considered': event.get('tools_considered', []),
                    'tools_selected': event.get('tools_selected', []),
                    'tool_calls': event.get('tool_calls', []),
                    'processing_time_ms': event.get('processing_time_ms', 0),
                    'confidence_score': event.get('confidence_score'),
                    'success': event.get('success', True)
                })
                
                # Use LLM's user prompt if available and we don't have one yet
                if not user_prompt and event.get('user_prompt'):
                    user_prompt = event['user_prompt']
                    user_timestamp = event['parsed_timestamp']
                    llm_reasoning = event.get('llm_reasoning', '')
            
            elif event.get('source') == 'mcp_audit':
                # MCP message event
                server_name = event.get('server_name', 'unknown')
                servers_involved.add(server_name)
                
                if event.get('direction') == 'user→llm':
                    # User prompt from our capture system
                    if not user_prompt:
                        user_prompt = event.get('payload', {}).get('content')
                        user_timestamp = event['parsed_timestamp']
                elif event.get('direction') == 'llm→mcp_client' and event.get('payload', {}).get('method') == 'tools/call':
                    # MCP tool call
                    tool_name = event.get('enhanced_context', {}).get('tool_name')
                    tool_args = event.get('payload', {}).get('params', {}).get('arguments', {})
                    
                    mcp_calls.append({
                        'timestamp': event['parsed_timestamp'].isoformat(),
                        'server': server_name,
                        'tool': tool_name,
                        'args': tool_args
                    })
        
        # Generate enhanced flow summary with LLM reasoning
        flow_summary = {
            'flow_id': f"flow_{int(start_time.timestamp())}",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_ms': duration_ms,
            'event_count': len(flow_events),
            'servers_involved': list(servers_involved),
            'cross_server_flow': len(servers_involved) > 1,
            'has_user_context': user_prompt is not None,
            'user_prompt': user_prompt,
            'user_timestamp': user_timestamp.isoformat() if user_timestamp else None,
            'llm_reasoning': llm_reasoning,
            'llm_decisions': llm_decisions,
            'mcp_calls': mcp_calls,
            'success': self._determine_flow_success(flow_events),
            'timeline': [
                {
                    'timestamp': event['parsed_timestamp'].isoformat(),
                    'type': self._classify_event_type(event),
                    'source': event.get('source', 'unknown'),
                    'server': event.get('server_name', 'N/A'),
                    'content': self._extract_event_content(event)
                }
                for event in flow_events
            ]
        }
        
        return flow_summary
    
    def _classify_event_type(self, event: Dict[str, Any]) -> str:
        """Classify event type for timeline display."""
        if event.get('source') == 'llm_decision':
            if '[Tool Discovery]' in event.get('user_prompt', ''):
                return 'llm_tool_discovery'
            elif event.get('tools_selected'):
                return 'llm_tool_selection'
            else:
                return 'llm_reasoning'
        
        direction = event.get('direction', '')
        
        if direction == 'user→llm':
            return 'user_prompt'
        elif direction == 'llm→mcp_client':
            method = event.get('payload', {}).get('method')
            if method == 'tools/call':
                return 'tool_call'
            elif method == 'initialize':
                return 'initialization'
            else:
                return 'llm_request'
        elif 'server' in direction:
            return 'mcp_response'
        else:
            return 'other'
    
    def _extract_event_content(self, event: Dict[str, Any]) -> str:
        """Extract meaningful content from event for timeline."""
        if event.get('source') == 'llm_decision':
            reasoning = event.get('llm_reasoning', '')
            tools = event.get('tools_selected', [])
            if tools:
                return f"Selected {', '.join(tools)}: {reasoning[:100]}..."
            return reasoning[:100] + '...' if len(reasoning) > 100 else reasoning
        
        direction = event.get('direction', '')
        payload = event.get('payload', {})
        
        if direction == 'user→llm':
            content = payload.get('content', '')
            return content[:100] + '...' if len(content) > 100 else content
        elif direction == 'llm→mcp_client':
            method = payload.get('method')
            if method == 'tools/call':
                tool_name = payload.get('params', {}).get('name')
                return f"Call {tool_name}"
            else:
                return method or 'Unknown request'
        else:
            return payload.get('method', 'Response')
    
    def _determine_flow_success(self, flow_events: List[Dict[str, Any]]) -> bool:
        """Determine if the flow completed successfully."""
        # Check LLM decisions for success
        llm_success = any(
            event.get('source') == 'llm_decision' and event.get('success', False)
            for event in flow_events
        )
        
        # Check MCP tool calls and responses
        has_tool_call = any(
            event.get('direction') == 'llm→mcp_client' and 
            event.get('payload', {}).get('method') == 'tools/call'
            for event in flow_events
        )
        
        has_response = any(
            'server' in event.get('direction', '') and
            event.get('payload', {}).get('result') is not None
            for event in flow_events
        )
        
        return llm_success or (has_tool_call and has_response)
    
    def filter_flows_by_server(self, flows: List[Dict[str, Any]], server_filter: str) -> List[Dict[str, Any]]:
        """Filter flows by server name."""
        if server_filter == 'all' or not server_filter:
            return flows
        
        if ',' in server_filter:
            # Multiple servers
            servers = [s.strip() for s in server_filter.split(',')]
            return [flow for flow in flows if any(server in flow['servers_involved'] for server in servers)]
        else:
            # Single server
            return [flow for flow in flows if server_filter in flow['servers_involved']]
    
    def generate_timeline_report(self, flows: List[Dict[str, Any]], report_type: str = 'detailed') -> Dict[str, Any]:
        """Generate timeline-based report from flows with LLM reasoning."""
        if not flows:
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'total_flows': 0,
                'flows_with_user_context': 0,
                'flows_with_llm_reasoning': 0,
                'cross_server_flows': 0,
                'message': 'No interaction flows found'
            }
        
        # Calculate statistics
        total_flows = len(flows)
        flows_with_user_context = len([f for f in flows if f['has_user_context']])
        flows_with_llm_reasoning = len([f for f in flows if f.get('llm_reasoning')])
        cross_server_flows = len([f for f in flows if f['cross_server_flow']])
        successful_flows = len([f for f in flows if f['success']])
        
        servers_involved = set()
        total_tool_calls = 0
        total_llm_decisions = 0
        
        for flow in flows:
            servers_involved.update(flow['servers_involved'])
            total_tool_calls += len(flow['mcp_calls'])
            total_llm_decisions += len(flow.get('llm_decisions', []))
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': 'timeline_based_with_llm_reasoning',
            'analysis_method': 'timestamp_proximity_grouping_with_llm_decisions',
            'time_window_seconds': self.time_window_seconds,
            'summary': {
                'total_flows': total_flows,
                'flows_with_user_context': flows_with_user_context,
                'user_context_rate': flows_with_user_context / total_flows if total_flows > 0 else 0,
                'flows_with_llm_reasoning': flows_with_llm_reasoning,
                'llm_reasoning_rate': flows_with_llm_reasoning / total_flows if total_flows > 0 else 0,
                'cross_server_flows': cross_server_flows,
                'successful_flows': successful_flows,
                'success_rate': successful_flows / total_flows if total_flows > 0 else 0,
                'servers_involved': list(servers_involved),
                'total_tool_calls': total_tool_calls,
                'total_llm_decisions': total_llm_decisions
            }
        }
        
        # Add flow details based on report type
        if report_type in ['detailed']:
            report['interaction_flows'] = flows
        else:
            # For usability reports, add aggregated metrics
            report['usability_metrics'] = self._calculate_usability_metrics(flows)
        
        return report
    
    def _calculate_usability_metrics(self, flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate usability metrics from timeline flows."""
        if not flows:
            return {
                'user_interactions': 0,
                'successful_completions': 0,
                'abandonment_rate': 1.0,
                'avg_flow_duration_sec': 0.0,
                'tool_usage_success_rate': 0.0,
                'llm_reasoning_quality': 0.0
            }
        
        flows_with_user = [f for f in flows if f.get('has_user_context', False)]
        successful_flows = [f for f in flows if f.get('success', False)]
        flows_with_reasoning = [f for f in flows if f.get('llm_reasoning', False)]
        
        # Calculate metrics
        user_interactions = len(flows_with_user)
        successful_completions = len([f for f in flows_with_user if f.get('success', False)])
        abandonment_rate_raw = 1 - (successful_completions / user_interactions) if user_interactions > 0 else 1.0
        abandonment_rate = int(abandonment_rate_raw) if abandonment_rate_raw == int(abandonment_rate_raw) else round(abandonment_rate_raw, 3)
        
        # Fix: Convert duration to seconds and round, handling None values
        durations_ms = [f.get('duration_ms', 0) or 0 for f in flows]  # Handle None and missing values
        avg_duration_ms = sum(durations_ms) / len(flows) if flows else 0
        avg_duration_sec_raw = avg_duration_ms / 1000
        avg_duration_sec = int(avg_duration_sec_raw) if avg_duration_sec_raw == int(avg_duration_sec_raw) else round(avg_duration_sec_raw, 1)
        
        # Fix: Calculate tool success rate correctly - count successful tool calls vs total tool calls
        total_tool_calls = 0
        successful_tool_calls = 0
        
        for flow in flows:
            flow_tool_calls = len(flow.get('mcp_calls', []))  # Handle missing or None mcp_calls
            total_tool_calls += flow_tool_calls
            
            # Count successful tool calls in this flow
            if flow.get('success', False):  # Handle missing or None success
                successful_tool_calls += flow_tool_calls
        
        tool_success_rate = round(successful_tool_calls / total_tool_calls if total_tool_calls > 0 else 0.0, 3)
        
        # LLM reasoning quality metric (0-1 scale, converted to 0-100)
        llm_reasoning_quality = round(len(flows_with_reasoning) / len(flows) if flows else 0.0, 3)
        
        return {
            'user_interactions': user_interactions,
            'successful_completions': successful_completions,
            'abandonment_rate': abandonment_rate,
            'avg_flow_duration_sec': avg_duration_sec,  # Changed from _ms to _sec
            'tool_usage_success_rate': tool_success_rate,
            'llm_reasoning_quality': llm_reasoning_quality
        }
    
    def _convert_flows_to_interactions(self, flows: List[Dict[str, Any]]) -> List:
        """Convert timeline flows to MCPInteraction objects for cognitive analysis."""
        interactions = []
        
        try:
            # Import here to avoid circular imports
            from ..core.models import MCPInteraction, MCPMessageTrace, MCPMessageDirection, MCPProtocol
            from datetime import datetime
            
            for flow in flows:
                # Extract basic flow information
                start_time_str = flow.get('start_time', datetime.utcnow().isoformat())
                end_time_str = flow.get('end_time', start_time_str)
                
                # Parse timestamps
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                
                # Calculate duration
                duration_ms = flow.get('duration_ms', 0)
                
                # Create simplified message traces for cognitive analysis (not every protocol event)
                message_traces = []
                
                # Only create traces for meaningful user-level actions, not protocol noise
                mcp_calls = flow.get('mcp_calls', [])
                for i, call in enumerate(mcp_calls):
                    trace = MCPMessageTrace(
                        timestamp=start_time,
                        direction=MCPMessageDirection.LLM_TO_MCP_CLIENT,
                        protocol=MCPProtocol.JSON_RPC,
                        payload={
                            'method': call.get('tool', 'unknown_tool'),
                            'params': call.get('args', {})
                        },
                        server_name=flow.get('servers_involved', ['unknown'])[0] if flow.get('servers_involved') else 'unknown',
                        error_code=None,  # Explicitly set no error for successful flows
                        latency_ms=int(duration_ms) if duration_ms else None
                    )
                    message_traces.append(trace)
                
                # If no MCP calls, create a single trace representing the flow
                if not message_traces:
                    trace = MCPMessageTrace(
                        timestamp=start_time,
                        direction=MCPMessageDirection.LLM_TO_MCP_CLIENT,
                        protocol=MCPProtocol.JSON_RPC,
                        payload={
                            'method': 'user_interaction',
                            'flow_type': flow.get('user_prompt', 'unknown')
                        },
                        server_name=flow.get('servers_involved', ['unknown'])[0] if flow.get('servers_involved') else 'unknown',
                        error_code=None,  # Explicitly set no error for successful flows
                        latency_ms=int(duration_ms) if duration_ms else None
                    )
                    message_traces.append(trace)
                
                # Extract user query from LLM decisions or flow
                user_query = flow.get('user_prompt', 'Unknown user request')
                
                # For cognitive analysis, preserve inferred/placeholder prompts to trigger base scoring
                if (not user_query or 
                    user_query == '[Inferred] User request requiring tool usage' or
                    user_query.startswith('[Tool Discovery]') or
                    user_query == 'Unknown user request'):
                    # Keep as inferred for cognitive analysis (will get base complexity score)
                    user_query = '[Inferred] User request requiring tool usage'
                
                # Create MCPInteraction object
                interaction = MCPInteraction(
                    session_id=flow.get('flow_id', f"flow_{hash(str(flow)) % 100000}"),
                    server_name=flow.get('servers_involved', ['unknown'])[0] if flow.get('servers_involved') else 'unknown',
                    user_query=user_query,
                    start_time=start_time,
                    end_time=end_time,
                    message_traces=message_traces,
                    success=flow.get('success', False),
                    total_latency_ms=int(duration_ms) if duration_ms is not None else 0,  # Handle None duration_ms
                    retry_count=0,  # TODO: Could infer from retry patterns
                    user_context={
                        'flow_type': 'timeline_based',
                        'tools_used': [call.get('tool') for call in flow.get('mcp_calls', [])],
                        'llm_reasoning': flow.get('llm_reasoning'),
                        'cross_server_flow': flow.get('cross_server_flow', False)
                    }
                )
                
                interactions.append(interaction)
                
        except Exception as e:
            logger.error(f"Error converting flows to interactions: {e}")
            
        return interactions
    
    async def generate_cognitive_analysis(self, flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cognitive load analysis and usability insights from flows."""
        
        # Convert flows to MCPInteraction objects
        interactions = self._convert_flows_to_interactions(flows)
        
        if not interactions:
            return {
                'cognitive_load': {
                    'overall_score': 0,
                    'prompt_complexity': 0,
                    'context_switching': 0,
                    'retry_frustration': 0,
                    'configuration_friction': 0,
                    'integration_cognition': 0,
                    'grade': 'F',
                    'friction_points': ['No interactions to analyze']
                },
                'usability_insights': ['No interactions detected - unable to analyze usability'],
                'grade_calculation': {
                    'method': 'cognitive_load_based',
                    'formula': 'weighted_average_of_5_factors',
                    'weights': {
                        'prompt_complexity': 0.15,
                        'context_switching': 0.20,
                        'retry_frustration': 0.30,
                        'configuration_friction': 0.25,
                        'integration_cognition': 0.10
                    },
                    'thresholds': {
                        'A': '0-20 (Excellent UX)',
                        'B': '21-40 (Good UX)',
                        'C': '41-60 (Acceptable UX)',
                        'D': '61-80 (Poor UX)',
                        'F': '81-100 (Critical UX Issues)'
                    }
                }
            }
        
        try:
            # Import cognitive analyzer
            from ..analyzers.cognitive_analyzer import CognitiveAnalyzer
            
            analyzer = CognitiveAnalyzer()
            
            # Analyze each interaction and compute average cognitive load
            cognitive_loads = []
            all_issues = []
            
            for interaction in interactions:
                cognitive_load = await analyzer.analyze_interaction(interaction)
                
                # Validate cognitive load to prevent None values
                if cognitive_load:
                    # Ensure all required fields have valid values
                    cognitive_load.overall_score = cognitive_load.overall_score or 50.0
                    cognitive_load.prompt_complexity = cognitive_load.prompt_complexity or 50.0
                    cognitive_load.context_switching = cognitive_load.context_switching or 50.0
                    cognitive_load.retry_frustration = cognitive_load.retry_frustration or 50.0
                    cognitive_load.configuration_friction = cognitive_load.configuration_friction or 50.0
                    cognitive_load.integration_cognition = cognitive_load.integration_cognition or 50.0
                    
                    cognitive_loads.append(cognitive_load)
                
                # Detect issues for this interaction
                issues = await analyzer.detect_usability_issues([interaction])
                all_issues.extend(issues)
            
            # Calculate average cognitive load metrics
            if cognitive_loads:
                # Get breakdown information from the most recent interaction
                latest_load = cognitive_loads[-1]  # Most recent interaction
                retry_breakdown = getattr(latest_load, 'retry_breakdown', None)
                configuration_breakdown = getattr(latest_load, 'configuration_breakdown', None)
                
                # Calculate averages with None handling
                avg_cognitive_load = {
                    'overall_score': round(sum(cl.overall_score or 0 for cl in cognitive_loads) / len(cognitive_loads), 1),
                    'prompt_complexity': round(sum(cl.prompt_complexity or 0 for cl in cognitive_loads) / len(cognitive_loads), 1),
                    'context_switching': round(sum(cl.context_switching or 0 for cl in cognitive_loads) / len(cognitive_loads), 1),
                    'retry_frustration': round(sum(cl.retry_frustration or 0 for cl in cognitive_loads) / len(cognitive_loads), 1),
                    'configuration_friction': round(sum(cl.configuration_friction or 0 for cl in cognitive_loads) / len(cognitive_loads), 1),
                    'integration_cognition': round(sum(cl.integration_cognition or 0 for cl in cognitive_loads) / len(cognitive_loads), 1)
                }
                
                # Add breakdown information if available
                if retry_breakdown:
                    avg_cognitive_load['retry_breakdown'] = retry_breakdown
                if configuration_breakdown:
                    avg_cognitive_load['configuration_breakdown'] = configuration_breakdown
            else:
                avg_cognitive_load = {
                    'overall_score': 50.0,
                    'prompt_complexity': 50.0,
                    'context_switching': 50.0,
                    'retry_frustration': 50.0,
                    'configuration_friction': 50.0,
                    'integration_cognition': 50.0
                }
            
            # Calculate cognitive load grade
            overall_score = avg_cognitive_load['overall_score']
            if overall_score <= 20:
                grade = 'A'
            elif overall_score <= 40:
                grade = 'B'
            elif overall_score <= 60:
                grade = 'C'
            elif overall_score <= 80:
                grade = 'D'
            else:
                grade = 'F'
            
            avg_cognitive_load['grade'] = grade
            
            # Generate friction points
            friction_points = []
            if avg_cognitive_load.get('prompt_complexity', 0) and avg_cognitive_load['prompt_complexity'] > 60:
                friction_points.append('High prompt complexity detected')
            if avg_cognitive_load.get('context_switching', 0) and avg_cognitive_load['context_switching'] > 60:
                friction_points.append('Frequent context switching required')
            if avg_cognitive_load.get('retry_frustration', 0) and avg_cognitive_load['retry_frustration'] > 60:
                friction_points.append('Users experiencing retry frustration')
            if avg_cognitive_load.get('configuration_friction', 0) and avg_cognitive_load['configuration_friction'] > 60:
                friction_points.append('Configuration complexity causing friction')
            if avg_cognitive_load.get('integration_cognition', 0) and avg_cognitive_load['integration_cognition'] > 60:
                friction_points.append('Tool integration complexity')
            
            if not friction_points:
                friction_points.append('No significant friction points detected')
            
            avg_cognitive_load['friction_points'] = friction_points
            
            # Generate usability insights
            insights = []
            
            # Performance insights
            avg_duration = sum(f.get('duration_ms', 0) for f in flows) / len(flows) / 1000 if flows else 0
            if avg_duration < 10:
                insights.append(f"Excellent response time - {avg_duration:.1f}s average keeps users engaged")
            elif avg_duration < 30:
                insights.append(f"Good response time - {avg_duration:.1f}s average provides smooth experience")
            elif avg_duration < 60:
                insights.append(f"Moderate response time - {avg_duration:.1f}s may benefit from optimization")
            else:
                insights.append(f"Slow response time - {avg_duration:.1f}s average may cause user frustration")
            
            # Success rate insights
            successful_flows = sum(1 for f in flows if f.get('success', False))
            success_rate = successful_flows / len(flows) if flows else 0
            if success_rate == 1.0:
                insights.append("Perfect reliability - all interactions completed successfully")
            elif success_rate >= 0.95:
                insights.append(f"Excellent reliability - {success_rate:.1%} success rate")
            elif success_rate >= 0.8:
                insights.append(f"Good reliability - {success_rate:.1%} success rate with room for improvement")
            else:
                insights.append(f"Poor reliability - {success_rate:.1%} success rate needs attention")
            
            # LLM reasoning insights
            llm_flows = sum(1 for f in flows if f.get('llm_reasoning'))
            if llm_flows == len(flows):
                insights.append("Perfect LLM integration - tool selection working flawlessly")
            elif llm_flows >= len(flows) * 0.8:
                insights.append("Good LLM integration - most interactions have proper reasoning")
            else:
                insights.append("LLM integration needs improvement - missing reasoning in some interactions")
            
            # Cognitive load insights
            if overall_score <= 20:
                insights.append("Outstanding cognitive experience - users can focus on their goals")
            elif overall_score <= 40:
                insights.append("Good cognitive experience - minimal mental overhead")
            elif overall_score <= 60:
                insights.append("Acceptable cognitive load - some optimization opportunities exist")
            else:
                insights.append("High cognitive load detected - users may struggle with complexity")
            
            return {
                'cognitive_load': avg_cognitive_load,
                'usability_insights': insights,
                'grade_calculation': {
                    'method': 'cognitive_load_based',
                    'formula': 'weighted_average_of_5_factors',
                    'weights': {
                        'prompt_complexity': 0.15,
                        'context_switching': 0.20,
                        'retry_frustration': 0.30,
                        'configuration_friction': 0.25,
                        'integration_cognition': 0.10
                    },
                    'thresholds': {
                        'A': '0-20 (Excellent UX)',
                        'B': '21-40 (Good UX)', 
                        'C': '41-60 (Acceptable UX)',
                        'D': '61-80 (Poor UX)',
                        'F': '81-100 (Critical UX Issues)'
                    },
                    'current_score': overall_score,
                    'explanation': f'Score {overall_score} = (prompt:{avg_cognitive_load["prompt_complexity"]}×0.15) + (context:{avg_cognitive_load["context_switching"]}×0.20) + (retry:{avg_cognitive_load["retry_frustration"]}×0.30) + (config:{avg_cognitive_load["configuration_friction"]}×0.25) + (integration:{avg_cognitive_load["integration_cognition"]}×0.10)'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in cognitive analysis: {e}")
            return {
                'cognitive_load': {
                    'overall_score': 50,
                    'grade': 'C',
                    'friction_points': ['Error in cognitive analysis']
                },
                'usability_insights': ['Unable to generate insights due to analysis error'],
                'grade_calculation': {
                    'method': 'cognitive_load_based',
                    'error': str(e)
                }
            } 