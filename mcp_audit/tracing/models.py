"""
Comprehensive Tracing Models for MCP Component Flow.

Captures complete end-to-end traces from user input through all components.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import uuid


class ComponentType(str, Enum):
    """Types of components in the MCP ecosystem."""
    USER_INTERFACE = "user_interface"
    MCP_HOST = "mcp_host"
    LLM_ENGINE = "llm_engine"
    MCP_CLIENT = "mcp_client"
    MCP_SERVER = "mcp_server"
    EXTERNAL_API = "external_api"
    AUDIT_AGENT = "audit_agent"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    NETWORK = "network"


class TraceEventType(str, Enum):
    """Types of trace events."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    FUNCTION_CALL = "function_call"
    FUNCTION_RETURN = "function_return"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    ERROR_OCCURRED = "error_occurred"
    RETRY_ATTEMPT = "retry_attempt"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PROCESSING = "processing"
    RESPONSE_GENERATED = "response_generated"


class TraceEvent(BaseModel):
    """Individual trace event within a component interaction."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: TraceEventType
    component: ComponentType
    component_name: str
    description: str
    
    # Event data
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing information
    duration_ms: Optional[int] = None
    cpu_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Context
    parent_event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def is_error(self) -> bool:
        """Check if this event represents an error."""
        return self.event_type == TraceEventType.ERROR_OCCURRED or self.error_code is not None


class ComponentInteraction(BaseModel):
    """Interaction between two components."""
    interaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    # Components involved
    source_component: ComponentType
    source_name: str
    target_component: ComponentType
    target_name: str
    
    # Interaction details
    operation: str
    protocol: str = "unknown"  # JSON-RPC, HTTP, WebSocket, etc.
    method: Optional[str] = None
    
    # Data flow
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    latency_ms: Optional[int] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    
    # Status
    success: bool = True
    status_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Correlation tracking
    correlation_id: Optional[str] = None
    
    # Events within this interaction
    events: List[TraceEvent] = Field(default_factory=list)
    
    def add_event(self, event: TraceEvent) -> None:
        """Add an event to this interaction."""
        self.events.append(event)
    
    def get_duration_ms(self) -> int:
        """Get the total duration of this interaction."""
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


class RequestFlow(BaseModel):
    """Complete flow of a user request through all components."""
    flow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Request metadata
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    user_query: str
    session_id: Optional[str] = None
    
    # Flow status
    status: str = "in_progress"  # in_progress, completed, failed, timeout
    final_response: Optional[str] = None
    error_summary: Optional[str] = None
    
    # Component interactions
    interactions: List[ComponentInteraction] = Field(default_factory=list)
    
    # Flow metrics
    total_latency_ms: Optional[int] = None
    component_count: int = 0
    api_calls_count: int = 0
    retry_count: int = 0
    error_count: int = 0
    
    def add_interaction(self, interaction: ComponentInteraction) -> None:
        """Add a component interaction to this flow."""
        interaction.correlation_id = self.correlation_id
        self.interactions.append(interaction)
        self.component_count = len(set(
            [i.source_component for i in self.interactions] + 
            [i.target_component for i in self.interactions]
        ))
    
    def complete_flow(self, final_response: Optional[str] = None, error: Optional[str] = None) -> None:
        """Mark the flow as completed."""
        self.end_time = datetime.utcnow()
        self.final_response = final_response
        self.error_summary = error
        self.status = "failed" if error else "completed"
        
        if self.start_time and self.end_time:
            self.total_latency_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        
        # Calculate metrics
        self.api_calls_count = len([i for i in self.interactions if i.target_component == ComponentType.EXTERNAL_API])
        self.retry_count = len([i for i in self.interactions if "retry" in i.operation.lower()])
        self.error_count = len([i for i in self.interactions if not i.success])
    
    def get_component_chain(self) -> List[str]:
        """Get the chain of components involved in this flow."""
        chain = []
        for interaction in self.interactions:
            if interaction.source_name not in chain:
                chain.append(interaction.source_name)
            if interaction.target_name not in chain:
                chain.append(interaction.target_name)
        return chain
    
    def get_critical_path(self) -> List[ComponentInteraction]:
        """Get the critical path (longest latency chain) through the flow."""
        # Sort interactions by latency descending
        return sorted(
            [i for i in self.interactions if i.latency_ms], 
            key=lambda x: x.latency_ms or 0, 
            reverse=True
        )
    
    def get_error_points(self) -> List[ComponentInteraction]:
        """Get all interaction points where errors occurred."""
        return [i for i in self.interactions if not i.success]


class TraceAnalysis(BaseModel):
    """Analysis of a complete request flow trace."""
    flow_id: str
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Performance analysis
    total_duration_ms: int
    critical_path_duration_ms: int
    network_latency_ms: int
    processing_time_ms: int
    
    # Component analysis
    component_performance: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    bottleneck_components: List[str] = Field(default_factory=list)
    efficient_components: List[str] = Field(default_factory=list)
    
    # Error analysis
    error_points: List[Dict[str, Any]] = Field(default_factory=list)
    retry_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    failure_cascade: List[str] = Field(default_factory=list)
    
    # Flow characteristics
    complexity_score: float = 0.0  # 0-100
    efficiency_score: float = 0.0  # 0-100
    reliability_score: float = 0.0  # 0-100
    
    # Recommendations
    performance_recommendations: List[str] = Field(default_factory=list)
    reliability_recommendations: List[str] = Field(default_factory=list)
    optimization_opportunities: List[str] = Field(default_factory=list)


class TraceSession(BaseModel):
    """Collection of related request flows in a session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    # Session metadata
    user_id: Optional[str] = None
    host_info: Optional[Dict[str, Any]] = None
    server_list: List[str] = Field(default_factory=list)
    
    # Request flows
    flows: List[RequestFlow] = Field(default_factory=list)
    
    # Session metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    
    def add_flow(self, flow: RequestFlow) -> None:
        """Add a request flow to this session."""
        flow.session_id = self.session_id
        self.flows.append(flow)
        self._update_metrics()
    
    def _update_metrics(self) -> None:
        """Update session metrics."""
        self.total_requests = len(self.flows)
        self.successful_requests = len([f for f in self.flows if f.status == "completed"])
        self.failed_requests = len([f for f in self.flows if f.status == "failed"])
        
        completed_flows = [f for f in self.flows if f.total_latency_ms]
        if completed_flows:
            self.avg_response_time_ms = sum(f.total_latency_ms for f in completed_flows) / len(completed_flows)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session."""
        return {
            "session_id": self.session_id,
            "duration_minutes": (
                (self.end_time or datetime.utcnow()) - self.start_time
            ).total_seconds() / 60,
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "avg_response_time_ms": self.avg_response_time_ms,
            "unique_servers": len(set(self.server_list)),
            "component_types_used": len(set(
                i.source_component for flow in self.flows for i in flow.interactions
            ))
        } 