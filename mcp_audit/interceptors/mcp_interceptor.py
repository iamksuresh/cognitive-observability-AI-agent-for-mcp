"""
MCP Communication Interceptor.

Captures and processes MCP messages from host adapters for analysis.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from ..adapters.base import HostAdapter
from ..core.models import (
    MCPInteraction,
    MCPMessageTrace,
    MCPMessageDirection
)

logger = logging.getLogger(__name__)


class MCPCommunicationInterceptor:
    """
    Intercepts and processes MCP communications from host adapters.
    
    Converts raw MCP message traces into structured interaction sessions
    for cognitive analysis.
    """
    
    def __init__(self):
        """Initialize the MCP interceptor."""
        self.host_adapter: Optional[HostAdapter] = None
        self.active_interactions: Dict[str, MCPInteraction] = {}
        self.completed_interactions: List[MCPInteraction] = []
        self.message_buffer: List[MCPMessageTrace] = []
        self.is_active = False
        self.processing_task: Optional[asyncio.Task] = None
        
    async def setup(self, host_adapter: HostAdapter) -> None:
        """
        Set up the interceptor with a host adapter.
        
        Args:
            host_adapter: The host adapter to intercept messages from
        """
        try:
            self.host_adapter = host_adapter
            self.is_active = True
            
            # Start processing messages from the host adapter
            self.processing_task = asyncio.create_task(self._process_messages())
            
            logger.info(f"MCP interceptor set up with {host_adapter.get_adapter_name()}")
            
        except Exception as e:
            logger.error(f"Failed to set up MCP interceptor: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up interceptor resources."""
        try:
            self.is_active = False
            
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            
            # Finalize any remaining active interactions
            for interaction in self.active_interactions.values():
                interaction.end_time = datetime.utcnow()
                self.completed_interactions.append(interaction)
            
            self.active_interactions.clear()
            self.message_buffer.clear()
            
            logger.info("MCP interceptor cleaned up")
            
        except Exception as e:
            logger.error(f"Error during MCP interceptor cleanup: {e}")
    
    async def _process_messages(self) -> None:
        """Main message processing loop."""
        if not self.host_adapter:
            logger.error("No host adapter available for message processing")
            return
        
        try:
            async for message_trace in self.host_adapter.stream_mcp_messages():
                if not self.is_active:
                    break
                
                await self._process_message_trace(message_trace)
                
        except asyncio.CancelledError:
            logger.info("Message processing cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message processing loop: {e}")
    
    async def _process_message_trace(self, message_trace: MCPMessageTrace) -> None:
        """
        Process a single MCP message trace.
        
        Args:
            message_trace: The message trace to process
        """
        try:
            # Determine if this is the start of a new interaction
            interaction_id = self._extract_interaction_id(message_trace)
            
            if interaction_id not in self.active_interactions:
                # Start new interaction
                interaction = self._create_new_interaction(message_trace, interaction_id)
                self.active_interactions[interaction_id] = interaction
            
            # Add message to existing interaction
            interaction = self.active_interactions[interaction_id]
            interaction.message_traces.append(message_trace)
            
            # Check if interaction is complete
            if self._is_interaction_complete(interaction, message_trace):
                await self._finalize_interaction(interaction_id)
            
        except Exception as e:
            logger.error(f"Error processing message trace: {e}")
    
    def _extract_interaction_id(self, message_trace: MCPMessageTrace) -> str:
        """
        Extract or generate an interaction ID from a message trace.
        
        Args:
            message_trace: The message trace
            
        Returns:
            Unique interaction identifier
        """
        # Try to extract from JSON-RPC id or session info
        payload = message_trace.payload
        
        if isinstance(payload, dict):
            # JSON-RPC message
            if 'id' in payload:
                return str(payload['id'])
            
            # Tool call with session context
            if 'params' in payload and isinstance(payload['params'], dict):
                if 'name' in payload['params']:
                    # Generate ID based on tool name and timestamp
                    tool_name = payload['params']['name']
                    timestamp = int(message_trace.timestamp.timestamp())
                    return f"{tool_name}_{timestamp}"
        
        # Generate unique ID based on timestamp and direction
        timestamp = int(message_trace.timestamp.timestamp())
        direction = message_trace.direction.value.replace('→', '_')
        return f"interaction_{direction}_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def _create_new_interaction(
        self, 
        message_trace: MCPMessageTrace, 
        interaction_id: str
    ) -> MCPInteraction:
        """
        Create a new MCP interaction from the first message trace.
        
        Args:
            message_trace: The initial message trace
            interaction_id: Unique interaction identifier
            
        Returns:
            New MCPInteraction object
        """
        # Extract user query and server name from message
        user_query = self._extract_user_query(message_trace)
        server_name = self._extract_server_name(message_trace)
        
        return MCPInteraction(
            session_id=interaction_id,
            server_name=server_name,
            user_query=user_query,
            start_time=message_trace.timestamp,
            message_traces=[],  # Will be added separately
            success=False,  # Will be determined when complete
            retry_count=0,
            user_context={}
        )
    
    def _extract_user_query(self, message_trace: MCPMessageTrace) -> str:
        """Extract user query from message trace."""
        payload = message_trace.payload
        
        if isinstance(payload, dict):
            # Tool call - extract arguments
            if 'params' in payload and isinstance(payload['params'], dict):
                params = payload['params']
                if 'arguments' in params:
                    args = params['arguments']
                    if isinstance(args, dict):
                        # Common query patterns
                        for key in ['query', 'question', 'city', 'location', 'q']:
                            if key in args:
                                return f"Query about {args[key]}"
                        
                        # Fallback to first string value
                        for value in args.values():
                            if isinstance(value, str):
                                return f"Query: {value}"
            
            # HTTP request - extract from URL or params
            if 'url' in payload and 'params' in payload:
                params = payload['params']
                if isinstance(params, dict) and 'q' in params:
                    return f"Weather query for {params['q']}"
        
        return "MCP interaction"
    
    def _extract_server_name(self, message_trace: MCPMessageTrace) -> str:
        """Extract server name from message trace."""
        payload = message_trace.payload
        
        if isinstance(payload, dict):
            # Check URL for API identification
            if 'url' in payload:
                url = payload['url']
                if 'openweathermap.org' in url:
                    return 'openweather'
                elif 'api' in url:
                    return 'external_api'
            
            # Check method/tool name
            if 'params' in payload and isinstance(payload['params'], dict):
                params = payload['params']
                if 'name' in params:
                    tool_name = params['name']
                    if 'weather' in tool_name.lower():
                        return 'openweather'
                    return f"tool_{tool_name}"
        
        return 'unknown_server'
    
    def _is_interaction_complete(
        self, 
        interaction: MCPInteraction, 
        latest_message: MCPMessageTrace
    ) -> bool:
        """
        Determine if an interaction is complete.
        
        Args:
            interaction: The interaction to check
            latest_message: The latest message trace
            
        Returns:
            True if interaction is complete
        """
        # Check for error responses
        if latest_message.error_code:
            return True
        
        # Check for successful API responses
        if (latest_message.direction == MCPMessageDirection.SERVER_TO_API and
            latest_message.latency_ms is not None):
            return True
        
        # Check interaction duration (timeout after 30 seconds)
        duration = latest_message.timestamp - interaction.start_time
        if duration.total_seconds() > 30:
            return True
        
        return False
    
    async def _finalize_interaction(self, interaction_id: str) -> None:
        """
        Finalize a completed interaction.
        
        Args:
            interaction_id: ID of the interaction to finalize
        """
        try:
            interaction = self.active_interactions.pop(interaction_id)
            
            # Set end time
            interaction.end_time = datetime.utcnow()
            
            # Calculate total latency
            if interaction.message_traces:
                start_time = interaction.start_time
                end_time = interaction.end_time or datetime.utcnow()
                interaction.total_latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Determine success status
            interaction.success = self._determine_success(interaction)
            
            # Count retries
            interaction.retry_count = self._count_retries(interaction)
            
            # Add to completed interactions
            self.completed_interactions.append(interaction)
            
            logger.debug(f"Finalized interaction {interaction_id}: success={interaction.success}")
            
        except Exception as e:
            logger.error(f"Error finalizing interaction {interaction_id}: {e}")
    
    def _determine_success(self, interaction: MCPInteraction) -> bool:
        """Determine if an interaction was successful."""
        # Check for error codes in message traces
        for message in interaction.message_traces:
            if message.error_code:
                return False
        
        # Check for successful API responses
        for message in interaction.message_traces:
            if (message.direction == MCPMessageDirection.SERVER_TO_API and
                message.latency_ms is not None and
                not message.error_code):
                return True
        
        # Default to unsuccessful if no clear success indicators
        return False
    
    def _count_retries(self, interaction: MCPInteraction) -> int:
        """Count retry attempts in an interaction."""
        retry_count = 0
        for message in interaction.message_traces:
            if message.retry_attempt and message.retry_attempt > 1:
                retry_count += 1
        return retry_count
    
    async def get_recent_interactions(self) -> List[MCPInteraction]:
        """
        Get recently completed interactions.
        
        Returns:
            List of completed interactions since last call
        """
        recent = self.completed_interactions.copy()
        self.completed_interactions.clear()
        return recent
    
    def get_active_interaction_count(self) -> int:
        """Get count of currently active interactions."""
        return len(self.active_interactions)
    
    def get_total_message_count(self) -> int:
        """Get total count of processed messages."""
        return len(self.message_buffer) 