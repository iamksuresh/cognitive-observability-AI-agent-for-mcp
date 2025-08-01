"""
PostHog integration for MCP audit analytics.
"""

from typing import Dict, Any, List, Optional
import aiohttp

from ..core.models import UsabilityReport, MCPMessageTrace
from .base import BaseIntegration


class PostHogIntegration(BaseIntegration):
    """Integration with PostHog for product analytics and user behavior."""
    
    def __init__(self, api_key: str, host: str = "https://app.posthog.com", config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        self.host = host.rstrip('/')
    
    async def send_usability_report(self, report: UsabilityReport) -> bool:
        """Send usability report as PostHog event."""
        try:
            event_data = {
                "api_key": self.api_key,
                "event": "mcp_usability_analysis",
                "distinct_id": f"mcp_audit_{report.server_name}",
                "timestamp": report.generated_at.isoformat(),
                "properties": {
                    "server_name": report.server_name,
                    "usability_score": report.overall_usability_score,
                    "grade": report.grade,
                    "cognitive_load": {
                        "overall": report.cognitive_load.overall_score,
                        "prompt_complexity": report.cognitive_load.prompt_complexity,
                        "context_switching": report.cognitive_load.context_switching,
                        "retry_frustration": report.cognitive_load.retry_frustration,
                        "configuration_friction": report.cognitive_load.configuration_friction,
                        "integration_cognition": report.cognitive_load.integration_cognition
                    },
                    "session_summary": {
                        "total_sessions": report.session_summary.total_sessions,
                        "successful_completions": report.session_summary.successful_completions,
                        "abandonment_rate": report.session_summary.abandonment_rate
                    },
                    "communication_patterns": {
                        "avg_response_time_ms": report.communication_patterns.avg_response_time_ms,
                        "retry_rate": report.communication_patterns.retry_rate,
                        "first_attempt_success_rate": report.communication_patterns.first_attempt_success_rate
                    },
                    "$set": {
                        "server_type": "mcp",
                        "analysis_tool": "mcp_audit_agent"
                    }
                }
            }
            
            return await self._send_event(event_data)
            
        except Exception as e:
            print(f"❌ PostHog usability report error: {e}")
            return False
    
    async def send_cognitive_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send cognitive metrics as PostHog events."""
        try:
            event_data = {
                "api_key": self.api_key,
                "event": "cognitive_load_metrics",
                "distinct_id": f"mcp_audit_{metrics.get('server', 'unknown')}",
                "properties": {
                    **metrics,
                    "$set": {
                        "analysis_tool": "mcp_audit_agent",
                        "metric_type": "cognitive_load"
                    }
                }
            }
            
            return await self._send_event(event_data)
            
        except Exception as e:
            print(f"❌ PostHog cognitive metrics error: {e}")
            return False
    
    async def send_trace_data(self, traces: List[MCPMessageTrace]) -> bool:
        """Send MCP traces as PostHog events."""
        try:
            events = []
            
            for trace in traces:
                event_data = {
                    "api_key": self.api_key,
                    "event": "mcp_message_trace",
                    "distinct_id": f"mcp_trace_{trace.timestamp.isoformat()}",
                    "timestamp": trace.timestamp.isoformat(),
                    "properties": {
                        "direction": trace.direction.value,
                        "protocol": trace.protocol.value,
                        "latency_ms": trace.latency_ms,
                        "error_code": trace.error_code,
                        "message_method": trace.payload.get("method", "unknown"),
                        "has_error": trace.error_code is not None,
                        "$set": {
                            "trace_source": "mcp_audit_agent"
                        }
                    }
                }
                events.append(event_data)
            
            # Send events in batch
            return await self._send_batch_events(events)
            
        except Exception as e:
            print(f"❌ PostHog trace data error: {e}")
            return False
    
    async def _send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send a single event to PostHog."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/capture/",
                    json=event_data
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _send_batch_events(self, events: List[Dict[str, Any]]) -> bool:
        """Send multiple events to PostHog in batch."""
        try:
            batch_data = {
                "api_key": self.api_key,
                "batch": events
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/batch/",
                    json=batch_data
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _test_api_connection(self) -> bool:
        """Test PostHog API connection."""
        try:
            test_event = {
                "api_key": self.api_key,
                "event": "mcp_audit_connection_test",
                "distinct_id": "test_connection",
                "properties": {
                    "source": "mcp_audit_agent",
                    "test": True
                }
            }
            
            return await self._send_event(test_event)
            
        except Exception:
            return False 