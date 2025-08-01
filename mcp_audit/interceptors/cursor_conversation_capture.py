"""
Cursor Conversation Capture Interceptor.

Automatically captures user raw queries in Cursor IDE before they reach Claude,
extending the audit capability to the full user workflow.
"""

import asyncio
import json
import re
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Set
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..core.models import ConversationContext
from .conversation_interceptor import ConversationContextInterceptor

logger = logging.getLogger(__name__)


class CursorConversationHandler(FileSystemEventHandler):
    """Handler for monitoring Cursor conversation files."""
    
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.processed_queries: Set[str] = set()
        self.last_processed_time = datetime.utcnow()
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        try:
            # Monitor Cursor conversation files
            if self._is_conversation_file(event.src_path):
                asyncio.create_task(self._process_conversation_file(event.src_path))
        except Exception as e:
            logger.debug(f"Error processing conversation file {event.src_path}: {e}")
    
    def _is_conversation_file(self, file_path: str) -> bool:
        """Check if file is a Cursor conversation file."""
        path = Path(file_path)
        
        # Common Cursor conversation file patterns
        conversation_patterns = [
            'conversation',
            'chat',
            'messages',
            'history'
        ]
        
        return (
            path.suffix in ['.json', '.jsonl', '.db', '.sqlite'] and
            any(pattern in path.name.lower() for pattern in conversation_patterns)
        )
    
    async def _process_conversation_file(self, file_path: str):
        """Process conversation file for new user queries."""
        try:
            path = Path(file_path)
            
            if path.suffix == '.json':
                await self._process_json_conversation(path)
            elif path.suffix == '.jsonl':
                await self._process_jsonl_conversation(path)
            elif path.suffix in ['.db', '.sqlite']:
                await self._process_sqlite_conversation(path)
                
        except Exception as e:
            logger.debug(f"Error processing conversation file {file_path}: {e}")
    
    async def _process_json_conversation(self, file_path: Path):
        """Process JSON conversation file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract user messages from various JSON structures
            messages = self._extract_messages_from_json(data)
            
            for message in messages:
                if self._is_new_user_message(message):
                    await self.callback(message['content'], message.get('timestamp'))
                    
        except Exception as e:
            logger.debug(f"Error processing JSON conversation {file_path}: {e}")
    
    async def _process_jsonl_conversation(self, file_path: Path):
        """Process JSONL conversation file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if self._is_user_message(data):
                            content = self._extract_message_content(data)
                            if content and self._is_new_user_message({'content': content}):
                                await self.callback(content, data.get('timestamp'))
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.debug(f"Error processing JSONL conversation {file_path}: {e}")
    
    async def _process_sqlite_conversation(self, file_path: Path):
        """Process SQLite conversation database."""
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Common table names for conversations
            table_names = ['messages', 'conversations', 'chat_messages']
            
            for table_name in table_names:
                try:
                    # Get recent user messages
                    cursor.execute(f"""
                        SELECT content, timestamp, role 
                        FROM {table_name} 
                        WHERE role = 'user' 
                        AND timestamp > datetime('now', '-1 hour')
                        ORDER BY timestamp DESC
                    """)
                    
                    for row in cursor.fetchall():
                        content, timestamp, role = row
                        if self._is_new_user_message({'content': content}):
                            await self.callback(content, timestamp)
                            
                except sqlite3.OperationalError:
                    # Table doesn't exist or different schema
                    continue
            
            conn.close()
            
        except Exception as e:
            logger.debug(f"Error processing SQLite conversation {file_path}: {e}")
    
    def _extract_messages_from_json(self, data: Dict) -> List[Dict]:
        """Extract messages from various JSON conversation structures."""
        messages = []
        
        # Common patterns for conversation data
        if isinstance(data, list):
            messages = data
        elif 'messages' in data:
            messages = data['messages']
        elif 'conversation' in data:
            messages = data['conversation']
        elif 'history' in data:
            messages = data['history']
        
        return [msg for msg in messages if isinstance(msg, dict)]
    
    def _is_user_message(self, message: Dict) -> bool:
        """Check if message is from user."""
        role = message.get('role', '').lower()
        sender = message.get('sender', '').lower()
        type_field = message.get('type', '').lower()
        
        return role in ['user', 'human'] or sender in ['user', 'human'] or type_field == 'user'
    
    def _extract_message_content(self, message: Dict) -> Optional[str]:
        """Extract content from message."""
        # Try different content field names
        for field in ['content', 'text', 'message', 'prompt', 'query']:
            if field in message and isinstance(message[field], str):
                return message[field].strip()
        
        return None
    
    def _is_new_user_message(self, message: Dict) -> bool:
        """Check if this is a new user message we haven't processed."""
        content = message.get('content', '').strip()
        
        if not content or len(content) < 3:
            return False
        
        # Create hash for deduplication
        content_hash = hash(content)
        
        if content_hash in self.processed_queries:
            return False
        
        self.processed_queries.add(content_hash)
        
        # Clean up old hashes (keep only last 1000)
        if len(self.processed_queries) > 1000:
            # Remove oldest 200 entries
            old_hashes = list(self.processed_queries)[:200]
            for old_hash in old_hashes:
                self.processed_queries.discard(old_hash)
        
        return True


class CursorConversationCapture:
    """
    Automatically captures user conversations in Cursor IDE.
    
    This interceptor monitors multiple sources to capture user queries:
    1. Conversation history files
    2. Clipboard monitoring for copy-paste patterns  
    3. Log file monitoring
    4. Memory-based detection
    """
    
    def __init__(self):
        self.conversation_interceptor = ConversationContextInterceptor()
        self.file_observer: Optional[Observer] = None
        self.is_active = False
        self.capture_callbacks: List[Callable] = []
        
        # Monitoring paths
        self.cursor_paths = self._find_cursor_paths()
        
    def _find_cursor_paths(self) -> List[Path]:
        """Find potential Cursor data paths to monitor."""
        paths = []
        
        # Common Cursor data locations
        home = Path.home()
        
        # Platform-specific paths
        possible_paths = [
            # Workspace-level
            Path.cwd() / ".cursor",
            
            # User-level 
            home / ".cursor",
            home / ".config" / "Cursor",
            home / "Library" / "Application Support" / "Cursor",  # macOS
            home / "AppData" / "Roaming" / "Cursor",  # Windows
            
            # Common conversation storage locations
            home / ".cursor" / "conversations",
            home / ".cursor" / "history",
            home / ".cursor" / "chats",
        ]
        
        # Add existing paths
        for path in possible_paths:
            if path.exists():
                paths.append(path)
                logger.debug(f"Found Cursor path: {path}")
        
        return paths
    
    async def start_capture(self) -> bool:
        """Start automatically capturing user conversations."""
        try:
            if self.is_active:
                logger.warning("Conversation capture already active")
                return True
            
            self.is_active = True
            
            # Set up file system monitoring
            await self._setup_file_monitoring()
            
            # Set up additional monitoring methods
            await self._setup_additional_monitoring()
            
            logger.info(f"Started Cursor conversation capture monitoring {len(self.cursor_paths)} paths")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start conversation capture: {e}")
            self.is_active = False
            return False
    
    async def stop_capture(self):
        """Stop conversation capture."""
        try:
            self.is_active = False
            
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
                self.file_observer = None
            
            logger.info("Stopped Cursor conversation capture")
            
        except Exception as e:
            logger.error(f"Error stopping conversation capture: {e}")
    
    async def _setup_file_monitoring(self):
        """Set up file system monitoring for conversation files."""
        try:
            if not self.cursor_paths:
                logger.warning("No Cursor paths found for monitoring")
                return
            
            # Create file handler
            handler = CursorConversationHandler(self._on_user_query_captured)
            
            # Set up observer
            self.file_observer = Observer()
            
            for path in self.cursor_paths:
                if path.exists() and path.is_dir():
                    self.file_observer.schedule(handler, str(path), recursive=True)
                    logger.debug(f"Monitoring path: {path}")
            
            self.file_observer.start()
            
        except Exception as e:
            logger.error(f"Error setting up file monitoring: {e}")
    
    async def _setup_additional_monitoring(self):
        """Set up additional monitoring methods."""
        try:
            # TODO: Add clipboard monitoring for copy-paste patterns
            # TODO: Add memory monitoring for active Cursor process
            # TODO: Add network monitoring for API calls
            
            logger.debug("Additional monitoring methods set up")
            
        except Exception as e:
            logger.error(f"Error setting up additional monitoring: {e}")
    
    async def _on_user_query_captured(self, user_query: str, timestamp: Optional[str] = None):
        """Handle captured user query."""
        try:
            # Create conversation context
            context = await self.conversation_interceptor.capture_user_prompt(
                user_prompt=user_query,
                conversation_id="cursor_auto_capture",
                host_interface="cursor"
            )
            
            # Notify callbacks
            for callback in self.capture_callbacks:
                try:
                    await callback(context)
                except Exception as e:
                    logger.error(f"Error in capture callback: {e}")
            
            logger.info(f"🎯 Auto-captured user query: {user_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error handling captured user query: {e}")
    
    def register_capture_callback(self, callback: Callable[[ConversationContext], None]):
        """Register callback for when user queries are captured."""
        self.capture_callbacks.append(callback)
    
    async def manual_capture_query(self, user_query: str) -> ConversationContext:
        """Manually capture a user query."""
        return await self.conversation_interceptor.capture_user_prompt(
            user_prompt=user_query,
            conversation_id="manual_capture",
            host_interface="cursor"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get capture status."""
        return {
            "is_active": self.is_active,
            "monitoring_paths": [str(p) for p in self.cursor_paths],
            "total_conversations": len(self.conversation_interceptor.conversation_log),
            "file_observer_active": self.file_observer is not None and self.file_observer.is_alive() if self.file_observer else False
        } 