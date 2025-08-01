"""
MCP Proxy Interceptor - Captures real-time MCP communications.

This proxy sits between the MCP host (Cursor) and MCP servers, 
intercepting and logging all JSON-RPC messages while forwarding them transparently.
"""

import asyncio
import json
import shutil
import subprocess
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator

from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol

logger = logging.getLogger(__name__)


class MCPProxy:
    """
    Transparent proxy for MCP communications.
    
    Acts as a man-in-the-middle between MCP host and server,
    capturing all JSON-RPC messages for audit analysis.
    """
    
    def __init__(self, target_server_cmd: List[str], audit_callback=None):
        self.target_server_cmd = target_server_cmd
        self.audit_callback = audit_callback
        self.server_process: Optional[subprocess.Popen] = None
        self.captured_messages: List[MCPMessageTrace] = []
        self.message_counter = 0
        
    async def start_proxy_server(self, working_directory: Optional[str] = None):
        """Start the MCP server subprocess and begin proxying."""
        try:
            # Start the actual MCP server as subprocess
            # Use the specified working directory or current directory
            cwd = working_directory or str(Path.cwd())
            
            self.server_process = subprocess.Popen(
                self.target_server_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # Unbuffered for real-time
                cwd=cwd  # Set working directory for target command
            )
            
            logger.info(f"Started MCP server proxy: {' '.join(self.target_server_cmd)} (cwd: {cwd})")
            
            # Wait a moment and check if process started successfully
            await asyncio.sleep(0.1)
            if self.server_process.poll() is not None:
                # Process exited immediately - likely an error
                stderr_output = self.server_process.stderr.read() if self.server_process.stderr else "No error output"
                logger.error(f"MCP server process exited immediately with code {self.server_process.returncode}")
                logger.error(f"Stderr: {stderr_output}")
                raise RuntimeError(f"Target MCP server failed to start: {stderr_output}")
            
            # Start bidirectional message forwarding
            await asyncio.gather(
                self._forward_stdin_to_server(),
                self._forward_server_to_stdout(),
                self._monitor_stderr()
            )
            
        except Exception as e:
            logger.error(f"Error in MCP proxy: {e}")
            await self.cleanup()
    
    async def _forward_stdin_to_server(self):
        """Forward messages from host (Cursor) to MCP server."""
        try:
            while True:
                # Read from stdin (from Cursor)
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                # Parse and capture the message
                await self._capture_message(line.strip(), MCPMessageDirection.LLM_TO_MCP_CLIENT)
                
                # Forward to actual MCP server
                if self.server_process and self.server_process.stdin:
                    self.server_process.stdin.write(line)
                    self.server_process.stdin.flush()
                    
        except Exception as e:
            logger.error(f"Error forwarding stdin: {e}")
    
    async def _forward_server_to_stdout(self):
        """Forward messages from MCP server to host (Cursor)."""
        try:
            while True:
                if not self.server_process or not self.server_process.stdout:
                    break
                
                # Read from MCP server
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.server_process.stdout.readline
                )
                
                if not line:
                    break
                
                # Parse and capture the message
                await self._capture_message(line.strip(), MCPMessageDirection.MCP_CLIENT_TO_SERVER)
                
                # Forward to Cursor
                sys.stdout.write(line)
                sys.stdout.flush()
                
        except Exception as e:
            logger.error(f"Error forwarding stdout: {e}")
    
    async def _monitor_stderr(self):
        """Monitor MCP server stderr for errors."""
        try:
            while True:
                if not self.server_process or not self.server_process.stderr:
                    break
                
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.server_process.stderr.readline
                )
                
                if not line:
                    break
                
                # Log server errors with higher severity for debugging
                stderr_msg = line.strip()
                if stderr_msg:
                    if "error" in stderr_msg.lower() or "failed" in stderr_msg.lower():
                        logger.error(f"MCP Server Error: {stderr_msg}")
                    else:
                        logger.warning(f"MCP Server stderr: {stderr_msg}")
                
        except Exception as e:
            logger.error(f"Error monitoring stderr: {e}")
    
    async def _capture_message(self, message: str, direction: MCPMessageDirection):
        """Capture and analyze an MCP message."""
        try:
            if not message.strip():
                return
            
            # Parse JSON-RPC message
            json_data = json.loads(message)
            
            # Create trace record
            trace = MCPMessageTrace(
                direction=direction,
                protocol=MCPProtocol.JSON_RPC,
                payload=json_data,
                timestamp=datetime.utcnow(),
                latency_ms=None
            )
            
            self.captured_messages.append(trace)
            self.message_counter += 1
            
            # Call audit callback if provided
            if self.audit_callback:
                await self.audit_callback(trace)
            
            logger.info(f"📡 Captured {direction.value}: {json_data.get('method', 'response')}")
            
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON message: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error capturing message: {e}")
    
    async def cleanup(self):
        """Clean up proxy resources."""
        if self.server_process:
            self.server_process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.server_process.wait
                    ), 
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.server_process.kill()
    
    def get_captured_messages(self) -> List[MCPMessageTrace]:
        """Get all captured messages."""
        return self.captured_messages.copy()


class MCPProxyManager:
    """
    Manages MCP proxy setup and configuration.
    
    Handles replacing MCP server commands with proxy commands
    and restoring original configuration.
    """
    
    def __init__(self):
        self.original_config: Optional[Dict] = None
        self.proxy_process: Optional[asyncio.subprocess.Process] = None
        self.captured_messages: List[MCPMessageTrace] = []
    
    async def setup_proxy_for_server(self, server_name: str = "mastra") -> bool:
        """Set up proxy for a specific MCP server."""
        try:
            # Prioritize project-level configuration first, then global
            config_path = Path(".cursor/mcp.json")
            if not config_path.exists():
                config_path = Path.home() / ".cursor" / "mcp.json"
            
            if not config_path.exists():
                logger.error("MCP configuration file not found")
                return False
            
            logger.info(f"📁 Using config file: {config_path}")
            
            # Backup original configuration
            with open(config_path, 'r') as f:
                self.original_config = json.load(f)
            
            # Create proxy configuration
            proxy_config = self._create_proxy_config(server_name)
            
            # Write proxy configuration
            with open(config_path, 'w') as f:
                json.dump(proxy_config, f, indent=2)
            
            logger.info(f"✅ Set up MCP proxy for server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup MCP proxy: {e}")
            return False
    
    def _create_proxy_config(self, server_name: str) -> Dict:
        """Create proxy configuration that replaces original server command."""
        if not self.original_config:
            raise ValueError("No original configuration loaded")
        
        proxy_config = self.original_config.copy()
        
        if "mcpServers" in proxy_config and server_name in proxy_config["mcpServers"]:
            original_server = proxy_config["mcpServers"][server_name]
            
            # Check if proxy is already applied to prevent recursion
            if self._is_already_proxied(original_server):
                logger.info(f"⚠️ Proxy already applied for {server_name}, skipping...")
                return proxy_config
            
            # Replace with proxy command (flattened args approach)
            original_args = original_server.get("args", [])
            proxy_args = [
                "-m", "mcp_audit.interceptors.mcp_proxy_runner",
                "--target-command", original_server.get("command", ""),
                "--target-args"
            ] + original_args
            
            # Use virtual environment Python if available, fallback to system python
            venv_python = Path.cwd() / ".venv" / "bin" / "python"
            if venv_python.exists():
                python_cmd = str(venv_python)
            else:
                # Try python3 first (common on macOS), fallback to python
                if shutil.which("python3"):
                    python_cmd = "python3"
                elif shutil.which("python"):
                    python_cmd = "python"
                else:
                    python_cmd = "python3"  # Default fallback
            
            # Preserve original working directory for the target command
            original_cwd = original_server.get("cwd", str(Path.cwd()))
            
            proxy_config["mcpServers"][server_name] = {
                "command": python_cmd,
                "args": proxy_args,
                "cwd": original_cwd,  # Use original working directory, not current
                "env": {
                    "MCP_TARGET_CWD": original_cwd,  # Pass target working directory to proxy
                    "MCP_SERVER_NAME": server_name  # Pass server name to proxy for metrics
                }
            }
            
            logger.info(f"✅ Applied fresh proxy configuration for {server_name}")
        
        return proxy_config
    
    def _is_already_proxied(self, server_config: Dict) -> bool:
        """Check if server configuration is already using the proxy."""
        args = server_config.get("args", [])
        command = server_config.get("command", "")
        
        # Check if proxy is already in the configuration
        # Handle both "python" and venv python paths
        is_python_command = (
            command == "python" or 
            command.endswith("/bin/python") or
            command.endswith("/bin/python3")
        )
        
        return (
            is_python_command and 
            len(args) > 0 and 
            args[0] == "-m" and 
            len(args) > 1 and 
            args[1] == "mcp_audit.interceptors.mcp_proxy_runner"
        )
    
    async def restore_original_config(self):
        """Restore original MCP configuration."""
        try:
            if not self.original_config:
                return
            
            config_path = Path.home() / ".cursor" / "mcp.json"
            if not config_path.exists():
                config_path = Path(".cursor/mcp.json")
            
            with open(config_path, 'w') as f:
                json.dump(self.original_config, f, indent=2)
            
            logger.info("✅ Restored original MCP configuration")
            
        except Exception as e:
            logger.error(f"Failed to restore MCP config: {e}")
    
    async def start_message_capture(self, audit_callback=None):
        """Start capturing messages from the proxy."""
        # This would be called by the proxy runner
        pass


async def run_proxy(target_command: str, target_args: List[str]):
    """Main proxy runner function."""
    proxy = MCPProxy([target_command] + target_args)
    
    try:
        await proxy.start_proxy_server()
    except KeyboardInterrupt:
        logger.info("Proxy interrupted by user")
    finally:
        await proxy.cleanup()
    
    return proxy.get_captured_messages() 