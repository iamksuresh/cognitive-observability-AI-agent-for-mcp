"""
Enhanced Cursor Adapter with Automatic User Query Capture.

Extends the basic Cursor adapter to automatically intercept user raw queries
before they reach Claude, providing complete workflow visibility.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime, timedelta

from .cursor import CursorAdapter
from ..core.models import MCPMessageTrace, ConversationContext, MCPInteraction
from ..interceptors.cursor_conversation_capture import CursorConversationCapture
from ..interceptors.conversation_interceptor import ConversationContextInterceptor

logger = logging.getLogger(__name__)


class EnhancedCursorAdapter(CursorAdapter):
    """
    Enhanced Cursor adapter with automatic user query interception.
    
    This adapter provides the complete workflow visibility:
    USER QUERY → CONVERSATION CAPTURE → CLAUDE → MCP AUDIT → MCP SERVER
                       ↑ Automatic capture      ↑ Existing capture
    """
    
    def __init__(self):
        """Initialize enhanced Cursor adapter."""
        super().__init__()
        
        # User query capture
        self.conversation_capture = CursorConversationCapture()
        self.conversation_interceptor = ConversationContextInterceptor()
        
        # Correlation tracking
        self.pending_conversations: List[ConversationContext] = []
        self.conversation_mcp_correlations: Dict[str, str] = {}
        
    async def initialize(self) -> None:
        """Initialize the enhanced adapter with user query capture."""
        try:
            # Initialize base adapter
            await super().initialize()
            
            # Set up conversation capture
            await self._setup_conversation_capture()
            
            # Set up correlation handling
            self._setup_correlation_callbacks()
            
            logger.info("Enhanced Cursor adapter initialized with automatic user query capture")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced Cursor adapter: {e}")
            raise
    
    async def _setup_conversation_capture(self):
        """Set up automatic conversation capture."""
        try:
            # Register callback for captured user queries
            self.conversation_capture.register_capture_callback(self._on_user_query_captured)
            
            # Start automatic capture
            success = await self.conversation_capture.start_capture()
            if success:
                logger.info("🎯 Automatic user query capture started")
            else:
                logger.warning("⚠️ Failed to start automatic capture, manual capture still available")
                
        except Exception as e:
            logger.error(f"Error setting up conversation capture: {e}")
    
    def _setup_correlation_callbacks(self):
        """Set up callbacks to correlate conversations with MCP interactions."""
        # Register callback for MCP correlation
        self.conversation_interceptor.register_mcp_correlation_callback(
            self._on_mcp_correlation_ready
        )
    
    async def _on_user_query_captured(self, context: ConversationContext):
        """Handle captured user query and prepare for MCP correlation."""
        try:
            # Add to pending conversations for correlation
            self.pending_conversations.append(context)
            
            # Keep only recent conversations (last 10 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            self.pending_conversations = [
                conv for conv in self.pending_conversations
                if conv.message_timestamp >= cutoff_time
            ]
            
            logger.info(f"📝 User query captured and ready for correlation: {context.user_prompt[:50]}...")
            
        except Exception as e:
            logger.error(f"Error handling captured user query: {e}")
    
    def _on_mcp_correlation_ready(self, context: ConversationContext):
        """Callback for when conversation is ready for MCP correlation."""
        logger.debug(f"Conversation context ready for MCP correlation: {context.conversation_id}")
    
    async def stream_mcp_messages(self) -> AsyncGenerator[MCPMessageTrace, None]:
        """
        Stream MCP messages with automatic user query correlation.
        
        This enhanced version automatically correlates MCP messages with
        recently captured user queries.
        """
        logger.info("Starting enhanced MCP message streaming with user query correlation...")
        
        async for message in super().stream_mcp_messages():
            # Enhance message with conversation context if available
            enhanced_message = await self._enhance_message_with_context(message)
            yield enhanced_message
    
    async def _enhance_message_with_context(self, message: MCPMessageTrace) -> MCPMessageTrace:
        """Enhance MCP message with conversation context."""
        try:
            # Find matching conversation context
            matching_context = self._find_matching_conversation_context(message)
            
            if matching_context:
                # Add conversation context to message metadata
                if not hasattr(message, 'metadata'):
                    message.metadata = {}
                
                message.metadata.update({
                    'user_query': matching_context.user_prompt,
                    'user_intent': matching_context.user_intent,
                    'conversation_id': matching_context.conversation_id,
                    'complexity_level': matching_context.complexity_level,
                    'conversation_timestamp': matching_context.message_timestamp.isoformat()
                })
                
                logger.debug(f"🔗 Enhanced MCP message with user context: {matching_context.user_prompt[:30]}...")
            
            return message
            
        except Exception as e:
            logger.error(f"Error enhancing message with context: {e}")
            return message
    
    def _find_matching_conversation_context(self, message: MCPMessageTrace) -> Optional[ConversationContext]:
        """Find conversation context that matches the MCP message timing."""
        try:
            # Look for conversations within the last 30 seconds
            message_time = message.timestamp
            time_window = timedelta(seconds=30)
            
            # Find the most recent conversation before this message
            matching_conversations = [
                conv for conv in self.pending_conversations
                if (message_time - conv.message_timestamp) <= time_window
                and conv.message_timestamp <= message_time
            ]
            
            if matching_conversations:
                # Return the most recent matching conversation
                return max(matching_conversations, key=lambda c: c.message_timestamp)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding matching conversation context: {e}")
            return None
    
    async def generate_enhanced_interaction_report(self) -> Dict[str, Any]:
        """Generate a report showing the complete user workflow."""
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "adapter_type": "enhanced_cursor",
                "capture_status": self.conversation_capture.get_status(),
                "workflow_summary": await self._generate_workflow_summary(),
                "conversation_insights": await self._generate_conversation_insights(),
                "correlation_statistics": self._generate_correlation_stats()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating enhanced interaction report: {e}")
            return {"error": str(e)}
    
    async def _generate_workflow_summary(self) -> Dict[str, Any]:
        """Generate summary of the complete workflow."""
        try:
            # Get recent conversations
            recent_conversations = [
                conv for conv in self.pending_conversations
                if conv.message_timestamp >= datetime.utcnow() - timedelta(hours=1)
            ]
            
            # Analyze user intents
            intent_counts = {}
            complexity_counts = {}
            
            for conv in recent_conversations:
                intent = conv.user_intent or 'unknown'
                complexity = conv.complexity_level or 'unknown'
                
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
                complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            return {
                "total_conversations": len(recent_conversations),
                "user_intent_distribution": intent_counts,
                "complexity_distribution": complexity_counts,
                "average_query_length": sum(len(conv.user_prompt) for conv in recent_conversations) / max(len(recent_conversations), 1),
                "capture_methods_active": self.conversation_capture.get_status()["is_active"]
            }
            
        except Exception as e:
            logger.error(f"Error generating workflow summary: {e}")
            return {"error": str(e)}
    
    async def _generate_conversation_insights(self) -> Dict[str, Any]:
        """Generate insights about user conversations."""
        try:
            recent_conversations = [
                conv for conv in self.pending_conversations
                if conv.message_timestamp >= datetime.utcnow() - timedelta(hours=1)
            ]
            
            if not recent_conversations:
                return {"message": "No recent conversations to analyze"}
            
            # Analyze query patterns
            query_patterns = []
            for conv in recent_conversations:
                query = conv.user_prompt.lower()
                
                if any(word in query for word in ['what', 'how', 'why', 'explain']):
                    query_patterns.append('question')
                elif any(word in query for word in ['create', 'make', 'generate']):
                    query_patterns.append('creation')
                elif any(word in query for word in ['fix', 'debug', 'error']):
                    query_patterns.append('troubleshooting')
                else:
                    query_patterns.append('other')
            
            pattern_counts = {}
            for pattern in query_patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            return {
                "query_patterns": pattern_counts,
                "most_common_pattern": max(pattern_counts, key=pattern_counts.get) if pattern_counts else None,
                "conversation_frequency": len(recent_conversations),
                "average_time_between_queries": self._calculate_average_query_interval(recent_conversations)
            }
            
        except Exception as e:
            logger.error(f"Error generating conversation insights: {e}")
            return {"error": str(e)}
    
    def _calculate_average_query_interval(self, conversations: List[ConversationContext]) -> Optional[float]:
        """Calculate average time between queries in seconds."""
        try:
            if len(conversations) < 2:
                return None
            
            # Sort by timestamp
            sorted_conversations = sorted(conversations, key=lambda c: c.message_timestamp)
            
            intervals = []
            for i in range(1, len(sorted_conversations)):
                interval = (sorted_conversations[i].message_timestamp - sorted_conversations[i-1].message_timestamp).total_seconds()
                intervals.append(interval)
            
            return sum(intervals) / len(intervals) if intervals else None
            
        except Exception as e:
            logger.error(f"Error calculating query intervals: {e}")
            return None
    
    def _generate_correlation_stats(self) -> Dict[str, Any]:
        """Generate statistics about conversation-MCP correlations."""
        return {
            "pending_conversations": len(self.pending_conversations),
            "total_correlations": len(self.conversation_mcp_correlations),
            "correlation_success_rate": self._calculate_correlation_success_rate()
        }
    
    def _calculate_correlation_success_rate(self) -> float:
        """Calculate how often we successfully correlate conversations with MCP calls."""
        try:
            total_conversations = len(self.conversation_interceptor.conversation_log)
            if total_conversations == 0:
                return 0.0
            
            correlated_conversations = len(self.conversation_mcp_correlations)
            return (correlated_conversations / total_conversations) * 100
            
        except Exception as e:
            logger.error(f"Error calculating correlation success rate: {e}")
            return 0.0
    
    async def manual_capture_user_query(self, user_query: str) -> ConversationContext:
        """
        Manually capture a user query.
        
        Useful for testing or when automatic capture isn't working.
        """
        try:
            context = await self.conversation_capture.manual_capture_query(user_query)
            await self._on_user_query_captured(context)
            return context
            
        except Exception as e:
            logger.error(f"Error manually capturing user query: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up enhanced adapter resources."""
        try:
            # Stop conversation capture
            if self.conversation_capture.is_active:
                await self.conversation_capture.stop_capture()
            
            # Clean up base adapter
            await super().cleanup()
            
            logger.info("Enhanced Cursor adapter cleaned up")
            
        except Exception as e:
            logger.error(f"Error during enhanced adapter cleanup: {e}")
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive status of enhanced adapter."""
        base_status = super().get_live_interception_status()
        
        enhanced_status = {
            "base_adapter": base_status,
            "conversation_capture": self.conversation_capture.get_status(),
            "pending_conversations": len(self.pending_conversations),
            "correlation_stats": self._generate_correlation_stats(),
            "enhancement_active": self.conversation_capture.is_active
        }
        
        return enhanced_status 