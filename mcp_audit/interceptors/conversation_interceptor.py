"""
Conversation Context Interceptor.

Captures user conversation context alongside MCP protocol interactions
to provide complete usability audit with actual user prompts.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from ..core.models import ConversationContext, MCPInteraction

logger = logging.getLogger(__name__)


class ConversationContextInterceptor:
    """
    Captures user conversation context to correlate with MCP interactions.
    
    This interceptor works at the conversation level (above MCP protocol)
    to capture actual user prompts that trigger tool calls.
    """
    
    def __init__(self):
        """Initialize the conversation interceptor."""
        self.conversation_log: List[ConversationContext] = []
        self.active_conversations: Dict[str, List[str]] = {}
        self.mcp_correlation_callbacks: List[Callable] = []
        
        # Storage
        self.log_file = Path.home() / ".cursor" / "mcp_conversation_context.jsonl"
        
    def register_mcp_correlation_callback(self, callback: Callable[[ConversationContext], None]):
        """Register a callback to correlate conversation with MCP interactions."""
        self.mcp_correlation_callbacks.append(callback)
    
    async def capture_user_prompt(
        self,
        user_prompt: str,
        conversation_id: Optional[str] = None,
        tools_available: Optional[List[str]] = None,
        host_interface: str = "cursor"
    ) -> ConversationContext:
        """
        Capture a user prompt and create conversation context.
        
        Args:
            user_prompt: The actual user message
            conversation_id: Optional conversation identifier
            tools_available: List of tools available to the LLM
            host_interface: The interface used (cursor, cli, etc.)
            
        Returns:
            ConversationContext object
        """
        try:
            # Get conversation history
            conversation_id = conversation_id or "default"
            preceding_messages = self.active_conversations.get(conversation_id, [])
            
            # Analyze user intent (simple heuristics for now)
            user_intent = self._analyze_user_intent(user_prompt)
            complexity_level = self._assess_complexity(user_prompt)
            
            # Create conversation context
            context = ConversationContext(
                user_prompt=user_prompt,
                conversation_id=conversation_id,
                message_timestamp=datetime.utcnow(),
                preceding_messages=preceding_messages.copy(),
                user_intent=user_intent,
                complexity_level=complexity_level,
                tools_available=tools_available or [],
                host_interface=host_interface
            )
            
            # Update conversation history
            self.active_conversations.setdefault(conversation_id, []).append(user_prompt)
            
            # Keep only last 10 messages per conversation
            if len(self.active_conversations[conversation_id]) > 10:
                self.active_conversations[conversation_id] = self.active_conversations[conversation_id][-10:]
            
            # Store context
            self.conversation_log.append(context)
            await self._persist_context(context)
            
            # Notify MCP correlation callbacks
            for callback in self.mcp_correlation_callbacks:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Error in MCP correlation callback: {e}")
            
            logger.info(f"Captured user prompt: {user_prompt[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error capturing user prompt: {e}")
            # Return minimal context on error
            return ConversationContext(user_prompt=user_prompt, host_interface=host_interface)
    
    async def correlate_with_mcp_interaction(
        self, 
        interaction: MCPInteraction,
        time_window_seconds: int = 10
    ) -> bool:
        """
        Correlate an MCP interaction with recent conversation context.
        
        Args:
            interaction: The MCP interaction to enhance
            time_window_seconds: Time window to search for matching conversation
            
        Returns:
            True if correlation was successful
        """
        try:
            # Find the most recent conversation context within time window
            cutoff_time = interaction.start_time.replace(tzinfo=None) - timedelta(seconds=time_window_seconds)
            
            matching_contexts = [
                ctx for ctx in reversed(self.conversation_log)
                if ctx.message_timestamp.replace(tzinfo=None) >= cutoff_time
            ]
            
            if matching_contexts:
                # Use the most recent context
                context = matching_contexts[0]
                interaction.conversation_context = context
                
                # Update the legacy user_query field with actual prompt
                interaction.user_query = f"User: {context.user_prompt}"
                
                logger.info(f"Correlated MCP interaction with user prompt: {context.user_prompt[:50]}...")
                return True
            
            logger.debug(f"No conversation context found for interaction {interaction.session_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error correlating conversation with MCP interaction: {e}")
            return False
    
    def _analyze_user_intent(self, prompt: str) -> str:
        """Analyze user intent from the prompt using simple heuristics."""
        prompt_lower = prompt.lower()
        
        # Intent patterns
        if any(word in prompt_lower for word in ['create', 'generate', 'make', 'build']):
            return "creation"
        elif any(word in prompt_lower for word in ['fix', 'debug', 'error', 'problem', 'issue']):
            return "troubleshooting"
        elif any(word in prompt_lower for word in ['explain', 'how', 'what', 'why', 'help']):
            return "information_seeking"
        elif any(word in prompt_lower for word in ['change', 'modify', 'update', 'edit']):
            return "modification"
        elif any(word in prompt_lower for word in ['test', 'run', 'execute', 'start']):
            return "execution"
        else:
            return "general"
    
    def _assess_complexity(self, prompt: str) -> str:
        """Assess the complexity level of the user prompt."""
        # Simple heuristics based on length and content
        word_count = len(prompt.split())
        
        if word_count <= 5:
            return "simple"
        elif word_count <= 20:
            return "moderate"
        else:
            return "complex"
    
    async def _persist_context(self, context: ConversationContext):
        """Persist conversation context to disk."""
        try:
            # Ensure directory exists
            self.log_file.parent.mkdir(exist_ok=True)
            
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "timestamp": context.message_timestamp.isoformat(),
                    "conversation_id": context.conversation_id,
                    "user_prompt": context.user_prompt,
                    "user_intent": context.user_intent,
                    "complexity_level": context.complexity_level,
                    "tools_available": context.tools_available,
                    "host_interface": context.host_interface
                }) + '\n')
                
        except Exception as e:
            logger.error(f"Error persisting conversation context: {e}")
    
    def load_recent_contexts(self, hours: int = 24) -> List[ConversationContext]:
        """Load recent conversation contexts from disk."""
        try:
            if not self.log_file.exists():
                return []
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            contexts = []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', ''))
                        
                        if timestamp >= cutoff_time:
                            context = ConversationContext(
                                user_prompt=data['user_prompt'],
                                conversation_id=data['conversation_id'],
                                message_timestamp=timestamp,
                                user_intent=data.get('user_intent'),
                                complexity_level=data.get('complexity_level'),
                                tools_available=data.get('tools_available', []),
                                host_interface=data.get('host_interface', 'cursor')
                            )
                            contexts.append(context)
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Skipping invalid context line: {e}")
                        continue
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error loading conversation contexts: {e}")
            return [] 