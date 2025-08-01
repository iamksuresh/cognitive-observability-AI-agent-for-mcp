"""
Core data models for MCP Usability Audit Agent.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class MCPMessageDirection(str, Enum):
    """Direction of MCP message flow."""
    USER_TO_LLM = "user→llm"
    LLM_TO_MCP_CLIENT = "llm→mcp_client"
    MCP_CLIENT_TO_SERVER = "mcp_client→server"
    SERVER_TO_API = "server→api"


class MCPProtocol(str, Enum):
    """MCP transport protocol types."""
    JSON_RPC = "JSON-RPC"
    HTTP = "HTTP"
    WEBSOCKET = "WebSocket"
    STDIO = "stdio"


class UsabilityIssueType(str, Enum):
    """Types of usability issues that can be detected."""
    AUTHENTICATION_FRICTION = "authentication_friction"
    PARAMETER_CONFUSION = "parameter_confusion"
    ERROR_RECOVERY_ISSUES = "error_recovery_issues"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    ONBOARDING_COMPLEXITY = "onboarding_complexity"
    TOOL_DISCOVERY_PROBLEMS = "tool_discovery_problems"


class IssueSeverity(str, Enum):
    """Severity levels for usability issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MCPMessageTrace(BaseModel):
    """Individual MCP message trace data."""
    direction: MCPMessageDirection
    protocol: MCPProtocol
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[int] = None
    error_code: Optional[str] = None
    retry_attempt: Optional[int] = None


class ConversationContext(BaseModel):
    """Captures the user conversation context that led to MCP interactions."""
    user_prompt: str  # The actual user message that triggered the interaction
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    message_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context enrichment
    preceding_messages: List[str] = Field(default_factory=list)  # Previous messages in conversation
    user_intent: Optional[str] = None  # AI-inferred user intent
    complexity_level: Optional[str] = None  # simple, moderate, complex
    
    # Tool context
    tools_available: List[str] = Field(default_factory=list)
    tools_suggested: List[str] = Field(default_factory=list)
    
    # Metadata
    host_interface: str = "cursor"  # cursor, cli, api, etc.
    response_format: Optional[str] = None  # json, text, markdown


class MCPInteraction(BaseModel):
    """Complete MCP interaction session data."""
    session_id: str
    server_name: str
    user_query: str  # Legacy field - now derived from conversation_context
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    message_traces: List[MCPMessageTrace] = Field(default_factory=list)
    success: bool = False
    total_latency_ms: Optional[int] = None
    retry_count: int = 0
    user_context: Optional[Dict[str, Any]] = None
    
    # New: Rich conversation context
    conversation_context: Optional[ConversationContext] = None
    
    def get_actual_user_prompt(self) -> str:
        """Get the actual user prompt from conversation context, fallback to extracted query."""
        if self.conversation_context:
            return self.conversation_context.user_prompt
        return self.user_query


class CognitiveLoadMetrics(BaseModel):
    """Cognitive load analysis metrics."""
    overall_score: float = Field(ge=0, le=100, description="Overall cognitive load score (0-100)")
    prompt_complexity: float = Field(ge=0, le=100)
    context_switching: float = Field(ge=0, le=100)
    retry_frustration: float = Field(ge=0, le=100)
    configuration_friction: float = Field(ge=0, le=100)
    integration_cognition: float = Field(ge=0, le=100)
    
    # Detailed breakdown information
    retry_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Detailed breakdown of retry frustration calculation")
    configuration_breakdown: Optional[Dict[str, Any]] = Field(default=None, description="Detailed breakdown of configuration friction calculation")
    
    def get_load_description(self) -> str:
        """Get human-readable description of cognitive load."""
        if self.overall_score > 80:
            return "HIGH FRICTION - User likely struggling"
        elif self.overall_score > 60:
            return "MEDIUM FRICTION - Some confusion detected"
        else:
            return "LOW FRICTION - Smooth interaction"


class UsabilityIssue(BaseModel):
    """Individual usability issue detected."""
    type: UsabilityIssueType
    severity: IssueSeverity
    description: str
    frequency: int = 1
    impact_description: str
    suggested_fix: str
    estimated_improvement: Optional[float] = None


class UsabilityRecommendation(BaseModel):
    """Actionable usability recommendation."""
    priority: IssueSeverity
    category: str
    issue: str
    impact: str
    effort: str = Field(description="low, medium, high")
    recommendation: str
    estimated_improvement: float
    implementation_steps: List[str] = Field(default_factory=list)


class SessionSummary(BaseModel):
    """Summary of monitoring session."""
    total_sessions: int
    successful_completions: int
    avg_session_duration_ms: float
    abandonment_rate: float
    common_abandonment_points: List[str] = Field(default_factory=list)


class CommunicationPatterns(BaseModel):
    """Analysis of communication patterns."""
    avg_prompt_tokens: Optional[int] = None
    avg_response_time_ms: float
    retry_rate: float
    confidence_decline: bool = False
    common_confusion_triggers: List[str] = Field(default_factory=list)
    
    tool_discovery_success_rate: float
    first_attempt_success_rate: float
    avg_parameter_errors: float
    common_failure_points: List[str] = Field(default_factory=list)


class BenchmarkingData(BaseModel):
    """Ecosystem benchmarking information."""
    percentile_rank: Optional[int] = None
    total_servers_in_category: Optional[int] = None
    category: Optional[str] = None
    better_than_servers: List[str] = Field(default_factory=list)
    worse_than_servers: List[str] = Field(default_factory=list)
    best_practice_gaps: List[str] = Field(default_factory=list)


class UsabilityInsights(BaseModel):
    """Real-time usability insights."""
    cognitive_load: CognitiveLoadMetrics
    current_interaction: Optional[MCPInteraction] = None
    detected_issues: List[UsabilityIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    interaction_timeline: List[Dict[str, Any]] = Field(default_factory=list)


class UsabilityReport(BaseModel):
    """Complete usability analysis report."""
    # Report metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_window_hours: float = 24.0
    server_name: str
    server_version: Optional[str] = None
    server_repository: Optional[str] = None
    
    # Executive summary
    overall_usability_score: float = Field(ge=0, le=100)
    grade: str = Field(description="A, B, C, D, or F")
    primary_concerns: List[str] = Field(default_factory=list)
    key_wins: List[str] = Field(default_factory=list)
    
    # Session analytics
    session_summary: SessionSummary
    
    # Cognitive load analysis
    cognitive_load: CognitiveLoadMetrics
    
    # Communication patterns
    communication_patterns: CommunicationPatterns
    
    # Usability insights
    detected_issues: List[UsabilityIssue] = Field(default_factory=list)
    
    # Actionable recommendations
    recommendations: List[UsabilityRecommendation] = Field(default_factory=list)
    
    # Ecosystem benchmarking
    benchmarking: Optional[BenchmarkingData] = None
    
    def get_grade(self) -> str:
        """Calculate letter grade based on overall score."""
        if self.overall_usability_score >= 90:
            return "A"
        elif self.overall_usability_score >= 80:
            return "B"
        elif self.overall_usability_score >= 70:
            return "C"
        elif self.overall_usability_score >= 60:
            return "D"
        else:
            return "F"


class HostInfo(BaseModel):
    """Information about the MCP host being monitored."""
    name: str
    version: Optional[str] = None
    type: str = "unknown"
    mcp_protocol_version: Optional[str] = None
    connected_servers: List[str] = Field(default_factory=list)


class MonitoringConfig(BaseModel):
    """Configuration for the monitoring session."""
    host_info: Optional[HostInfo] = None
    target_servers: List[str] = Field(default_factory=list)
    observability_enabled: bool = True
    langsmith_project_id: Optional[str] = None
    helicone_api_key: Optional[str] = None
    real_time_alerts: bool = False
    cognitive_load_threshold: float = 75.0 