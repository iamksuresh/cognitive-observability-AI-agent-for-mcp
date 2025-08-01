"""
Enterprise integrations for MCP audit data export.
"""

import logging

logger = logging.getLogger(__name__)

# Import base classes that should always be available
from .manager import IntegrationManager
from .base import BaseIntegration

# Gracefully import optional integrations
__all__ = [
    "BaseIntegration",
    "IntegrationManager"
]

# Try to import each integration, but don't fail if dependencies are missing
try:
    from .langsmith import LangSmithIntegration
    __all__.append("LangSmithIntegration")
except ImportError as e:
    logger.debug(f"LangSmith integration not available: {e}")

try:
    from .mixpanel import MixpanelIntegration
    __all__.append("MixpanelIntegration")
except ImportError as e:
    logger.debug(f"Mixpanel integration not available: {e}")

try:
    from .posthog import PostHogIntegration
    __all__.append("PostHogIntegration")
except ImportError as e:
    logger.debug(f"PostHog integration not available: {e}")

try:
    from .opentelemetry import OpenTelemetryIntegration
    __all__.append("OpenTelemetryIntegration")
except ImportError as e:
    logger.debug(f"OpenTelemetry integration not available: {e}")
    logger.info("Install 'mcp-audit-agent[integrations]' for full OpenTelemetry support") 