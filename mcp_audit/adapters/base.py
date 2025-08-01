"""
Base host adapter interface.

Defines the contract for all MCP host integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

from ..core.models import MCPInteraction, HostInfo, MCPMessageTrace

logger = logging.getLogger(__name__)


class HostAdapter(ABC):
    """
    Abstract base class for MCP host adapters.
    
    Each MCP host (Cursor, Claude Desktop, Windsurf, etc.) has its own
    adapter that implements this interface to provide unified access to
    MCP communications.
    """
    
    def __init__(self):
        """Initialize the host adapter."""
        self.is_initialized = False
        self.host_info: Optional[HostInfo] = None
        
    @abstractmethod
    async def detect_environment(self) -> bool:
        """
        Detect if this adapter's target host is available.
        
        Returns:
            True if the target host environment is detected, False otherwise
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the adapter and establish connection to the host.
        
        Raises:
            Exception: If initialization fails
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        pass
    
    @abstractmethod
    async def get_host_info(self) -> HostInfo:
        """
        Get information about the host environment.
        
        Returns:
            Host information including version, type, connected servers
        """
        pass
    
    @abstractmethod
    async def stream_mcp_messages(self) -> AsyncGenerator[MCPMessageTrace, None]:
        """
        Stream MCP messages as they occur.
        
        Yields:
            MCPMessageTrace objects for each intercepted message
        """
        pass
    
    @abstractmethod
    async def get_connected_servers(self) -> List[str]:
        """
        Get list of currently connected MCP servers.
        
        Returns:
            List of server names
        """
        pass
    
    @abstractmethod
    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific MCP server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server capabilities dictionary
        """
        pass
    
    async def is_available(self) -> bool:
        """
        Check if the host is currently available and responsive.
        
        Returns:
            True if host is available, False otherwise
        """
        try:
            return await self.detect_environment() and self.is_initialized
        except Exception as e:
            logger.error(f"Error checking host availability: {e}")
            return False
    
    def get_adapter_name(self) -> str:
        """Get the name of this adapter."""
        return self.__class__.__name__
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about this adapter."""
        return {
            "name": self.get_adapter_name(),
            "initialized": self.is_initialized,
            "host_info": self.host_info.dict() if self.host_info else None
        } 