"""
Cursor MCP Host Adapter.

Implements integration with Cursor IDE for monitoring MCP communications.
"""

import os
import json
import asyncio
import psutil
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

from .base import HostAdapter
from ..core.models import (
    HostInfo, 
    MCPMessageTrace, 
    MCPMessageDirection, 
    MCPProtocol
)
from ..interceptors.live_interceptor import LiveMCPInterceptor

logger = logging.getLogger(__name__)


class CursorAdapter(HostAdapter):
    """
    Cursor IDE adapter for MCP usability monitoring.
    
    Integrates with Cursor to monitor MCP communications between
    the IDE and connected MCP servers like Mastra docs server.
    """
    
    def __init__(self):
        """Initialize Cursor adapter."""
        super().__init__()
        self.cursor_process: Optional[psutil.Process] = None
        self.config_path: Optional[Path] = None
        self.mcp_servers_config: Dict[str, Any] = {}
        self.message_buffer: List[MCPMessageTrace] = []
        self.is_monitoring = False
        
        # Advanced live interception
        self.live_interceptor = LiveMCPInterceptor()
        self.real_messages_captured = False
        
    async def detect_environment(self) -> bool:
        """
        Detect if Cursor is running and has MCP configuration.
        
        Returns:
            True if Cursor environment is detected
        """
        try:
            # Check if Cursor process is running
            cursor_process = self._find_cursor_process()
            if not cursor_process:
                logger.debug("Cursor process not found")
                return False
            
            # Check for Cursor configuration directory
            config_path = self._find_cursor_config_path()
            if not config_path or not config_path.exists():
                logger.debug("Cursor config directory not found")
                return False
            
            # Check for MCP configuration
            mcp_config_file = config_path / "mcp.json"
            if not mcp_config_file.exists():
                logger.debug(f"MCP configuration not found at: {mcp_config_file}")
                return False
            
            logger.info("Cursor environment detected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error detecting Cursor environment: {e}")
            return False
    
    async def initialize(self) -> None:
        """Initialize connection to Cursor."""
        try:
            # Find and store Cursor process
            self.cursor_process = self._find_cursor_process()
            if not self.cursor_process:
                raise RuntimeError("Cursor process not found")
            
            # Find and store config path
            self.config_path = self._find_cursor_config_path()
            if not self.config_path:
                raise RuntimeError("Cursor config path not found")
            
            # Load MCP servers configuration
            await self._load_mcp_config()
            
            # Set up host info
            self.host_info = HostInfo(
                name="Cursor",
                version=await self._get_cursor_version(),
                type="cursor",
                mcp_protocol_version="2025-06-18",  # Assume latest
                connected_servers=list(self.mcp_servers_config.keys())
            )
            
            # Start monitoring MCP communications
            await self._start_mcp_monitoring()
            
            self.is_initialized = True
            logger.info(f"Cursor adapter initialized with {len(self.mcp_servers_config)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cursor adapter: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up Cursor adapter resources."""
        try:
            self.is_monitoring = False
            
            # Stop live interceptor
            if self.live_interceptor.is_active:
                await self.live_interceptor.stop_interception()
            
            self.message_buffer.clear()
            self.is_initialized = False
            logger.info("Cursor adapter cleaned up")
            
        except Exception as e:
            logger.error(f"Error during Cursor adapter cleanup: {e}")
    
    async def get_host_info(self) -> HostInfo:
        """Get Cursor host information."""
        if not self.host_info:
            raise RuntimeError("Cursor adapter not initialized")
        return self.host_info
    
    async def stream_mcp_messages(self) -> AsyncGenerator[MCPMessageTrace, None]:
        """
        Stream MCP messages as they occur using advanced live interception.
        
        This implementation uses multiple methods to capture real MCP communications
        between Cursor and MCP servers like Mastra docs server.
        """
        logger.info("Starting advanced MCP message streaming...")
        
        # Start the live interceptor
        if not self.live_interceptor.is_active:
            success = await self.live_interceptor.start_interception()
            if not success:
                logger.warning("Failed to start live interception")
        
        while self.is_monitoring and self.is_initialized:
            try:
                # Get captured messages from live interceptor
                captured_messages = await self.live_interceptor.get_captured_messages()
                
                if captured_messages:
                    self.real_messages_captured = True
                    logger.info(f"Yielding {len(captured_messages)} real MCP messages")
                    
                    for message in captured_messages:
                        yield message
                else:
                    # Brief pause when no messages available
                    await asyncio.sleep(0.5)
                        
            except Exception as e:
                logger.error(f"Error in message streaming: {e}")
                await asyncio.sleep(1.0)
    
    async def get_connected_servers(self) -> List[str]:
        """Get list of connected MCP servers."""
        return list(self.mcp_servers_config.keys())
    
    async def get_server_capabilities(self, server_name: str) -> Dict[str, Any]:
        """Get capabilities of a specific MCP server."""
        if server_name not in self.mcp_servers_config:
            return {}
        
        # For OpenWeather, return known capabilities
        if "openweather" in server_name.lower():
            return {
                "tools": [
                    "getCurrentWeather",
                    "getForecast", 
                    "getAirQuality",
                    "searchLocation"
                ],
                "resources": [],
                "prompts": [],
                "version": "1.0.0",
                "authentication": "api_key",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "requests_per_day": 1000
                }
            }
        
        # Generic server capabilities
        return {
            "tools": [],
            "resources": [],
            "prompts": [],
            "version": "unknown"
        }
    
    def _find_cursor_process(self) -> Optional[psutil.Process]:
        """Find running Cursor process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    # Check for Cursor process names
                    if proc.info['name'] and 'cursor' in proc.info['name'].lower():
                        return proc
                    
                    # Check for Cursor executable path
                    if proc.info['exe'] and 'cursor' in proc.info['exe'].lower():
                        return proc
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Cursor process: {e}")
            return None
    
    def _find_cursor_config_path(self) -> Optional[Path]:
        """Find Cursor configuration directory."""
        try:
            # Cursor config paths to check
            possible_paths = []
            
            # First priority: Workspace .cursor directory
            import os
            current_dir = Path.cwd()
            workspace_cursor = current_dir / ".cursor"
            if workspace_cursor.exists() and workspace_cursor.is_dir():
                possible_paths.append(workspace_cursor)
                logger.debug(f"Found workspace Cursor config at: {workspace_cursor}")
            
            # Second priority: Global Cursor config paths
            if os.name == 'nt':  # Windows
                appdata = os.getenv('APPDATA')
                if appdata:
                    possible_paths.extend([
                        Path(appdata) / "Cursor" / "User",
                        Path(appdata) / "cursor" / "User",
                    ])
            else:  # macOS/Linux
                home = Path.home()
                possible_paths.extend([
                    home / ".cursor",
                    home / ".config" / "Cursor" / "User",
                    home / ".config" / "cursor" / "User",
                    home / "Library" / "Application Support" / "Cursor" / "User",  # macOS
                ])
            
            # Check each possible path for MCP config
            for path in possible_paths:
                if path.exists() and path.is_dir():
                    # Check if MCP config exists
                    mcp_config_file = path / "mcp.json"
                    if mcp_config_file.exists():
                        logger.debug(f"Found Cursor config with MCP at: {path}")
                        return path
                    else:
                        logger.debug(f"Cursor config found but no mcp.json at: {path}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Cursor config path: {e}")
            return None
    
    async def _load_mcp_config(self) -> None:
        """Load MCP servers configuration from Cursor."""
        try:
            if not self.config_path:
                return
            
            mcp_config_file = self.config_path / "mcp.json"
            if not mcp_config_file.exists():
                logger.warning(f"MCP config file not found at: {mcp_config_file}")
                return
            
            with open(mcp_config_file, 'r') as f:
                config_data = json.load(f)
            
            # Extract MCP servers configuration
            self.mcp_servers_config = config_data.get('mcpServers', {})
            
            logger.info(f"Loaded MCP config from {mcp_config_file} with {len(self.mcp_servers_config)} servers: {list(self.mcp_servers_config.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            self.mcp_servers_config = {}
    
    async def _get_cursor_version(self) -> str:
        """Get Cursor version."""
        try:
            # Try to get version from process info
            if self.cursor_process:
                try:
                    # This is a simplified approach
                    # In reality, we'd need to read Cursor's package.json or similar
                    return "1.0.0"  # Placeholder
                except Exception:
                    pass
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error getting Cursor version: {e}")
            return "unknown"
    
    async def _start_mcp_monitoring(self) -> None:
        """Start monitoring MCP communications."""
        try:
            self.is_monitoring = True
            
            # This is a simplified implementation
            # In a real implementation, we would:
            # 1. Hook into Cursor's internal MCP client
            # 2. Intercept JSON-RPC messages
            # 3. Parse and analyze the communication patterns
            
            logger.info("MCP monitoring started (simplified implementation)")
            
        except Exception as e:
            logger.error(f"Error starting MCP monitoring: {e}")
            self.is_monitoring = False
    
    async def get_live_interception_status(self) -> Dict[str, Any]:
        """Get status of live MCP interception."""
        try:
            status = self.live_interceptor.get_status()
            status['real_messages_captured'] = self.real_messages_captured
            return status
        except Exception as e:
            logger.error(f"Error getting live interception status: {e}")
            return {"error": str(e)}
    
    async def record_real_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """
        Record a real MCP interaction when detected.
        
        This method can be called by external monitoring tools
        to feed real interaction data into the audit system.
        """
        try:
            from datetime import datetime
            from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol
            
            # Convert interaction data to MCPMessageTrace
            trace = MCPMessageTrace(
                direction=MCPMessageDirection.LLM_TO_MCP_CLIENT,
                protocol=MCPProtocol.JSON_RPC,
                payload=interaction_data,
                timestamp=datetime.utcnow(),
                latency_ms=interaction_data.get('latency_ms')
            )
            
            # Add to message buffer for processing
            self.message_buffer.append(trace)
            
            logger.info(f"Recorded real MCP interaction: {interaction_data.get('method', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error recording real interaction: {e}") 