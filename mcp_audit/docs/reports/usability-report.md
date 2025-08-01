# Usability Report

## Report Type
**Timeline-Based Cognitive Load Assessment with LLM Reasoning Analysis**

The usability report provides human-centered analysis of MCP tool interactions using timeline-based flow tracking. It focuses on cognitive load assessment, LLM reasoning quality, and user experience metrics with actionable recommendations for improving tool usability.

## Command
```bash
mcp-audit report --type usability
```

## CLI Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--since` | Time window for analysis | `24h` | `--since 4h`, `--since 1d`, `--since 1w` |
| `--server` | Specific MCP server to analyze | All servers | `--server mastra` |
| `--output` | Output file path | Auto-generated | `--output ux_analysis.json` |
| `--format` | Report format | `json` | `--format json` |
| `--grade-only` | Show only overall grade | `false` | `--grade-only` |

### Example Commands
```bash
# Generate usability report for last 4 hours
mcp-audit report --type usability --since 4h

# Quick UX grade for specific server
mcp-audit report --type usability --server mastra --grade-only

# Weekly usability analysis
mcp-audit report --type usability --since 1w --output weekly_ux.json
```

## When to Use This Report

### Primary Use Cases
- **📊 UX Performance Monitoring**: Regular assessment of tool usability and user satisfaction
- **🧠 Cognitive Load Analysis**: Understanding mental effort required to use MCP tools
- **🤖 LLM Reasoning Quality**: Evaluating AI agent decision-making effectiveness
- **📈 Flow Success Tracking**: Monitoring complete interaction sequences and outcomes
- **🔍 Timeline-Based Analysis**: Understanding user behavior patterns over time
- **🎯 User Experience Optimization**: Identifying pain points and improvement opportunities

### Best For
- **Product Managers**: Tracking UX KPIs and user satisfaction metrics
- **UX Designers**: Understanding user interaction patterns and pain points
- **Product Teams**: Making data-driven decisions about tool improvements
- **Customer Success**: Identifying training needs and support requirements
- **Engineering Teams**: Prioritizing usability improvements in development

### Ideal Scenarios
- Evaluating the success of new tool deployments
- Identifying why users abandon certain workflows
- Comparing usability across different MCP servers
- Preparing usability improvement roadmaps
- Understanding cognitive barriers to tool adoption
- Measuring impact of UX improvements

## Detailed Report Explanation

### Core Components

#### 1. **Overall Usability Score & Grade**
```json
{
  "overall_usability_score": 100,
  "grade": "A",
  "cognitive_grade": "A",
  "composite_score": 100,
  "server_name": "mastra"
}
```

**Cognitive Load Based Grading Scale:**
- **A (0-20)**: Excellent UX, minimal cognitive friction
- **B (21-40)**: Good UX, minor cognitive improvements needed  
- **C (41-60)**: Acceptable UX, moderate cognitive load
- **D (61-80)**: Poor UX, high cognitive load
- **F (81-100)**: Critical UX Issues, extreme cognitive friction

#### 2. **Report Summary & Flow Analysis**
```json
{
  "summary": {
    "total_flows": 10,
    "flows_with_user_context": 10,
    "user_context_rate": 1.0,
    "flows_with_llm_reasoning": 10,
    "llm_reasoning_rate": 1.0,
    "cross_server_flows": 0,
    "successful_flows": 10,
    "success_rate": 1.0,
    "servers_involved": ["mastra"],
    "total_tool_calls": 3,
    "total_llm_decisions": 28
  }
}
```

**Flow Metrics:**
- **total_flows**: Complete interaction sequences analyzed
- **flows_with_user_context**: Flows with clear user intent
- **user_context_rate**: Percentage of flows with identifiable user goals
- **flows_with_llm_reasoning**: Flows where LLM decision-making was captured
- **llm_reasoning_rate**: Quality of AI agent reasoning patterns
- **cross_server_flows**: Multi-server interaction sequences

#### 3. **Usability Metrics**
```json
{
  "usability_metrics": {
    "user_interactions": 10,
    "successful_completions": 10,
    "abandonment_rate": 0,
    "avg_flow_duration_sec": 15.8,
    "tool_usage_success_rate": 100,
    "llm_reasoning_quality": 100
  }
}
```

**Core Usability Indicators:**
- **user_interactions**: Total user-initiated sequences
- **successful_completions**: Flows that achieved user objectives
- **avg_flow_duration_sec**: Time from initiation to completion
- **tool_usage_success_rate**: Effectiveness of tool utilization
- **llm_reasoning_quality**: AI agent decision-making quality

#### 4. **Cognitive Load Analysis**
```json
{
  "cognitive_load": {
    "overall_score": 16.3,
    "prompt_complexity": 20.0,
    "context_switching": 19.5,
    "retry_frustration": 13.0,
    "configuration_friction": 10.0,
    "integration_cognition": 30.0,
    "retry_breakdown": {
      "base_score": 10.0,
      "retry_penalty": 0,
      "retry_count": 0,
      "failure_penalty": 0,
      "failed_interaction": false,
      "error_penalty": 0,
      "actual_error_count": 0,
      "latency_penalty": 0,
      "latency_ms": 23510,
      "latency_threshold_ms": 30000,
      "explanations": []
    },
    "configuration_breakdown": {
      "base_score": 10.0,
      "auth_penalty": 0,
      "param_penalty": 0,
      "config_keyword_penalty": 0,
      "latency_penalty": 0,
      "latency_ms": 23510,
      "latency_threshold_ms": 45000,
      "explanations": []
    },
    "grade": "A",
    "friction_points": [
      "No significant friction points detected"
    ]
  }
}
```

**Cognitive Load Factors:**
- **prompt_complexity**: Mental effort required to formulate requests
- **context_switching**: Cognitive overhead of switching between tools
- **retry_frustration**: Stress from failed attempts and retries (with detailed breakdown)
- **configuration_friction**: Setup and parameter complexity (with detailed breakdown)
- **integration_cognition**: Understanding tool relationships

**Advanced Breakdowns:**
- **retry_breakdown**: Detailed analysis of retry patterns, failures, and latency impacts
- **configuration_breakdown**: Authentication, parameter, and setup friction analysis
- **friction_points**: Specific areas where users experience cognitive strain

**Score Interpretation:**
- **0-20**: Low cognitive load (excellent UX)
- **21-40**: Moderate cognitive load (good UX)
- **41-60**: High cognitive load (needs improvement)
- **61-80**: Very high cognitive load (poor UX)
- **81-100**: Extreme cognitive load (critical UX issues)

#### 5. **Usability Insights & Grade Calculation**
```json
{
  "usability_insights": [
    "Good response time - 15.8s average provides smooth experience",
    "Perfect reliability - all interactions completed successfully",
    "Perfect LLM integration - tool selection working flawlessly",
    "Outstanding cognitive experience - users can focus on their goals"
  ],
  "grade_calculation": {
    "method": "cognitive_load_based",
    "formula": "weighted_average_of_5_factors",
    "weights": {
      "prompt_complexity": 0.15,
      "context_switching": 0.2,
      "retry_frustration": 0.3,
      "configuration_friction": 0.25,
      "integration_cognition": 0.1
    },
    "thresholds": {
      "A": "0-20 (Excellent UX)",
      "B": "21-40 (Good UX)",
      "C": "41-60 (Acceptable UX)",
      "D": "61-80 (Poor UX)",
      "F": "81-100 (Critical UX Issues)"
    },
    "current_score": 16.3,
    "explanation": "Score 16.3 = (prompt:20.0×0.15) + (context:19.5×0.20) + (retry:13.0×0.30) + (config:10.0×0.25) + (integration:30.0×0.10)"
  }
}
```

**Grading Methodology:**
- **method**: Primary algorithm used for scoring (cognitive_load_based)
- **formula**: Mathematical approach to combining factors
- **weights**: Importance assigned to each cognitive load factor
- **current_score**: Final calculated cognitive load score
- **explanation**: Step-by-step calculation breakdown

#### 6. **Meta Information & Scoring Configuration**
```json
{
  "meta": {
    "scoring_algorithm": "cognitive_load_based_primary",
    "cognitive_load_weight": 1.0,
    "tool_success_weight": 0.7,
    "llm_reasoning_weight": 0.3,
    "scale": "0-100",
    "primary_grading": "cognitive_load_analysis",
    "cognitive_thresholds": {
      "A": "0-20 (Excellent UX)",
      "B": "21-40 (Good UX)",
      "C": "41-60 (Acceptable UX)",
      "D": "61-80 (Poor UX)",
      "F": "81-100 (Critical UX Issues)"
    },
    "event_grouping_window_sec": 30,
    "description": "Events within this window are grouped as related interactions"
  }
}
```

**Scoring Configuration:**
- **scoring_algorithm**: Primary methodology for usability assessment
- **cognitive_load_weight**: Emphasis on cognitive friction analysis
- **tool_success_weight**: Importance of tool execution success
- **llm_reasoning_weight**: Weight given to AI agent decision quality
- **event_grouping_window_sec**: Time window for grouping related interactions

### Advanced Analytics

#### **User Behavior Patterns**
```json
{
  "behavioral_insights": {
    "exploration_patterns": "Sequential tool discovery",
    "retry_behaviors": "Low retry frequency indicates good success rates",
    "abandonment_triggers": "No common abandonment patterns detected",
    "efficiency_indicators": "High first-attempt success"
  }
}
```

#### **Usability Trends**
```json
{
  "trends": {
    "success_rate_trend": "stable_high",
    "cognitive_load_trend": "decreasing",
    "user_confidence_trend": "increasing",
    "tool_adoption_trend": "positive"
  }
}
```

#### **Comparative Analysis**
When multiple servers are analyzed:
```json
{
  "server_comparison": {
    "best_performing": "mastra",
    "usability_ranking": ["mastra", "server2", "server3"],
    "improvement_priorities": {
      "server2": ["response_time", "error_clarity"],
      "server3": ["tool_discovery", "documentation"]
    }
  }
}
```

### Actionable Recommendations

#### **High-Impact Improvements**
```json
{
  "recommendations": [
    {
      "category": "tool_documentation",
      "priority": "high",
      "description": "Add interactive examples for complex tools",
      "expected_impact": "20% improvement in first-attempt success",
      "implementation_effort": "medium"
    },
    {
      "category": "error_messaging", 
      "priority": "medium",
      "description": "Provide clearer parameter validation errors",
      "expected_impact": "15% reduction in retry rate",
      "implementation_effort": "low"
    }
  ]
}
```

#### **Quick Wins**
- Parameter validation improvements
- Error message clarity
- Tool description enhancements
- Example additions

#### **Long-term Initiatives**
- Workflow simplification
- Advanced tool discovery
- Personalized recommendations
- Proactive assistance

### Performance Correlation

#### **Technical vs. Usability Metrics**
```json
{
  "performance_correlation": {
    "response_time_impact": "Minimal (under 100ms)",
    "error_rate_impact": "High (each error reduces satisfaction 25%)",
    "availability_impact": "Critical (downtime severely affects trust)"
  }
}
```

## Sample Generated Reports

### File Location
```
/<FOLDER_PATH>/usability_report_20250730_201716.json
```

### Key Sections in Sample Report

1. **Overall Score**: 100/100 (Grade A)
2. **Flow Analysis**: 10 flows, 100% success rate with full LLM reasoning capture
3. **Cognitive Load**: 16.3/100 (excellent - minimal cognitive friction)
4. **Usability Metrics**: Perfect completion rates, 15.8s average flow duration
5. **Grade Calculation**: Transparent weighted scoring methodology
6. **Meta Configuration**: Detailed scoring algorithm parameters

### Sample Usability Profile
```json
{
  "server": "mastra",
  "report_type": "timeline_based_with_llm_reasoning",
  "grade": "A",
  "key_strengths": [
    "Good response times (15.8s average)",
    "Perfect reliability (100% completion)",
    "Perfect LLM integration",
    "Outstanding cognitive experience (16.3/100 load)"
  ],
  "improvement_areas": [
    "No significant friction points detected"
  ],
  "cognitive_focus": "Primary scoring based on cognitive load analysis"
}
```

### Report Size & Depth
- **116 lines** of comprehensive usability analysis
- **Timeline-based flow tracking** with LLM reasoning capture
- **Detailed cognitive load breakdowns** with penalty analysis
- **Transparent scoring methodology** with weighted calculations
- **Meta-configuration insights** for reproducible analysis

### Common Usability Patterns

#### **High-Performing Tools (Grade A)**
- Fast response times (< 100ms)
- Clear tool descriptions
- Intuitive parameter structures
- Excellent error handling
- High first-attempt success rates

#### **Problem Tools (Grade C-F)**
- Slow response times (> 1000ms)
- Confusing tool names/descriptions
- Complex parameter requirements
- Poor error messages
- High abandonment rates

#### **Improvement Opportunities**
- Tool discovery enhancement
- Parameter simplification
- Error message clarity
- Documentation improvements
- Workflow streamlining

This usability report provides human-centered insights that complement technical metrics, enabling teams to create more user-friendly and cognitively accessible MCP tool experiences. 