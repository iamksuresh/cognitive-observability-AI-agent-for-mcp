"""
Integration Manager - Orchestrates sending data to configured integrations.

Loads configured integrations and automatically sends usability reports
and trace data to platforms like OpenTelemetry, Mixpanel, PostHog, etc.
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ..core.models import UsabilityReport, MCPMessageTrace, MCPInteraction

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Manages and orchestrates data sending to configured integrations."""
    
    def __init__(self):
        self.integrations = {}
        self.config_file = Path.home() / ".mcp-audit" / "integrations.json"
        self._load_configured_integrations()
    
    def _load_configured_integrations(self):
        """Load configured integrations from config file."""
        try:
            if not self.config_file.exists():
                logger.info("Creating default integrations configuration with OpenTelemetry enabled")
                self._create_default_config()
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            for platform, settings in config.items():
                if settings.get("enabled", False):
                    integration = self._create_integration(platform, settings)
                    if integration:
                        self.integrations[platform] = integration
                        logger.info(f"✅ Loaded {platform} integration")
        
        except Exception as e:
            logger.error(f"Error loading integrations: {e}")
    
    def _create_default_config(self):
        """Create default integrations configuration with OpenTelemetry enabled."""
        default_config = {
            "opentelemetry": {
                "service_name": "mcp-audit-agent",
                "jaeger_endpoint": "http://localhost:14268/api/traces",
                "prometheus_port": 8889,
                "enabled": True,
                "real_time_export": True,
                "export_interval_seconds": 5
            }
        }
        
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default configuration
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"✅ Created default integrations config at {self.config_file}")
    
    def _create_integration(self, platform: str, settings: Dict[str, Any]):
        """Create an integration instance based on platform and settings."""
        try:
            if platform == "opentelemetry":
                from .opentelemetry import OpenTelemetryIntegration
                return OpenTelemetryIntegration(
                    service_name=settings.get("service_name", "mcp-audit-agent"),
                    jaeger_endpoint=settings.get("jaeger_endpoint"),
                    prometheus_port=settings.get("prometheus_port", 8889),
                    real_time_export=settings.get("real_time_export", True),
                    export_interval=settings.get("export_interval_seconds", 5)
                )
            
            elif platform == "mixpanel":
                from .mixpanel import MixpanelIntegration
                return MixpanelIntegration(
                    api_key=settings.get("api_key"),
                    project_token=settings.get("project_token")
                )
            
            elif platform == "posthog":
                from .posthog import PostHogIntegration
                return PostHogIntegration(
                    api_key=settings.get("api_key"),
                    host=settings.get("host", "https://app.posthog.com")
                )
            
            elif platform == "langsmith":
                from .langsmith import LangSmithIntegration
                return LangSmithIntegration(
                    api_key=settings.get("api_key"),
                    project_name=settings.get("project_name", "mcp-audit")
                )
            
            else:
                logger.warning(f"Unknown integration platform: {platform}")
                return None
                
        except ImportError as e:
            logger.warning(f"Failed to load {platform} integration: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating {platform} integration: {e}")
            return None
    
    async def send_usability_report(self, report: UsabilityReport) -> Dict[str, bool]:
        """Send usability report to all configured integrations."""
        results = {}
        
        for platform, integration in self.integrations.items():
            try:
                logger.debug(f"Sending usability report to {platform}")
                success = await integration.send_usability_report(report)
                results[platform] = success
                
                if success:
                    logger.info(f"✅ Sent usability report to {platform}")
                else:
                    logger.warning(f"⚠️ Failed to send usability report to {platform}")
                    
            except Exception as e:
                logger.error(f"❌ Error sending to {platform}: {e}")
                results[platform] = False
        
        return results
    
    async def send_trace_data(self, traces: List[MCPMessageTrace]) -> Dict[str, bool]:
        """Send trace data to all configured integrations."""
        results = {}
        
        for platform, integration in self.integrations.items():
            try:
                logger.debug(f"Sending {len(traces)} traces to {platform}")
                success = await integration.send_trace_data(traces)
                results[platform] = success
                
                if success:
                    logger.info(f"✅ Sent {len(traces)} traces to {platform}")
                else:
                    logger.warning(f"⚠️ Failed to send traces to {platform}")
                    
            except Exception as e:
                logger.error(f"❌ Error sending traces to {platform}: {e}")
                results[platform] = False
        
        return results
    
    async def send_cognitive_metrics(self, metrics: Dict[str, Any]) -> Dict[str, bool]:
        """Send cognitive metrics to all configured integrations."""
        results = {}
        
        for platform, integration in self.integrations.items():
            try:
                if hasattr(integration, 'send_cognitive_metrics'):
                    success = await integration.send_cognitive_metrics(metrics)
                    results[platform] = success
                    
                    if success:
                        logger.info(f"✅ Sent cognitive metrics to {platform}")
                else:
                    logger.debug(f"Platform {platform} doesn't support cognitive metrics")
                    results[platform] = True  # Not an error
                    
            except Exception as e:
                logger.error(f"❌ Error sending cognitive metrics to {platform}: {e}")
                results[platform] = False
        
        return results
    
    async def send_interactions(self, interactions: List[MCPInteraction]) -> Dict[str, bool]:
        """Send MCP interactions to integrations (extracts traces automatically)."""
        # Extract all traces from interactions
        all_traces = []
        for interaction in interactions:
            all_traces.extend(interaction.message_traces)
        
        if all_traces:
            return await self.send_trace_data(all_traces)
        else:
            logger.debug("No traces found in interactions")
            return {}
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all configured integrations."""
        return {
            "configured_integrations": list(self.integrations.keys()),
            "total_integrations": len(self.integrations),
            "config_file": str(self.config_file),
            "integrations_available": {
                platform: integration.get_enhancement_status() 
                if hasattr(integration, 'get_enhancement_status') 
                else {"status": "active"}
                for platform, integration in self.integrations.items()
            }
        }
    
    def reload_integrations(self):
        """Reload integrations from config file."""
        logger.info("🔄 Reloading integrations...")
        self.integrations.clear()
        self._load_configured_integrations()
        
        configured_count = len(self.integrations)
        logger.info(f"✅ Reloaded {configured_count} integrations")
        
        return configured_count > 0 