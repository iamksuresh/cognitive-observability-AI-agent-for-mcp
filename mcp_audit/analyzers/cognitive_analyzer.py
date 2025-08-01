"""
Cognitive Load Analyzer.

Analyzes MCP interactions to calculate cognitive load metrics and detect usability issues.
"""

from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta
import re

from ..core.models import (
    MCPInteraction,
    CognitiveLoadMetrics,
    UsabilityIssue,
    UsabilityRecommendation,
    UsabilityIssueType,
    IssueSeverity,
    MCPMessageDirection
)

logger = logging.getLogger(__name__)


class CognitiveAnalyzer:
    """
    Analyzes MCP interactions to understand cognitive load and usability issues.
    
    Uses pattern recognition and heuristics to identify friction points
    that affect agent and user experience.
    """
    
    def __init__(self):
        """Initialize the cognitive analyzer."""
        self.baseline_latency_ms = 15000  # Expected baseline for smooth interactions (15 seconds)
        self.high_cognitive_threshold = 80.0
        self.medium_cognitive_threshold = 60.0
        
    async def analyze_interaction(self, interaction: MCPInteraction) -> CognitiveLoadMetrics:
        """
        Analyze a single MCP interaction for cognitive load.
        
        Args:
            interaction: The MCP interaction to analyze
            
        Returns:
            Cognitive load metrics for the interaction
        """
        try:
            # Calculate individual cognitive load components
            prompt_complexity = self._calculate_prompt_complexity(interaction)
            context_switching = self._calculate_context_switching(interaction)
            retry_frustration, retry_breakdown = self._calculate_retry_frustration(interaction)
            configuration_friction, config_breakdown = self._calculate_configuration_friction(interaction)
            integration_cognition = self._calculate_integration_cognition(interaction)
            
            # Calculate overall cognitive load score
            overall_score = self._calculate_overall_cognitive_load(
                prompt_complexity,
                context_switching,
                retry_frustration,
                configuration_friction,
                integration_cognition
            )
            
            return CognitiveLoadMetrics(
                overall_score=overall_score,
                prompt_complexity=prompt_complexity,
                context_switching=context_switching,
                retry_frustration=retry_frustration,
                configuration_friction=configuration_friction,
                integration_cognition=integration_cognition,
                retry_breakdown=retry_breakdown,
                configuration_breakdown=config_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error analyzing interaction cognitive load: {e}")
            # Return default metrics on error
            return CognitiveLoadMetrics(
                overall_score=50.0,
                prompt_complexity=50.0,
                context_switching=50.0,
                retry_frustration=50.0,
                configuration_friction=50.0,
                integration_cognition=50.0
            )
    
    def _calculate_prompt_complexity(self, interaction: MCPInteraction) -> float:
        """Calculate cognitive load from prompt complexity."""
        try:
            # Analyze the user query complexity
            query = interaction.user_query.lower()
            
            # Check if this is an inferred/placeholder prompt
            if ('[inferred]' in query or 
                'user request requiring' in query or
                'unknown' in query or
                len(query.strip()) < 3):
                # For inferred prompts, just return base complexity
                return 20.0
            
            # Base complexity score
            complexity_score = 20.0
            
            # Generic complexity analysis based on query characteristics
            words = query.split()
            word_count = len(words)
            
            # Add complexity for longer queries (cognitive load increases with length)
            if word_count > 10:
                complexity_score += 25  # Very long queries
            elif word_count > 5:
                complexity_score += 15  # Medium length queries
            elif word_count > 2:
                complexity_score += 5   # Short but multi-word queries
            
            # Add complexity for technical/domain-specific terms
            technical_indicators = [
                'api', 'config', 'authentication', 'parameter', 'endpoint', 'json', 'xml',
                'database', 'query', 'schema', 'token', 'oauth', 'webhook', 'integration',
                'middleware', 'proxy', 'cache', 'sync', 'async', 'batch', 'stream'
            ]
            technical_count = sum(1 for term in technical_indicators if term in query)
            complexity_score += technical_count * 8
            
            # Add complexity for conditional/complex logic terms
            complexity_indicators = [
                'if', 'when', 'unless', 'where', 'filter', 'sort', 'group', 'aggregate',
                'combine', 'merge', 'transform', 'convert', 'validate', 'parse'
            ]
            logic_count = sum(1 for term in complexity_indicators if term in query)
            complexity_score += logic_count * 10
            
            # Add complexity for multiple actions/verbs (indicates multi-step requests)
            action_verbs = [
                'create', 'update', 'delete', 'get', 'set', 'add', 'remove', 'modify',
                'send', 'receive', 'upload', 'download', 'import', 'export', 'backup',
                'restore', 'sync', 'copy', 'move', 'rename', 'list', 'search', 'find'
            ]
            action_count = sum(1 for verb in action_verbs if verb in query)
            if action_count > 2:
                complexity_score += (action_count - 1) * 12  # Penalty for multi-action requests
            
            # Add complexity for time-based queries (temporal reasoning is cognitively demanding)
            time_words = ['today', 'tomorrow', 'yesterday', 'week', 'month', 'year', 'hour', 'minute', 'day', 'now', 'later', 'before', 'after', 'since', 'until']
            if any(word in query for word in time_words):
                complexity_score += 15
            
            # Add complexity for numerical/quantitative references
            if re.search(r'\d+', query) or any(word in query for word in ['all', 'every', 'each', 'most', 'some', 'many', 'few']):
                complexity_score += 10
            
            return min(complexity_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating prompt complexity: {e}")
            return 50.0
    
    def _calculate_context_switching(self, interaction: MCPInteraction) -> float:
        """Calculate cognitive load from context switching."""
        try:
            if len(interaction.message_traces) < 2:
                return 20.0
            
            switching_score = 0.0
            
            # Count direction changes in message flow (original logic)
            direction_changes = 0
            last_direction = None
            
            for message in interaction.message_traces:
                if last_direction and message.direction != last_direction:
                    direction_changes += 1
                last_direction = message.direction
            
            # Add cognitive load for direction changes
            switching_score += direction_changes * 10
            
            # NEW: Count tool/method transitions (more important for cognitive load)
            tool_changes = 0
            last_method = None
            
            for message in interaction.message_traces:
                if isinstance(message.payload, dict):
                    current_method = message.payload.get('method')
                    if current_method and last_method and current_method != last_method:
                        tool_changes += 1
                    if current_method:
                        last_method = current_method
            
            # Tool transitions are more cognitively demanding than direction changes
            switching_score += tool_changes * 15
            
            # Base minimum score for any multi-message interaction
            if switching_score == 0 and len(interaction.message_traces) > 1:
                switching_score = 5.0
            
            return min(switching_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating context switching: {e}")
            return 50.0
    
    def _calculate_retry_frustration(self, interaction: MCPInteraction) -> tuple[float, dict]:
        """Calculate cognitive load from retry attempts and failures."""
        try:
            # Base frustration is low
            frustration_score = 10.0
            breakdown = {
                'base_score': 10.0,
                'retry_penalty': 0,
                'retry_count': interaction.retry_count,
                'failure_penalty': 0,
                'failed_interaction': not interaction.success,
                'error_penalty': 0,
                'actual_error_count': 0,
                'latency_penalty': 0,
                'latency_ms': interaction.total_latency_ms,
                'latency_threshold_ms': self.baseline_latency_ms * 2,
                'explanations': []
            }
            
            # Add frustration for retry attempts
            if interaction.retry_count and interaction.retry_count > 0:
                retry_penalty = interaction.retry_count * 25
                frustration_score += retry_penalty
                breakdown['retry_penalty'] = retry_penalty
                breakdown['explanations'].append(f"Retry attempts detected: {interaction.retry_count} retries × 25 points each")
            
            # Add frustration for failures - only if the overall interaction failed
            if not interaction.success:
                failure_penalty = 40
                frustration_score += failure_penalty
                breakdown['failure_penalty'] = failure_penalty
                breakdown['explanations'].append("Interaction failed to complete successfully")
            
            # Add frustration for error messages - only count actual errors (error codes that indicate failure)
            actual_error_count = 0
            for message in interaction.message_traces:
                # Only count as errors if there's an error_code AND it indicates a real failure
                if message.error_code and (
                    message.error_code.startswith('4') or  # 4xx client errors
                    message.error_code.startswith('5') or  # 5xx server errors
                    message.error_code in ['timeout', 'connection_error', 'parse_error']
                ):
                    actual_error_count += 1
            
            error_penalty = actual_error_count * 20
            frustration_score += error_penalty
            breakdown['error_penalty'] = error_penalty
            breakdown['actual_error_count'] = actual_error_count
            if actual_error_count > 0:
                breakdown['explanations'].append(f"Error messages detected: {actual_error_count} actual errors × 20 points each")
            
            # Add frustration for long latencies - but be more forgiving for successful operations
            if (interaction.total_latency_ms is not None and 
                interaction.total_latency_ms > 0 and  # Ensure it's not just a default/hardcoded 0
                interaction.total_latency_ms > self.baseline_latency_ms * 2):
                # Reduce penalty for successful operations (users are more tolerant of slow success than failure)
                latency_penalty = 15 if interaction.success else 30
                frustration_score += latency_penalty
                breakdown['latency_penalty'] = latency_penalty
                threshold_seconds = (self.baseline_latency_ms * 2) / 1000
                actual_seconds = interaction.total_latency_ms / 1000
                breakdown['explanations'].append(f"Slow response time: {actual_seconds:.1f}s exceeds {threshold_seconds:.0f}s threshold (reduced penalty due to success)")
            
            final_score = min(frustration_score, 100.0)
            return final_score, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating retry frustration: {e}")
            return 50.0, {'explanations': ['Error during calculation']}
    
    def _calculate_configuration_friction(self, interaction: MCPInteraction) -> tuple[float, dict]:
        """Calculate cognitive load from configuration and authentication issues."""
        try:
            friction_score = 10.0
            breakdown = {
                'base_score': 10.0,
                'auth_penalty': 0,
                'param_penalty': 0,
                'config_keyword_penalty': 0,
                'latency_penalty': 0,
                'latency_ms': interaction.total_latency_ms,
                'latency_threshold_ms': self.baseline_latency_ms * 3,
                'explanations': []
            }
            
            # Check for authentication-related errors
            auth_errors = 0
            param_errors = 0
            for message in interaction.message_traces:
                if message.error_code in ['401', '403']:
                    auth_errors += 1
                    friction_score += 50  # High friction for auth issues
                    breakdown['auth_penalty'] += 50
                elif message.error_code in ['400', '422']:
                    param_errors += 1
                    friction_score += 30  # Medium friction for parameter issues
                    breakdown['param_penalty'] += 30
            
            if auth_errors > 0:
                breakdown['explanations'].append(f"Authentication errors: {auth_errors} auth failures (401/403) × 50 points each")
            if param_errors > 0:
                breakdown['explanations'].append(f"Parameter validation errors: {param_errors} validation failures (400/422) × 30 points each")
            
            # Only check for configuration-related keywords in ERROR messages, not successful ones
            config_keyword_count = 0
            for message in interaction.message_traces:
                # Only analyze configuration keywords if there's actually an error
                if message.error_code and isinstance(message.payload, dict):
                    payload_str = str(message.payload).lower()
                    if any(word in payload_str for word in ['api key', 'token', 'auth', 'config']):
                        config_keyword_count += 1
                        friction_score += 35
                        breakdown['config_keyword_penalty'] += 35
            
            if config_keyword_count > 0:
                breakdown['explanations'].append(f"Configuration keywords in errors: {config_keyword_count} errors with config-related terms × 35 points each")
            
            # High latency can indicate configuration issues - but be more forgiving for successful operations
            if interaction.total_latency_ms is not None and interaction.total_latency_ms > self.baseline_latency_ms * 3:
                # Reduce penalty for successful operations (slow success is better than fast failure)
                latency_penalty = 10 if interaction.success else 25
                friction_score += latency_penalty
                breakdown['latency_penalty'] = latency_penalty
                threshold_seconds = (self.baseline_latency_ms * 3) / 1000
                actual_seconds = interaction.total_latency_ms / 1000
                penalty_type = "reduced penalty due to success" if interaction.success else "full penalty due to failure"
                breakdown['explanations'].append(f"Slow response time: {actual_seconds:.1f}s exceeds {threshold_seconds:.0f}s threshold ({penalty_type})")
            
            final_score = min(friction_score, 100.0)
            return final_score, breakdown
            
        except Exception as e:
            logger.error(f"Error calculating configuration friction: {e}")
            return 50.0, {'explanations': ['Error during calculation']}
    
    def _calculate_integration_cognition(self, interaction: MCPInteraction) -> float:
        """Calculate cognitive load from integration complexity."""
        try:
            integration_score = 20.0
            
            # Count different protocol types used
            protocols = set(message.protocol for message in interaction.message_traces)
            if len(protocols) > 1:
                integration_score += 20
            
            # Count different message directions
            directions = set(message.direction for message in interaction.message_traces)
            integration_score += len(directions) * 10
            
            # Complex parameter structures add cognitive load
            for message in interaction.message_traces:
                if isinstance(message.payload, dict):
                    payload_depth = self._calculate_dict_depth(message.payload)
                    if payload_depth > 3:
                        integration_score += 15
            
            return min(integration_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating integration cognition: {e}")
            return 50.0
    
    def _calculate_dict_depth(self, d: Dict[str, Any], current_depth: int = 0) -> int:
        """Calculate the depth of nested dictionaries."""
        if not isinstance(d, dict):
            return current_depth
        
        max_depth = current_depth
        for value in d.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_overall_cognitive_load(
        self,
        prompt_complexity: float,
        context_switching: float,
        retry_frustration: float,
        configuration_friction: float,
        integration_cognition: float
    ) -> float:
        """Calculate overall cognitive load from individual components."""
        # Weighted average of cognitive load components
        weights = {
            'prompt_complexity': 0.15,
            'context_switching': 0.20,
            'retry_frustration': 0.30,  # High weight - retries are very frustrating
            'configuration_friction': 0.25,  # High weight - config issues are major blockers
            'integration_cognition': 0.10
        }
        
        overall_score = (
            prompt_complexity * weights['prompt_complexity'] +
            context_switching * weights['context_switching'] +
            retry_frustration * weights['retry_frustration'] +
            configuration_friction * weights['configuration_friction'] +
            integration_cognition * weights['integration_cognition']
        )
        
        return min(overall_score, 100.0)
    
    async def detect_usability_issues(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """
        Detect usability issues from a set of interactions.
        
        Args:
            interactions: List of MCP interactions to analyze
            
        Returns:
            List of detected usability issues
        """
        issues = []
        
        try:
            # Authentication friction detection
            auth_issues = self._detect_authentication_issues(interactions)
            issues.extend(auth_issues)
            
            # Parameter confusion detection
            param_issues = self._detect_parameter_issues(interactions)
            issues.extend(param_issues)
            
            # Error recovery detection
            recovery_issues = self._detect_error_recovery_issues(interactions)
            issues.extend(recovery_issues)
            
            # Cognitive overload detection
            overload_issues = await self._detect_cognitive_overload(interactions)
            issues.extend(overload_issues)
            
            # Tool discovery issues
            discovery_issues = self._detect_tool_discovery_issues(interactions)
            issues.extend(discovery_issues)
            
        except Exception as e:
            logger.error(f"Error detecting usability issues: {e}")
        
        return issues
    
    def _detect_authentication_issues(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """Detect authentication-related usability issues."""
        issues = []
        
        auth_failures = 0
        total_interactions = len(interactions)
        
        for interaction in interactions:
            for message in interaction.message_traces:
                if message.error_code in ['401', '403']:
                    auth_failures += 1
                    break
        
        if auth_failures > 0:
            failure_rate = auth_failures / total_interactions
            
            if failure_rate > 0.5:
                severity = IssueSeverity.CRITICAL
                description = f"High authentication failure rate ({failure_rate:.1%})"
                suggested_fix = "Implement guided API key setup with validation"
            elif failure_rate > 0.2:
                severity = IssueSeverity.HIGH
                description = f"Moderate authentication failures ({failure_rate:.1%})"
                suggested_fix = "Add clear API key configuration instructions"
            else:
                severity = IssueSeverity.MEDIUM
                description = f"Some authentication failures detected ({failure_rate:.1%})"
                suggested_fix = "Improve error messages for authentication failures"
            
            issues.append(UsabilityIssue(
                type=UsabilityIssueType.AUTHENTICATION_FRICTION,
                severity=severity,
                description=description,
                frequency=auth_failures,
                impact_description="Users cannot access core functionality",
                suggested_fix=suggested_fix,
                estimated_improvement=30.0 if severity == IssueSeverity.CRITICAL else 20.0
            ))
        
        return issues
    
    def _detect_parameter_issues(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """Detect parameter-related confusion."""
        issues = []
        
        param_errors = 0
        total_interactions = len(interactions)
        
        for interaction in interactions:
            for message in interaction.message_traces:
                if message.error_code in ['400', '422']:
                    param_errors += 1
                    break
        
        if param_errors > 0:
            error_rate = param_errors / total_interactions
            
            if error_rate > 0.3:
                issues.append(UsabilityIssue(
                    type=UsabilityIssueType.PARAMETER_CONFUSION,
                    severity=IssueSeverity.HIGH,
                    description=f"High parameter error rate ({error_rate:.1%})",
                    frequency=param_errors,
                    impact_description="Users struggle with correct parameter format",
                    suggested_fix="Add parameter validation and examples",
                    estimated_improvement=25.0
                ))
        
        return issues
    
    def _detect_error_recovery_issues(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """Detect error recovery problems."""
        issues = []
        
        high_retry_interactions = 0
        for interaction in interactions:
            if interaction.retry_count and interaction.retry_count > 2:
                high_retry_interactions += 1
        
        if high_retry_interactions > 0:
            issues.append(UsabilityIssue(
                type=UsabilityIssueType.ERROR_RECOVERY_ISSUES,
                severity=IssueSeverity.MEDIUM,
                description=f"{high_retry_interactions} interactions required excessive retries",
                frequency=high_retry_interactions,
                impact_description="Users get stuck in retry loops",
                suggested_fix="Improve error messages and recovery guidance",
                estimated_improvement=15.0
            ))
        
        return issues
    
    async def _detect_cognitive_overload(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """Detect cognitive overload patterns."""
        issues = []
        
        high_cognitive_load_count = 0
        for interaction in interactions:
            # Calculate cognitive load for this interaction
            cognitive_load = await self.analyze_interaction(interaction)
            if cognitive_load.overall_score > self.high_cognitive_threshold:
                high_cognitive_load_count += 1
        
        if high_cognitive_load_count > len(interactions) * 0.4:  # More than 40% have high cognitive load
            issues.append(UsabilityIssue(
                type=UsabilityIssueType.COGNITIVE_OVERLOAD,
                severity=IssueSeverity.HIGH,
                description="High cognitive load detected in multiple interactions",
                frequency=high_cognitive_load_count,
                impact_description="Users experience mental fatigue and confusion",
                suggested_fix="Simplify interaction patterns and reduce complexity",
                estimated_improvement=35.0
            ))
        
        return issues
    
    def _detect_tool_discovery_issues(self, interactions: List[MCPInteraction]) -> List[UsabilityIssue]:
        """Detect tool discovery problems."""
        issues = []
        
        # Look for patterns indicating tool discovery confusion
        tool_list_calls = 0
        successful_tool_calls = 0
        
        for interaction in interactions:
            has_tool_list = False
            has_successful_call = False
            
            for message in interaction.message_traces:
                if isinstance(message.payload, dict):
                    method = message.payload.get('method', '')
                    if method == 'tools/list':
                        has_tool_list = True
                    elif method == 'tools/call' and not message.error_code:
                        has_successful_call = True
            
            if has_tool_list:
                tool_list_calls += 1
            if has_successful_call:
                successful_tool_calls += 1
        
        if tool_list_calls > 0 and successful_tool_calls / max(tool_list_calls, 1) < 0.5:
            issues.append(UsabilityIssue(
                type=UsabilityIssueType.TOOL_DISCOVERY_PROBLEMS,
                severity=IssueSeverity.MEDIUM,
                description="Low success rate after tool discovery",
                frequency=tool_list_calls - successful_tool_calls,
                impact_description="Users can't effectively use discovered tools",
                suggested_fix="Improve tool documentation and examples",
                estimated_improvement=20.0
            ))
        
        return issues
    
    async def generate_recommendations(
        self, 
        issues: List[UsabilityIssue],
        cognitive_load: CognitiveLoadMetrics
    ) -> List[UsabilityRecommendation]:
        """
        Generate actionable recommendations based on detected issues.
        
        Args:
            issues: List of detected usability issues
            cognitive_load: Overall cognitive load metrics
            
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        try:
            # Generate recommendations for each issue
            for issue in issues:
                recommendation = await self._create_recommendation_for_issue(issue)
                recommendations.append(recommendation)
            
            # Add general cognitive load recommendations
            if cognitive_load.overall_score > self.high_cognitive_threshold:
                cognitive_rec = self._create_cognitive_load_recommendation(cognitive_load)
                recommendations.append(cognitive_rec)
            
            # Sort by priority and impact
            recommendations.sort(key=lambda r: (
                self._priority_weight(r.priority),
                -r.estimated_improvement
            ))
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    async def _create_recommendation_for_issue(self, issue: UsabilityIssue) -> UsabilityRecommendation:
        """Create a recommendation for a specific usability issue."""
        implementation_steps = []
        
        if issue.type == UsabilityIssueType.AUTHENTICATION_FRICTION:
            implementation_steps = [
                "Add API key validation on setup",
                "Provide clear error messages for auth failures",
                "Create guided setup wizard",
                "Add test connectivity feature"
            ]
        elif issue.type == UsabilityIssueType.PARAMETER_CONFUSION:
            implementation_steps = [
                "Add parameter validation with clear error messages",
                "Provide usage examples in documentation",
                "Implement auto-completion for parameters",
                "Add parameter format hints"
            ]
        elif issue.type == UsabilityIssueType.ERROR_RECOVERY_ISSUES:
            implementation_steps = [
                "Improve error message clarity",
                "Add suggested recovery actions",
                "Implement progressive error disclosure",
                "Add contextual help for common errors"
            ]
        
        return UsabilityRecommendation(
            priority=issue.severity,
            category=issue.type.value.replace('_', ' ').title(),
            issue=issue.description,
            impact=issue.impact_description,
            effort="medium",  # Default effort level
            recommendation=issue.suggested_fix,
            estimated_improvement=issue.estimated_improvement or 15.0,
            implementation_steps=implementation_steps
        )
    
    def _create_cognitive_load_recommendation(self, cognitive_load: CognitiveLoadMetrics) -> UsabilityRecommendation:
        """Create a recommendation for high cognitive load."""
        return UsabilityRecommendation(
            priority=IssueSeverity.HIGH,
            category="Cognitive Load",
            issue=f"Overall cognitive load is high ({cognitive_load.overall_score:.1f})",
            impact="Users experience mental fatigue and reduced efficiency",
            effort="high",
            recommendation="Redesign interaction flow to reduce cognitive burden",
            estimated_improvement=30.0,
            implementation_steps=[
                "Analyze high-friction interaction patterns",
                "Simplify parameter structures",
                "Reduce context switching requirements",
                "Implement progressive disclosure",
                "Add smart defaults for common use cases"
            ]
        )
    
    def _priority_weight(self, priority: IssueSeverity) -> int:
        """Get numeric weight for priority sorting."""
        weights = {
            IssueSeverity.CRITICAL: 4,
            IssueSeverity.HIGH: 3,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.LOW: 1
        }
        return weights.get(priority, 1) 