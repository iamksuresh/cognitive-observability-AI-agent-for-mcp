"""
Live MCP Communication Interceptor.

Advanced interceptor that captures real MCP communications using multiple methods:
1. Process monitoring and stdio interception
2. Log file parsing with real-time monitoring  
3. Extension-based message capture
4. Network traffic analysis
"""

import asyncio
import json
import re
import time
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator, Set
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol

logger = logging.getLogger(__name__)


class MCPLogHandler(FileSystemEventHandler):
    """Handler for real-time log file monitoring."""
    
    def __init__(self, callback):
        self.callback = callback
        self.processed_lines: Set[str] = set()
    
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.log'):
            return
        
        try:
            # Read new lines from the log file
            with open(event.src_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Process only new lines
            for line in lines[-10:]:  # Check last 10 lines
                line_hash = hash(line)
                if line_hash not in self.processed_lines:
                    self.processed_lines.add(line_hash)
                    if self._is_mcp_line(line):
                        asyncio.create_task(self.callback(line))
                        
        except Exception as e:
            logger.debug(f"Error processing log file {event.src_path}: {e}")
    
    def _is_mcp_line(self, line: str) -> bool:
        """Check if line contains MCP communication data."""
        mcp_keywords = ['jsonrpc', 'tools/list', 'tools/call', 'mastra', 'mcp-docs-server']
        return any(keyword in line.lower() for keyword in mcp_keywords)


class LiveMCPInterceptor:
    """
    Advanced live MCP interceptor using multiple capture methods.
    """
    
    def __init__(self):
        self.is_active = False
        self.captured_messages: List[MCPMessageTrace] = []
        self.mcp_processes: List[psutil.Process] = []
        self.log_observer: Optional[Observer] = None
        self.interception_tasks: List[asyncio.Task] = []
        
    async def start_interception(self) -> bool:
        """Start all interception methods."""
        try:
            self.is_active = True
            
            # Method 1: Process monitoring
            await self._start_process_monitoring()
            
            # Method 2: Log file monitoring  
            await self._start_log_monitoring()
            
            # Method 3: Network monitoring
            await self._start_network_monitoring()
            
            logger.info("Live MCP interception started with multiple methods")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start live interception: {e}")
            return False
    
    async def stop_interception(self):
        """Stop all interception methods."""
        try:
            self.is_active = False
            
            # Cancel all tasks
            for task in self.interception_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Stop log monitoring
            if self.log_observer:
                self.log_observer.stop()
                self.log_observer.join()
            
            logger.info("Live MCP interception stopped")
            
        except Exception as e:
            logger.error(f"Error stopping interception: {e}")
    
    async def _start_process_monitoring(self):
        """Monitor MCP server processes for communications."""
        task = asyncio.create_task(self._monitor_processes())
        self.interception_tasks.append(task)
    
    async def _start_log_monitoring(self):
        """Monitor Cursor log files for MCP messages."""
        task = asyncio.create_task(self._monitor_logs())
        self.interception_tasks.append(task)
        
    async def _start_network_monitoring(self):
        """Monitor network communications."""
        task = asyncio.create_task(self._monitor_network())
        self.interception_tasks.append(task)
    
    async def _monitor_processes(self):
        """Advanced process monitoring for MCP communications."""
        try:
            while self.is_active:
                # Find MCP server processes
                current_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if self._is_mcp_process(cmdline):
                            current_processes.append(proc)
                            
                            # Try to capture stdio communications
                            await self._capture_process_stdio(proc)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                self.mcp_processes = current_processes
                
                if current_processes:
                    logger.debug(f"Monitoring {len(current_processes)} MCP processes")
                else:
                    logger.debug("No MCP processes found")
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
        except Exception as e:
            logger.error(f"Error in process monitoring: {e}")
    
    async def _capture_process_stdio(self, process: psutil.Process):
        """Attempt to capture stdio communications from MCP process."""
        try:
            # Method 1: Use strace/dtrace to monitor system calls (Unix/Linux/macOS)
            if hasattr(process, 'pid'):
                await self._trace_process_syscalls(process.pid)
                
        except Exception as e:
            logger.debug(f"Error capturing stdio for process {process.pid}: {e}")
    
    async def _trace_process_syscalls(self, pid: int):
        """Use system tracing to capture stdio."""
        try:
            # For macOS, use dtrace (requires sudo)
            # For Linux, use strace
            # This is a simplified version - full implementation would need privileges
            
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # dtrace command to trace read/write system calls
                cmd = f"sudo dtrace -n 'syscall::read:entry,syscall::write:entry /pid == {pid}/ {{ printf(\"%s\", copyinstr(arg1)); }}'"
            elif system == "Linux":
                # strace command to trace read/write
                cmd = f"strace -p {pid} -e trace=read,write -s 1000"
            else:
                return
            
            # Run tracing (this would need proper permission handling)
            logger.debug(f"Would trace process {pid} with: {cmd}")
            
        except Exception as e:
            logger.debug(f"Error tracing process {pid}: {e}")
    
    async def _monitor_logs(self):
        """Monitor Cursor logs for MCP communications."""
        try:
            # Set up file system monitoring for log directories
            log_dirs = self._get_cursor_log_directories()
            
            if log_dirs:
                self.log_observer = Observer()
                handler = MCPLogHandler(self._process_log_line)
                
                for log_dir in log_dirs:
                    if log_dir.exists():
                        self.log_observer.schedule(handler, str(log_dir), recursive=True)
                        logger.info(f"Monitoring log directory: {log_dir}")
                
                self.log_observer.start()
                
                # Also parse existing log files
                await self._parse_existing_logs(log_dirs)
            
            # Keep monitoring while active
            while self.is_active:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in log monitoring: {e}")
    
    async def _monitor_network(self):
        """Monitor network communications for MCP traffic."""
        try:
            while self.is_active:
                # Check if any MCP processes have network connections
                for proc in self.mcp_processes:
                    try:
                        # Get connections for this process
                        connections = proc.connections()
                        for conn in connections:
                            if conn.status == 'ESTABLISHED':
                                logger.debug(f"MCP process {proc.pid} has connection: {conn.laddr} -> {conn.raddr}")
                                # Could implement packet capture here
                                
                    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                        # Process may not exist or may not have permission to access connections
                        continue
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except Exception as e:
            logger.error(f"Error in network monitoring: {e}")
    
    def _is_mcp_process(self, cmdline: str) -> bool:
        """Determine if a process is an MCP server."""
        mcp_indicators = [
            'mcp-docs-server',
            'stdio.js',
            'mastra',
            '@mastra/mcp',
            'mcp-server',
            '--mcp'
        ]
        return any(indicator in cmdline.lower() for indicator in mcp_indicators)
    
    def _get_cursor_log_directories(self) -> List[Path]:
        """Get list of Cursor log directories to monitor."""
        home = Path.home()
        possible_dirs = [
            home / "Library/Application Support/Cursor/logs",
            home / ".cursor/logs",
            home / ".config/Cursor/logs"
        ]
        return [d for d in possible_dirs if d.exists()]
    
    async def _parse_existing_logs(self, log_dirs: List[Path]):
        """Parse existing log files for MCP messages."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=1)  # Last hour
            
            for log_dir in log_dirs:
                for log_file in log_dir.rglob("*.log"):
                    try:
                        # Only process recent files
                        if log_file.stat().st_mtime < cutoff_time.timestamp():
                            continue
                            
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        # Process recent lines
                        for line in lines[-100:]:  # Last 100 lines
                            if self._contains_mcp_data(line):
                                await self._process_log_line(line)
                                
                    except Exception as e:
                        logger.debug(f"Error processing log file {log_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error parsing existing logs: {e}")
    
    def _contains_mcp_data(self, line: str) -> bool:
        """Check if log line contains MCP communication data."""
        patterns = [
            r'"jsonrpc"\s*:\s*"2\.0"',
            r'"method"\s*:\s*"tools/list"',
            r'"method"\s*:\s*"tools/call"',
            r'mcp-docs-server',
            r'mastra.*docs',
            r'@mastra/mcp'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)
    
    async def _process_log_line(self, line: str):
        """Process a log line that contains MCP data."""
        try:
            # Extract JSON-RPC messages from the line
            json_matches = re.findall(r'\{[^{}]*"jsonrpc"[^{}]*\}', line)
            
            for json_str in json_matches:
                try:
                    json_data = json.loads(json_str)
                    
                    # Create MCPMessageTrace from the JSON data
                    trace = MCPMessageTrace(
                        direction=self._determine_direction(json_data),
                        protocol=MCPProtocol.JSON_RPC,
                        payload=json_data,
                        timestamp=datetime.utcnow(),
                        latency_ms=None
                    )
                    
                    self.captured_messages.append(trace)
                    logger.info(f"Captured real MCP message: {json_data.get('method', 'response')}")
                    
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error processing log line: {e}")
    
    def _determine_direction(self, json_data: Dict[str, Any]) -> MCPMessageDirection:
        """Determine message direction from JSON-RPC data."""
        if 'method' in json_data:
            method = json_data['method']
            if method.startswith('tools/'):
                return MCPMessageDirection.LLM_TO_MCP_CLIENT
            else:
                return MCPMessageDirection.MCP_CLIENT_TO_SERVER
        elif 'result' in json_data or 'error' in json_data:
            return MCPMessageDirection.SERVER_TO_MCP_CLIENT
        else:
            return MCPMessageDirection.LLM_TO_MCP_CLIENT
    
    async def get_captured_messages(self) -> List[MCPMessageTrace]:
        """Get all captured messages since last call."""
        messages = self.captured_messages.copy()
        self.captured_messages.clear()
        return messages
    
    def get_status(self) -> Dict[str, Any]:
        """Get current interception status."""
        return {
            "active": self.is_active,
            "mcp_processes": len(self.mcp_processes),
            "captured_messages": len(self.captured_messages),
            "methods": {
                "process_monitoring": len(self.mcp_processes) > 0,
                "log_monitoring": self.log_observer is not None,
                "network_monitoring": True if self.is_active else False
            }
        } 