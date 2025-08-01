"""
Mixpanel integration for MCP audit analytics.
"""

import json
import base64
from typing import Dict, Any, List, Optional
import aiohttp

from ..core.models import UsabilityReport, MCPMessageTrace
from .base import BaseIntegration


class MixpanelIntegration(BaseIntegration):
    """Integration with Mixpanel for user analytics and cognitive insights."""
    
    def __init__(self, api_key: str, project_token: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        self.project_token = project_token
        self.base_url = "https://api.mixpanel.com"
    
    async def send_usability_report(self, report: UsabilityReport) -> bool:
        """Send usability report as Mixpanel event."""
        try:
            event_data = {
                "event": "MCP Usability Analysis",
                "properties": {
                    "token": self.project_token,
                    "distinct_id": f"mcp_audit_{report.server_name}",
                    "time": int(report.generated_at.timestamp()),
                    "server_name": report.server_name,
                    "usability_score": report.overall_usability_score,
                    "grade": report.grade,
                    "cognitive_load_overall": report.cognitive_load.overall_score,
                    "cognitive_load_prompt_complexity": report.cognitive_load.prompt_complexity,
                    "cognitive_load_context_switching": report.cognitive_load.context_switching,
                    "cognitive_load_retry_frustration": report.cognitive_load.retry_frustration,
                    "cognitive_load_configuration_friction": report.cognitive_load.configuration_friction,
                    "cognitive_load_integration_cognition": report.cognitive_load.integration_cognition,
                    "total_sessions": report.session_summary.total_sessions,
                    "successful_completions": report.session_summary.successful_completions,
                    "abandonment_rate": report.session_summary.abandonment_rate,
                    "avg_response_time_ms": report.communication_patterns.avg_response_time_ms,
                    "retry_rate": report.communication_patterns.retry_rate,
                    "first_attempt_success_rate": report.communication_patterns.first_attempt_success_rate,
                    "category": "cognitive_observability",
                    "source": "mcp_audit_agent"
                }
            }
            
            return await self._send_event(event_data)
            
        except Exception as e:
            print(f"❌ Mixpanel usability report error: {e}")
            return False
    
    async def send_cognitive_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send cognitive metrics as Mixpanel events."""
        try:
            event_data = {
                "event": "Cognitive Load Metrics",
                "properties": {
                    "token": self.project_token,
                    "distinct_id": f"mcp_audit_{metrics.get('server', 'unknown')}",
                    "category": "cognitive_metrics",
                    "source": "mcp_audit_agent",
                    **metrics
                }
            }
            
            return await self._send_event(event_data)
            
        except Exception as e:
            print(f"❌ Mixpanel cognitive metrics error: {e}")
            return False
    
    async def send_trace_data(self, traces: List[MCPMessageTrace]) -> bool:
        """Send MCP traces as Mixpanel events."""
        try:
            for trace in traces:
                event_data = {
                    "event": "MCP Message Trace",
                    "properties": {
                        "token": self.project_token,
                        "distinct_id": f"mcp_audit_trace_{trace.timestamp.isoformat()}",
                        "time": int(trace.timestamp.timestamp()),
                        "direction": trace.direction.value,
                        "protocol": trace.protocol.value,
                        "latency_ms": trace.latency_ms,
                        "error_code": trace.error_code,
                        "message_type": trace.payload.get("method", "unknown"),
                        "category": "mcp_trace",
                        "source": "mcp_audit_agent"
                    }
                }
                
                success = await self._send_event(event_data)
                if not success:
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Mixpanel trace data error: {e}")
            return False
    
    async def _send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send a single event to Mixpanel."""
        try:
            # Encode event data
            event_json = json.dumps(event_data)
            event_encoded = base64.b64encode(event_json.encode()).decode()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/track",
                    data={"data": event_encoded}
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _test_api_connection(self) -> bool:
        """Test Mixpanel API connection."""
        try:
            test_event = {
                "event": "MCP Audit Connection Test",
                "properties": {
                    "token": self.project_token,
                    "distinct_id": "test_connection",
                    "source": "mcp_audit_agent"
                }
            }
            
            return await self._send_event(test_event)
            
        except Exception:
            return False 