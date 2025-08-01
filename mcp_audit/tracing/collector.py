"""
Trace Collector for MCP Component Interactions.

Captures and builds complete traces of request flows through all components.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from contextlib import asynccontextmanager

from .models import (
    ComponentType,
    TraceEvent,
    TraceEventType,
    ComponentInteraction,
    RequestFlow,
    TraceSession,
    TraceAnalysis
)

logger = logging.getLogger(__name__)


class TraceCollector:
    """
    Collects comprehensive traces of MCP component interactions.
    
    Builds complete request flows from user input through all components
    to final response, providing end-to-end observability.
    """
    
    def __init__(self):
        """Initialize the trace collector."""
        self.active_flows: Dict[str, RequestFlow] = {}
        self.completed_flows: List[RequestFlow] = []
        self.current_session: Optional[TraceSession] = None
        self.event_handlers: List[Callable] = []
        
        # Performance tracking
        self.start_time = time.time()
        self.trace_count = 0
        self.overhead_ms = 0.0
    
    def start_session(self, user_id: Optional[str] = None, host_info: Optional[Dict] = None) -> str:
        """Start a new tracing session."""
        self.current_session = TraceSession(
            user_id=user_id,
            host_info=host_info
        )
        logger.info(f"Started trace session: {self.current_session.session_id}")
        return self.current_session.session_id
    
    def end_session(self) -> Optional[TraceSession]:
        """End the current tracing session."""
        if self.current_session:
            self.current_session.end_time = datetime.utcnow()
            
            # Add any remaining active flows
            for flow in self.active_flows.values():
                flow.complete_flow(error="Session ended while flow was active")
                self.current_session.add_flow(flow)
            
            session = self.current_session
            self.current_session = None
            self.active_flows.clear()
            
            logger.info(f"Ended trace session: {session.session_id}")
            return session
        
        return None
    
    def start_request_flow(self, user_query: str, session_id: Optional[str] = None) -> str:
        """Start tracking a new request flow."""
        flow = RequestFlow(
            user_query=user_query,
            session_id=session_id
        )
        
        self.active_flows[flow.correlation_id] = flow
        
        # Add to current session if available
        if self.current_session:
            self.current_session.add_flow(flow)
        
        logger.debug(f"Started request flow: {flow.flow_id} for query: {user_query}")
        return flow.correlation_id
    
    def add_component_interaction(
        self,
        correlation_id: str,
        source_component: ComponentType,
        source_name: str,
        target_component: ComponentType,
        target_name: str,
        operation: str,
        protocol: str = "unknown",
        method: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        latency_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Add a component interaction to the flow."""
        start_time = time.time()
        
        try:
            if correlation_id not in self.active_flows:
                logger.warning(f"No active flow found for correlation_id: {correlation_id}")
                return ""
            
            flow = self.active_flows[correlation_id]
            
            interaction = ComponentInteraction(
                source_component=source_component,
                source_name=source_name,
                target_component=target_component,
                target_name=target_name,
                operation=operation,
                protocol=protocol,
                method=method,
                request_data=request_data,
                response_data=response_data,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message
            )
            
            flow.add_interaction(interaction)
            
            # Notify event handlers
            for handler in self.event_handlers:
                try:
                    handler(flow, interaction)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
            
            logger.debug(f"Added interaction: {source_name} -> {target_name} ({operation})")
            return interaction.interaction_id
            
        finally:
            # Track overhead
            overhead = (time.time() - start_time) * 1000
            self.overhead_ms += overhead
    
    def add_trace_event(
        self,
        correlation_id: str,
        interaction_id: str,
        event_type: TraceEventType,
        component: ComponentType,
        component_name: str,
        description: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        duration_ms: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> str:
        """Add a detailed trace event to an interaction."""
        if correlation_id not in self.active_flows:
            return ""
        
        flow = self.active_flows[correlation_id]
        
        # Find the interaction
        interaction = None
        for inter in flow.interactions:
            if inter.interaction_id == interaction_id:
                interaction = inter
                break
        
        if not interaction:
            logger.warning(f"Interaction not found: {interaction_id}")
            return ""
        
        event = TraceEvent(
            event_type=event_type,
            component=component,
            component_name=component_name,
            description=description,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=error_message,
            correlation_id=correlation_id
        )
        
        interaction.add_event(event)
        
        logger.debug(f"Added trace event: {event_type.value} in {component_name}")
        return event.event_id
    
    def complete_request_flow(
        self,
        correlation_id: str,
        final_response: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[RequestFlow]:
        """Complete a request flow."""
        if correlation_id not in self.active_flows:
            logger.warning(f"No active flow to complete: {correlation_id}")
            return None
        
        flow = self.active_flows.pop(correlation_id)
        flow.complete_flow(final_response=final_response, error=error)
        
        self.completed_flows.append(flow)
        self.trace_count += 1
        
        logger.info(f"Completed flow {flow.flow_id}: {flow.status} in {flow.total_latency_ms}ms")
        return flow
    
    @asynccontextmanager
    async def trace_interaction(
        self,
        correlation_id: str,
        source_component: ComponentType,
        source_name: str,
        target_component: ComponentType,
        target_name: str,
        operation: str,
        protocol: str = "unknown",
        method: Optional[str] = None
    ):
        """Context manager for tracing an interaction."""
        start_time = datetime.utcnow()
        interaction_id = None
        
        try:
            # Start the interaction
            interaction_id = self.add_component_interaction(
                correlation_id=correlation_id,
                source_component=source_component,
                source_name=source_name,
                target_component=target_component,
                target_name=target_name,
                operation=operation,
                protocol=protocol,
                method=method,
                success=True  # Will be updated on error
            )
            
            # Add start event
            self.add_trace_event(
                correlation_id=correlation_id,
                interaction_id=interaction_id,
                event_type=TraceEventType.REQUEST_START,
                component=source_component,
                component_name=source_name,
                description=f"Starting {operation} to {target_name}"
            )
            
            yield interaction_id
            
        except Exception as e:
            # Mark as failed and add error event
            if interaction_id and correlation_id in self.active_flows:
                flow = self.active_flows[correlation_id]
                for interaction in flow.interactions:
                    if interaction.interaction_id == interaction_id:
                        interaction.success = False
                        interaction.error_message = str(e)
                        break
                
                self.add_trace_event(
                    correlation_id=correlation_id,
                    interaction_id=interaction_id,
                    event_type=TraceEventType.ERROR_OCCURRED,
                    component=source_component,
                    component_name=source_name,
                    description=f"Error in {operation}: {str(e)}",
                    error_message=str(e)
                )
            
            raise
        
        finally:
            # Add end event with timing
            if interaction_id:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Update interaction timing
                if correlation_id in self.active_flows:
                    flow = self.active_flows[correlation_id]
                    for interaction in flow.interactions:
                        if interaction.interaction_id == interaction_id:
                            interaction.end_time = datetime.utcnow()
                            interaction.latency_ms = duration_ms
                            break
                
                self.add_trace_event(
                    correlation_id=correlation_id,
                    interaction_id=interaction_id,
                    event_type=TraceEventType.REQUEST_END,
                    component=target_component,
                    component_name=target_name,
                    description=f"Completed {operation}",
                    duration_ms=duration_ms
                )
    
    def add_event_handler(self, handler: Callable) -> None:
        """Add an event handler for real-time trace processing."""
        self.event_handlers.append(handler)
    
    def get_active_flows(self) -> List[RequestFlow]:
        """Get all currently active flows."""
        return list(self.active_flows.values())
    
    def get_completed_flows(self) -> List[RequestFlow]:
        """Get all completed flows."""
        return self.completed_flows.copy()
    
    def get_flow_by_id(self, flow_id: str) -> Optional[RequestFlow]:
        """Get a specific flow by ID."""
        # Check active flows
        for flow in self.active_flows.values():
            if flow.flow_id == flow_id:
                return flow
        
        # Check completed flows
        for flow in self.completed_flows:
            if flow.flow_id == flow_id:
                return flow
        
        return None
    
    def analyze_flow(self, flow_id: str) -> Optional[TraceAnalysis]:
        """Analyze a completed flow for performance and issues."""
        flow = self.get_flow_by_id(flow_id)
        if not flow or flow.status == "in_progress":
            return None
        
        # Calculate performance metrics
        total_duration = flow.total_latency_ms or 0
        critical_path = flow.get_critical_path()
        critical_path_duration = sum(i.latency_ms or 0 for i in critical_path)
        
        # Analyze components
        component_performance = {}
        for interaction in flow.interactions:
            comp_name = interaction.target_name
            if comp_name not in component_performance:
                component_performance[comp_name] = {
                    "total_time_ms": 0,
                    "call_count": 0,
                    "error_count": 0,
                    "avg_latency_ms": 0
                }
            
            perf = component_performance[comp_name]
            perf["total_time_ms"] += interaction.latency_ms or 0
            perf["call_count"] += 1
            if not interaction.success:
                perf["error_count"] += 1
            perf["avg_latency_ms"] = perf["total_time_ms"] / perf["call_count"]
        
        # Identify bottlenecks and efficient components
        bottlenecks = []
        efficient = []
        
        for comp_name, perf in component_performance.items():
            if perf["avg_latency_ms"] > 1000:  # > 1 second
                bottlenecks.append(comp_name)
            elif perf["avg_latency_ms"] < 100 and perf["error_count"] == 0:  # < 100ms, no errors
                efficient.append(comp_name)
        
        # Calculate scores
        complexity_score = min(len(flow.interactions) * 10, 100)
        efficiency_score = max(0, 100 - (total_duration / 1000) * 10)  # Penalty for slow responses
        error_rate = flow.error_count / max(len(flow.interactions), 1)
        reliability_score = max(0, 100 - error_rate * 100)
        
        # Generate recommendations
        recommendations = []
        if bottlenecks:
            recommendations.append(f"Optimize bottleneck components: {', '.join(bottlenecks)}")
        if flow.retry_count > 0:
            recommendations.append("Reduce retry frequency by improving error handling")
        if total_duration > 5000:  # > 5 seconds
            recommendations.append("Investigate overall response time - consider caching or parallel processing")
        
        return TraceAnalysis(
            flow_id=flow_id,
            total_duration_ms=total_duration,
            critical_path_duration_ms=critical_path_duration,
            network_latency_ms=sum(
                i.latency_ms or 0 for i in flow.interactions 
                if i.target_component == ComponentType.EXTERNAL_API
            ),
            processing_time_ms=total_duration - sum(
                i.latency_ms or 0 for i in flow.interactions 
                if i.target_component == ComponentType.EXTERNAL_API
            ),
            component_performance=component_performance,
            bottleneck_components=bottlenecks,
            efficient_components=efficient,
            error_points=[
                {
                    "component": i.target_name,
                    "error": i.error_message,
                    "operation": i.operation
                }
                for i in flow.get_error_points()
            ],
            complexity_score=complexity_score,
            efficiency_score=efficiency_score,
            reliability_score=reliability_score,
            performance_recommendations=recommendations
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics."""
        uptime_seconds = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime_seconds,
            "traces_collected": self.trace_count,
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.completed_flows),
            "avg_overhead_ms": self.overhead_ms / max(self.trace_count, 1),
            "traces_per_second": self.trace_count / max(uptime_seconds, 1)
        } 