"""
LLM Decision Interceptor.

Captures LLM decision-making process and tool selection reasoning
to provide complete traceability from user prompt to tool execution.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.models import MCPMessageTrace, MCPMessageDirection, MCPProtocol

logger = logging.getLogger(__name__)


class LLMDecisionTrace:
    """Represents an LLM decision-making process."""
    
    def __init__(self):
        self.timestamp = datetime.utcnow()
        self.user_prompt: Optional[str] = None
        self.llm_reasoning: Optional[str] = None
        self.tools_considered: List[str] = []
        self.tools_selected: List[str] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.confidence_score: Optional[float] = None
        self.processing_time_ms: Optional[int] = None


class LLMDecisionInterceptor:
    """
    Intercepts and analyzes LLM decision-making processes.
    
    Captures the reasoning layer between user prompts and tool calls
    to provide cognitive insights into AI agent behavior.
    """
    
    def __init__(self):
        """Initialize the LLM decision interceptor."""
        self.decision_log: List[LLMDecisionTrace] = []
        self.active_decisions: Dict[str, LLMDecisionTrace] = {}
        
        # Storage
        self.log_file = Path.home() / ".cursor" / "llm_decision_trace.jsonl"
        
    async def capture_llm_reasoning(
        self,
        user_prompt: str,
        available_tools: List[str],
        decision_id: Optional[str] = None
    ) -> str:
        """
        Capture the start of LLM reasoning process.
        
        Args:
            user_prompt: The user's input that triggered reasoning
            available_tools: List of tools available to the LLM
            decision_id: Optional identifier for this decision process
            
        Returns:
            Decision ID for tracking this reasoning session
        """
        try:
            decision_id = decision_id or f"decision_{int(datetime.utcnow().timestamp() * 1000)}"
            
            trace = LLMDecisionTrace()
            trace.user_prompt = user_prompt
            trace.tools_considered = available_tools.copy()
            
            self.active_decisions[decision_id] = trace
            
            logger.info(f"🧠 Started LLM reasoning for: {user_prompt[:50]}...")
            return decision_id
            
        except Exception as e:
            logger.error(f"Error capturing LLM reasoning: {e}")
            return decision_id or "error"
    
    async def capture_tool_selection(
        self,
        decision_id: str,
        selected_tools: List[str],
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> None:
        """
        Capture LLM tool selection decision.
        
        Args:
            decision_id: The decision session identifier
            selected_tools: Tools selected by the LLM
            reasoning: Optional reasoning text from the LLM
            confidence: Optional confidence score (0-1)
        """
        try:
            if decision_id not in self.active_decisions:
                logger.warning(f"Unknown decision ID: {decision_id}")
                return
            
            trace = self.active_decisions[decision_id]
            trace.tools_selected = selected_tools
            trace.llm_reasoning = reasoning
            trace.confidence_score = confidence
            
            logger.info(f"🎯 LLM selected tools: {selected_tools}")
            
        except Exception as e:
            logger.error(f"Error capturing tool selection: {e}")
    
    async def capture_tool_call(
        self,
        decision_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        call_timestamp: Optional[datetime] = None
    ) -> None:
        """
        Capture actual tool call execution.
        
        Args:
            decision_id: The decision session identifier
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool
            call_timestamp: When the call was made
        """
        try:
            if decision_id not in self.active_decisions:
                logger.warning(f"Unknown decision ID: {decision_id}")
                return
            
            trace = self.active_decisions[decision_id]
            
            tool_call = {
                "tool_name": tool_name,
                "arguments": tool_args,
                "timestamp": (call_timestamp or datetime.utcnow()).isoformat(),
                "call_id": f"{tool_name}_{len(trace.tool_calls)}"
            }
            
            trace.tool_calls.append(tool_call)
            
            logger.info(f"🔧 Tool called: {tool_name}")
            
        except Exception as e:
            logger.error(f"Error capturing tool call: {e}")
    
    async def complete_decision(
        self,
        decision_id: str,
        success: bool = True,
        final_reasoning: Optional[str] = None
    ) -> LLMDecisionTrace:
        """
        Complete a decision-making process.
        
        Args:
            decision_id: The decision session identifier
            success: Whether the decision process was successful
            final_reasoning: Optional final reasoning or reflection
            
        Returns:
            Completed LLMDecisionTrace
        """
        try:
            if decision_id not in self.active_decisions:
                logger.warning(f"Unknown decision ID: {decision_id}")
                return None
            
            trace = self.active_decisions.pop(decision_id)
            
            # Calculate processing time
            processing_time = datetime.utcnow() - trace.timestamp
            trace.processing_time_ms = int(processing_time.total_seconds() * 1000)
            
            if final_reasoning:
                trace.llm_reasoning = (trace.llm_reasoning or "") + f"\n[Final] {final_reasoning}"
            
            # Store completed trace
            self.decision_log.append(trace)
            await self._persist_decision(trace, success)
            
            logger.info(f"✅ Completed LLM decision in {trace.processing_time_ms}ms")
            return trace
            
        except Exception as e:
            logger.error(f"Error completing decision: {e}")
            return None
    
    def correlate_with_mcp_messages(
        self,
        mcp_messages: List[MCPMessageTrace],
        time_window_seconds: int = 10
    ) -> Dict[str, List[MCPMessageTrace]]:
        """
        Correlate LLM decisions with MCP message traces.
        
        Args:
            mcp_messages: List of MCP message traces
            time_window_seconds: Time window for correlation
            
        Returns:
            Dictionary mapping decision IDs to correlated MCP messages
        """
        correlations = {}
        
        for trace in self.decision_log:
            correlations[f"decision_{trace.timestamp.isoformat()}"] = []
            
            # Find MCP messages within time window
            window_start = trace.timestamp - timedelta(seconds=time_window_seconds)
            window_end = trace.timestamp + timedelta(seconds=time_window_seconds)
            
            for mcp_msg in mcp_messages:
                if window_start <= mcp_msg.timestamp <= window_end:
                    # Check if this MCP message relates to our tools
                    if (mcp_msg.direction == MCPMessageDirection.LLM_TO_MCP_CLIENT and
                        mcp_msg.payload.get('method') == 'tools/call'):
                        
                        tool_name = mcp_msg.payload.get('params', {}).get('name')
                        if tool_name in trace.tools_selected:
                            correlations[f"decision_{trace.timestamp.isoformat()}"].append(mcp_msg)
        
        return correlations
    
    async def _persist_decision(self, trace: LLMDecisionTrace, success: bool):
        """Persist decision trace to disk."""
        try:
            # Ensure directory exists
            self.log_file.parent.mkdir(exist_ok=True)
            
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "timestamp": trace.timestamp.isoformat(),
                    "user_prompt": trace.user_prompt,
                    "llm_reasoning": trace.llm_reasoning,
                    "tools_considered": trace.tools_considered,
                    "tools_selected": trace.tools_selected,
                    "tool_calls": trace.tool_calls,
                    "confidence_score": trace.confidence_score,
                    "processing_time_ms": trace.processing_time_ms,
                    "success": success
                }) + '\n')
                
        except Exception as e:
            logger.error(f"Error persisting decision trace: {e}")
    
    def get_recent_decisions(self, hours_back: float = 24.0) -> List[LLMDecisionTrace]:
        """Get recent decision traces."""
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        return [trace for trace in self.decision_log if trace.timestamp >= cutoff]
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics about LLM decision-making patterns."""
        if not self.decision_log:
            return {}
        
        tool_usage = {}
        avg_processing_time = 0
        total_decisions = len(self.decision_log)
        
        for trace in self.decision_log:
            for tool in trace.tools_selected:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
            
            if trace.processing_time_ms:
                avg_processing_time += trace.processing_time_ms
        
        return {
            "total_decisions": total_decisions,
            "avg_processing_time_ms": avg_processing_time / total_decisions if total_decisions > 0 else 0,
            "tool_usage_frequency": tool_usage,
            "most_used_tool": max(tool_usage.items(), key=lambda x: x[1])[0] if tool_usage else None
        } 