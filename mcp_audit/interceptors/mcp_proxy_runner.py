#!/usr/bin/env python3
"""
Enhanced MCP Proxy Runner with LLM Decision Tracking.

Runs the enhanced MCP proxy that captures not only MCP protocol messages
but also LLM decision-making processes for complete observability.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Enhanced proxy import
from .enhanced_mcp_proxy import EnhancedMCPProxy
from .conversation_interceptor import ConversationContextInterceptor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / ".cursor" / "enhanced_mcp_audit_proxy.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def enhanced_audit_message_callback(trace, server_name=None, server_process_id=None):
    """Enhanced callback to persist captured MCP messages with LLM decision context and server identification."""
    try:
        messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
        
        # Ensure directory exists
        messages_file.parent.mkdir(exist_ok=True)
        
        # Get server identification
        if not server_name:
            server_name = os.environ.get('MCP_SERVER_NAME', 'unknown')
        if not server_process_id:
            server_process_id = os.getpid()
        
        # Append message to JSONL file with enhanced context and server identification
        with open(messages_file, 'a', encoding='utf-8') as f:
            message_data = {
                "timestamp": trace.timestamp.isoformat(),
                "server_name": server_name,                    # ✅ Add server identification
                "server_process_id": server_process_id,        # ✅ Add process identification  
                "direction": trace.direction.value,
                "protocol": trace.protocol.value,
                "payload": trace.payload,
                "latency_ms": getattr(trace, 'latency_ms', None),
                "error_code": getattr(trace, 'error_code', None),
                "enhanced_context": {
                    "llm_initiated": trace.direction.value == "llm_to_mcp_client",
                    "tool_method": trace.payload.get('method'),
                    "tool_name": trace.payload.get('params', {}).get('name') if trace.payload.get('method') == 'tools/call' else None
                }
            }
            f.write(json.dumps(message_data) + '\n')
            
        logger.info(f"📡 Enhanced audit [{server_name}]: {trace.direction.value} - {trace.payload.get('method', 'response')}")
        
    except Exception as e:
        logger.error(f"Error in enhanced audit callback: {e}")


async def write_user_prompt_to_audit(user_prompt, server_name=None, conversation_id=None):
    """Write user prompt to the same audit file for timeline correlation."""
    try:
        messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
        
        # Ensure directory exists
        messages_file.parent.mkdir(exist_ok=True)
        
        # Get server identification (for multi-server context)
        if not server_name:
            server_name = os.environ.get('MCP_SERVER_NAME', 'user_prompt')
        
        # Create user prompt message
        with open(messages_file, 'a', encoding='utf-8') as f:
            message_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "server_name": server_name,
                "server_process_id": os.getpid(),
                "direction": "user→llm",                       # ✅ New direction type
                "protocol": "CURSOR_CHAT",
                "payload": {
                    "content": user_prompt,
                    "conversation_id": conversation_id or "default",
                    "type": "user_prompt"
                },
                "latency_ms": None,
                "error_code": None,
                "enhanced_context": {
                    "llm_initiated": False,
                    "tool_method": None,
                    "tool_name": None,
                    "user_initiated": True                     # ✅ Mark as user-initiated
                }
            }
            f.write(json.dumps(message_data) + '\n')
            
        logger.info(f"📝 User prompt captured [{server_name}]: {user_prompt[:50]}...")
        
    except Exception as e:
        logger.error(f"Error writing user prompt to audit: {e}")


async def start_enhanced_conversation_capture():
    """Start enhanced conversation context capture."""
    try:
        conversation_interceptor = ConversationContextInterceptor()
        
        # User prompt capture integration (future enhancement)
        # For now, we'll capture inferred prompts from MCP interactions
        logger.info("🎤 Enhanced conversation capture started")
        
        return conversation_interceptor
        
    except Exception as e:
        logger.error(f"Error starting conversation capture: {e}")
        return None


async def main():
    """Main entry point for the enhanced MCP proxy runner."""
    try:
        # Parse command line arguments
        if len(sys.argv) < 3:
            logger.error("Usage: python -m mcp_audit.interceptors.mcp_proxy_runner --target-command <command> --target-args <args>")
            return

        target_cmd_index = sys.argv.index('--target-command') + 1 if '--target-command' in sys.argv else 2
        target_args_index = sys.argv.index('--target-args') + 1 if '--target-args' in sys.argv else len(sys.argv)
        
        target_command = sys.argv[target_cmd_index]
        target_args = sys.argv[target_args_index:] if target_args_index < len(sys.argv) else []
        
        target_server_cmd = [target_command] + target_args
        
        # Extract server name from environment or infer from command
        server_name = os.environ.get('MCP_SERVER_NAME')
        if not server_name:
            # Try to infer server name from command
            if 'browser' in ' '.join(target_server_cmd):
                server_name = 'browser'
            elif 'mastra' in ' '.join(target_server_cmd):
                server_name = 'mastra'
            else:
                server_name = 'unknown'
        
        logger.info(f"🚀 Starting Enhanced MCP Proxy for [{server_name}]: {' '.join(target_server_cmd)}")
        
        # Initialize IntegrationManager for persistent metrics export
        from ..integrations.manager import IntegrationManager
        integration_manager = IntegrationManager()
        if 'opentelemetry' in integration_manager.integrations:
            logger.info("📊 OpenTelemetry metrics server started with proxy")
        
        # Create server-specific callback
        async def server_audit_callback(trace):
            await enhanced_audit_message_callback(trace, server_name=server_name)
            
            # Send to integrations in real-time
            try:
                if hasattr(trace, 'to_dict'):
                    # Send trace data to all configured integrations
                    await integration_manager.send_trace_data([trace.to_dict()])
            except Exception as e:
                logger.warning(f"Failed to send trace to integrations: {e}")
        
        # Start enhanced conversation capture
        conversation_interceptor = await start_enhanced_conversation_capture()
        
        # Create and start enhanced proxy
        enhanced_proxy = EnhancedMCPProxy(
            target_server_cmd=target_server_cmd,
            audit_callback=server_audit_callback  # ✅ Use server-specific callback
        )
        
        # Parse working directory from environment or use current directory
        # This allows the proxy to run the target command in the correct working directory
        working_directory = os.environ.get('MCP_TARGET_CWD', str(Path.cwd()))
        
        # Start the enhanced proxy (this runs until interrupted)
        logger.info("🧠 Starting Enhanced MCP Proxy with LLM decision tracking...")
        logger.info(f"🏠 Target working directory: {working_directory}")
        logger.info(f"🏷️  Server identification: {server_name}")
        await enhanced_proxy.start_proxy_server(working_directory=working_directory)
        logger.info("✅ Enhanced proxy shutdown completed")
            
    except Exception as e:
        logger.error(f"Enhanced proxy runner error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 