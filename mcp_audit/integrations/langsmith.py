"""
LangSmith integration for MCP audit data.
"""

import json
from typing import Dict, Any, List, Optional
import aiohttp

from ..core.models import UsabilityReport, MCPMessageTrace
from .base import BaseIntegration


class LangSmithIntegration(BaseIntegration):
    """Integration with LangSmith for tracing and observability."""
    
    def __init__(self, api_key: str, project_name: str = "mcp-audit", config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        self.project_name = project_name
        self.base_url = "https://api.smith.langchain.com"
    
    async def send_usability_report(self, report: UsabilityReport) -> bool:
        """Send usability report as LangSmith trace."""
        try:
            trace_data = {
                "name": f"MCP Usability Analysis - {report.server_name}",
                "project_name": self.project_name,
                "start_time": report.generated_at.isoformat(),
                "end_time": report.generated_at.isoformat(),
                "inputs": {
                    "server_name": report.server_name,
                    "analysis_window_hours": report.analysis_window_hours
                },
                "outputs": {
                    "usability_score": report.overall_usability_score,
                    "grade": report.grade,
                    "cognitive_load": report.cognitive_load.dict(),
                    "recommendations": report.recommendations
                },
                "tags": ["mcp-audit", "usability-analysis"],
                "metadata": {
                    "session_summary": report.session_summary.dict(),
                    "communication_patterns": report.communication_patterns.dict()
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/runs",
                    json=trace_data,
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ LangSmith integration error: {e}")
            return False
    
    async def send_cognitive_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send cognitive metrics as LangSmith events."""
        try:
            event_data = {
                "name": "cognitive_load_analysis",
                "project_name": self.project_name,
                "inputs": metrics,
                "tags": ["cognitive-metrics", "mcp-audit"]
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/runs",
                    json=event_data,
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"❌ LangSmith cognitive metrics error: {e}")
            return False
    
    async def send_trace_data(self, traces: List[MCPMessageTrace]) -> bool:
        """Send MCP traces to LangSmith."""
        try:
            for trace in traces:
                trace_data = {
                    "name": f"MCP Message - {trace.direction.value}",
                    "project_name": self.project_name,
                    "start_time": trace.timestamp.isoformat(),
                    "end_time": trace.timestamp.isoformat(),
                    "inputs": {
                        "direction": trace.direction.value,
                        "protocol": trace.protocol.value
                    },
                    "outputs": trace.payload,
                    "tags": ["mcp-trace", trace.protocol.value.lower()],
                    "metadata": {
                        "latency_ms": trace.latency_ms,
                        "error_code": trace.error_code
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/runs",
                        json=trace_data,
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            return False
            
            return True
            
        except Exception as e:
            print(f"❌ LangSmith trace data error: {e}")
            return False
    
    async def _test_api_connection(self) -> bool:
        """Test LangSmith API connection."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/projects",
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False 