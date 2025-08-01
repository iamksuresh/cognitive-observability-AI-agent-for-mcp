"""
User prompt capture for timeline correlation.
This module provides mechanisms to capture user prompts and write them to the audit file.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserPromptCapture:
    """Captures user prompts and writes them to the audit file for timeline correlation."""
    
    def __init__(self):
        self.messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
    
    async def capture_user_prompt(self, prompt: str, server_context: Optional[str] = None, conversation_id: Optional[str] = None):
        """
        Capture a user prompt and write it to the audit file.
        
        Args:
            prompt: The user's prompt/query
            server_context: Which server this prompt might be related to
            conversation_id: Optional conversation identifier
        """
        try:
            # Ensure directory exists
            self.messages_file.parent.mkdir(exist_ok=True)
            
            # Create user prompt message in same format as MCP messages
            message_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "server_name": server_context or "user_prompt",
                "server_process_id": None,
                "direction": "user→llm",
                "protocol": "CURSOR_CHAT",
                "payload": {
                    "content": prompt,
                    "conversation_id": conversation_id or "default",
                    "type": "user_prompt",
                    "method": "user_input"
                },
                "latency_ms": None,
                "error_code": None,
                "enhanced_context": {
                    "llm_initiated": False,
                    "tool_method": None,
                    "tool_name": None,
                    "user_initiated": True,
                    "prompt_length": len(prompt),
                    "prompt_complexity": self._assess_complexity(prompt)
                }
            }
            
            # Append to messages file
            with open(self.messages_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(message_data) + '\n')
            
            logger.info(f"📝 User prompt captured: {prompt[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error capturing user prompt: {e}")
            return False
    
    def _assess_complexity(self, prompt: str) -> str:
        """Simple heuristic to assess prompt complexity."""
        word_count = len(prompt.split())
        
        if word_count > 20:
            return "complex"
        elif word_count > 8:
            return "moderate"
        else:
            return "simple" 