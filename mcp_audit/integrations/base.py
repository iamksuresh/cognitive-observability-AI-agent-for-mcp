"""
Base class for enterprise integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.models import UsabilityReport, MCPMessageTrace


class BaseIntegration(ABC):
    """Base class for all enterprise platform integrations."""
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
        self.enabled = bool(api_key)
    
    @abstractmethod
    async def send_usability_report(self, report: UsabilityReport) -> bool:
        """Send a usability report to the platform."""
        pass
    
    @abstractmethod
    async def send_cognitive_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send cognitive load metrics to the platform."""
        pass
    
    @abstractmethod
    async def send_trace_data(self, traces: List[MCPMessageTrace]) -> bool:
        """Send trace data to the platform."""
        pass
    
    async def test_connection(self) -> bool:
        """Test connection to the platform."""
        try:
            return await self._test_api_connection()
        except Exception:
            return False
    
    @abstractmethod
    async def _test_api_connection(self) -> bool:
        """Platform-specific connection test."""
        pass
    
    def format_cognitive_event(self, event_name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Format an event for the platform."""
        return {
            "event": event_name,
            "properties": {
                **properties,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mcp_audit_agent",
                "category": "cognitive_observability"
            }
        } 