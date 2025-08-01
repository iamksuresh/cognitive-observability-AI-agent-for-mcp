"""
Enhanced MCP Proxy with LLM Decision Tracking.

Extends the base MCP proxy to capture LLM decision-making processes
and provide complete traceability from user prompts to tool execution.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .mcp_proxy import MCPProxy
from .llm_decision_interceptor import LLMDecisionInterceptor
from .conversation_interceptor import ConversationContextInterceptor
from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol

logger = logging.getLogger(__name__)


class EnhancedMCPProxy(MCPProxy):
    """
    Enhanced MCP Proxy with LLM decision tracking.
    
    Captures not just MCP protocol messages, but also LLM reasoning
    and decision-making processes for complete observability.
    """
    
    def __init__(self, target_server_cmd: List[str], audit_callback=None):
        super().__init__(target_server_cmd, audit_callback)
        
        # Enhanced interceptors
        self.llm_interceptor = LLMDecisionInterceptor()
        self.conversation_interceptor = ConversationContextInterceptor()
        
        # LLM decision tracking
        self.active_reasoning_sessions = {}
        self.tool_call_patterns = {
            'tool_call': re.compile(r'"method":\s*"tools/call"'),
            'tool_list': re.compile(r'"method":\s*"tools/list"'),
            'initialization': re.compile(r'"method":\s*"initialize"')
        }
        
        # Enhanced logging
        self.enhanced_log_file = Path.home() / ".cursor" / "enhanced_mcp_trace.jsonl"
    
    async def _capture_message(self, message: str, direction: MCPMessageDirection):
        """Override to add enhanced analysis and logging."""
        # Call parent method first  
        await super()._capture_message(message, direction)
        
        # Parse message for enhanced analysis
        try:
            if message.strip():
                payload = json.loads(message)
                
                # Create trace object for enhanced analysis
                trace = MCPMessageTrace(
                    direction=direction,
                    protocol=MCPProtocol.JSON_RPC,
                    payload=payload,
                    timestamp=datetime.utcnow(),
                    latency_ms=None
                )
                
                # Enhanced analysis
                await self._analyze_llm_decision(payload, direction)
                
                # Infer and capture user prompt for tool calls
                if direction == MCPMessageDirection.LLM_TO_MCP_CLIENT and payload.get('method') == 'tools/call':
                    await self._infer_and_capture_user_prompt(trace)
                
                # Enhanced logging
                await self._log_enhanced_trace(payload, direction, message)
                
        except json.JSONDecodeError:
            # Skip non-JSON messages
            pass
        except Exception as e:
            logger.error(f"Error in enhanced message capture: {e}")

    async def _infer_and_capture_user_prompt(self, trace: MCPMessageTrace):
        """Infer user prompt from tool call and capture it as conversation context."""
        try:
            tool_name = trace.payload.get('params', {}).get('name')
            tool_args = trace.payload.get('params', {}).get('arguments', {})
            
            # Generate intelligent user prompt inference based on tool and arguments
            inferred_prompt = self._generate_prompt_inference(tool_name, tool_args)
            
            if inferred_prompt:
                # Capture as conversation context
                session_id = f"inferred_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                context = await self.conversation_interceptor.capture_user_prompt(
                    user_prompt=inferred_prompt,
                    conversation_id=session_id,
                    tools_available=[tool_name],
                    host_interface='cursor'
                )
                
                # ✅ NEW: Store context for correlation with MCP interactions
                self._store_context_for_correlation(trace, context)
                
                logger.info(f"💬 Inferred user prompt: \"{inferred_prompt}\"")
                
        except Exception as e:
            logger.error(f"Error inferring user prompt: {e}")
    
    def _store_context_for_correlation(self, trace: MCPMessageTrace, context):
        """Store conversation context for correlation with MCP interactions."""
        # Create a recent context map for correlation
        if not hasattr(self, '_recent_contexts'):
            self._recent_contexts = {}
        
        # Use tool call ID for correlation
        call_id = trace.payload.get('id')
        if call_id:
            self._recent_contexts[call_id] = context
            logger.debug(f"🔗 Stored context for correlation: ID {call_id}")
    
    def _get_context_for_interaction(self, call_id) -> Optional[object]:
        """Retrieve stored conversation context for an interaction."""
        if hasattr(self, '_recent_contexts') and call_id in self._recent_contexts:
            context = self._recent_contexts.pop(call_id)  # Remove after use
            logger.debug(f"🔗 Retrieved context for interaction: ID {call_id}")
            return context
        return None

    def _generate_prompt_inference(self, tool_name: str, tool_args: dict) -> str:
        """Generate intelligent user prompt inference based on tool usage."""
        
        # Mastra course tools
        if tool_name == 'getMastraCourseStatus':
            return "get me the course status"
        elif tool_name == 'startMastraCourse':
            email = tool_args.get('email', '')
            return f"begin mastra course" + (f" with {email}" if email else "")
        elif tool_name == 'nextMastraCourseStep':
            return "continue to next step" 
        elif tool_name == 'clearMastraCourseHistory':
            return "clear the course history"
        elif tool_name == 'startMastraCourseLesson':
            lesson = tool_args.get('lessonName', '')
            return f"start lesson {lesson}" if lesson else "start a lesson"
            
        # General tool patterns
        elif 'search' in tool_name.lower():
            query = tool_args.get('query', tool_args.get('search_term', ''))
            return f"search for {query}" if query else "search for something"
        elif 'file' in tool_name.lower():
            filename = tool_args.get('target_file', tool_args.get('file', ''))
            return f"work with file {filename}" if filename else "work with a file"
        elif 'memory' in tool_name.lower():
            return "access or update memory"
        elif 'workflow' in tool_name.lower():
            return "run workflow or automation"
            
        # Generic fallback
        else:
            return f"use {tool_name} tool"
    
    async def _analyze_llm_decision(self, json_data: Dict[str, Any], direction: MCPMessageDirection):
        """Analyze message for LLM decision-making patterns."""
        try:
            method = json_data.get('method')
            
            if direction == MCPMessageDirection.LLM_TO_MCP_CLIENT:
                # This is Claude making a decision to use tools
                
                if method == 'tools/list':
                    # Claude is discovering available tools
                    await self._handle_tool_discovery(json_data)
                    
                elif method == 'tools/call':
                    # Claude has decided to call a specific tool
                    await self._handle_tool_call_decision(json_data)
                    
                elif method == 'initialize':
                    # Claude is initializing MCP connection
                    await self._handle_mcp_initialization(json_data)
            
            elif direction == MCPMessageDirection.MCP_CLIENT_TO_SERVER:
                # This could be responses or server-side processing
                if 'result' in json_data:
                    await self._handle_tool_response(json_data)
            
        except Exception as e:
            logger.error(f"Error analyzing LLM decision: {e}")
    
    async def _handle_tool_discovery(self, json_data: Dict[str, Any]):
        """Handle LLM tool discovery process."""
        try:
            # Start a new reasoning session
            session_id = f"discovery_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Capture this as the start of LLM reasoning
            decision_id = await self.llm_interceptor.capture_llm_reasoning(
                user_prompt="[Tool Discovery] Claude exploring available tools",
                available_tools=["tools/list"],  # Will be updated when we get the response
                decision_id=session_id
            )
            
            self.active_reasoning_sessions[session_id] = {
                'decision_id': decision_id,
                'phase': 'discovery',
                'start_time': datetime.utcnow()
            }
            
            logger.info(f"🔍 LLM started tool discovery: {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling tool discovery: {e}")
    
    async def _handle_tool_call_decision(self, json_data: Dict[str, Any]):
        """Handle LLM tool call decision."""
        try:
            params = json_data.get('params', {})
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            
            # Find or create reasoning session
            session_id = f"call_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Start reasoning session if not already active
            if session_id not in self.active_reasoning_sessions:
                decision_id = await self.llm_interceptor.capture_llm_reasoning(
                    user_prompt="[Inferred] User request requiring tool usage",
                    available_tools=[tool_name],
                    decision_id=session_id
                )
                
                self.active_reasoning_sessions[session_id] = {
                    'decision_id': decision_id,
                    'phase': 'execution',
                    'start_time': datetime.utcnow()
                }
            
            reasoning_session = self.active_reasoning_sessions[session_id]
            decision_id = reasoning_session['decision_id']
            
            # Capture tool selection
            await self.llm_interceptor.capture_tool_selection(
                decision_id=decision_id,
                selected_tools=[tool_name],
                reasoning=f"Claude selected {tool_name} to handle user request",
                confidence=0.8  # Estimated confidence for successful tool calls
            )
            
            # Capture tool call
            await self.llm_interceptor.capture_tool_call(
                decision_id=decision_id,
                tool_name=tool_name,
                tool_args=tool_args
            )
            
            logger.info(f"🎯 LLM decided to call tool: {tool_name}")
            
        except Exception as e:
            logger.error(f"Error handling tool call decision: {e}")
    
    async def _handle_mcp_initialization(self, json_data: Dict[str, Any]):
        """Handle MCP connection initialization."""
        try:
            capabilities = json_data.get('params', {}).get('capabilities', {})
            
            logger.info(f"🔌 MCP initialization with capabilities: {list(capabilities.keys())}")
            
            # This represents Claude setting up its tool environment
            session_id = f"init_{int(datetime.utcnow().timestamp() * 1000)}"
            
            decision_id = await self.llm_interceptor.capture_llm_reasoning(
                user_prompt="[System] MCP connection initialization",
                available_tools=list(capabilities.keys()),
                decision_id=session_id
            )
            
            await self.llm_interceptor.capture_tool_selection(
                decision_id=decision_id,
                selected_tools=["MCP_SETUP"],
                reasoning="Claude initializing MCP connection for tool access"
            )
            
        except Exception as e:
            logger.error(f"Error handling MCP initialization: {e}")
    
    async def _handle_tool_response(self, json_data: Dict[str, Any]):
        """Handle tool execution responses."""
        try:
            result = json_data.get('result')
            
            # Find active reasoning session to complete
            active_sessions = list(self.active_reasoning_sessions.keys())
            
            if active_sessions:
                # Complete the most recent session
                session_id = active_sessions[-1]
                reasoning_session = self.active_reasoning_sessions.pop(session_id)
                decision_id = reasoning_session['decision_id']
                
                # Determine success based on response
                success = 'error' not in json_data and result is not None
                
                final_reasoning = f"Tool execution {'succeeded' if success else 'failed'}"
                if result:
                    final_reasoning += f" with result type: {type(result).__name__}"
                
                await self.llm_interceptor.complete_decision(
                    decision_id=decision_id,
                    success=success,
                    final_reasoning=final_reasoning
                )
                
                logger.info(f"✅ Completed LLM decision session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling tool response: {e}")
    
    async def _log_enhanced_trace(self, json_data: Dict[str, Any], direction: MCPMessageDirection, raw_message: str):
        """Log enhanced trace with LLM decision context."""
        try:
            # Create enhanced trace entry
            enhanced_trace = {
                "timestamp": datetime.utcnow().isoformat(),
                "direction": direction.value,
                "protocol": MCPProtocol.JSON_RPC.value,
                "payload": json_data,
                "raw_message_length": len(raw_message),
                "llm_decision_context": self._extract_decision_context(json_data, direction),
                "message_classification": self._classify_message(json_data, direction)
            }
            
            # Ensure directory exists
            self.enhanced_log_file.parent.mkdir(exist_ok=True)
            
            # Append to enhanced log
            with open(self.enhanced_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(enhanced_trace) + '\n')
                
        except Exception as e:
            logger.error(f"Error logging enhanced trace: {e}")
    
    def _extract_decision_context(self, json_data: Dict[str, Any], direction: MCPMessageDirection) -> Dict[str, Any]:
        """Extract LLM decision context from message."""
        context = {
            "is_llm_initiated": direction == MCPMessageDirection.LLM_TO_MCP_CLIENT,
            "tool_related": False,
            "reasoning_phase": None
        }
        
        method = json_data.get('method')
        
        if method:
            context["tool_related"] = method.startswith('tools/')
            
            if method == 'tools/list':
                context["reasoning_phase"] = "discovery"
            elif method == 'tools/call':
                context["reasoning_phase"] = "execution"
                context["tool_name"] = json_data.get('params', {}).get('name')
            elif method == 'initialize':
                context["reasoning_phase"] = "initialization"
        
        return context
    
    def _classify_message(self, json_data: Dict[str, Any], direction: MCPMessageDirection) -> str:
        """Classify the message type for reporting."""
        if direction == MCPMessageDirection.LLM_TO_MCP_CLIENT:
            method = json_data.get('method')
            if method == 'tools/call':
                return "LLM_TOOL_EXECUTION"
            elif method == 'tools/list':
                return "LLM_TOOL_DISCOVERY"
            elif method == 'initialize':
                return "LLM_MCP_SETUP"
            else:
                return "LLM_OTHER_COMMAND"
        
        elif direction == MCPMessageDirection.MCP_CLIENT_TO_SERVER:
            if 'result' in json_data:
                return "TOOL_RESPONSE"
            elif 'error' in json_data:
                return "TOOL_ERROR"
            else:
                return "SERVER_MESSAGE"
        
        return "UNKNOWN"
    
    async def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics including LLM decision patterns."""
        base_stats = {
            "total_messages": len(self.captured_messages),
            "message_counter": self.message_counter
        }
        
        # Add LLM decision statistics
        llm_stats = self.llm_interceptor.get_decision_statistics()
        
        # Add correlation data
        correlations = self.llm_interceptor.correlate_with_mcp_messages(
            self.captured_messages, 
            time_window_seconds=30
        )
        
        return {
            **base_stats,
            "llm_decisions": llm_stats,
            "correlation_count": len(correlations),
            "active_reasoning_sessions": len(self.active_reasoning_sessions)
        } 