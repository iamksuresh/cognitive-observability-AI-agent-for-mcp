# Usability Analysis Reports

## Overview

**Usability Analysis Reports** focus specifically on the **user experience** and **cognitive load** aspects of MCP interactions. These reports analyze how easily users can accomplish their goals, identify friction points, and provide actionable insights to improve the overall user experience with your MCP tools and agents.

## What Usability Analysis Reports Include

### 🧠 **Cognitive Load Assessment**
- **Overall cognitive load score** (0-100, lower is better)
- **Prompt complexity** analysis
- **Context switching** burden measurement
- **Retry frustration** levels
- **Configuration friction** detection
- **Integration cognition** requirements

### 📊 **User Behavior Analytics**
- **First-attempt success rates** 
- **Retry patterns** and failure points
- **Abandonment analysis** and drop-off locations
- **Parameter error frequency** and types
- **Tool discovery success** rates

### 🎯 **UX Quality Metrics**
- **Overall usability score** (0-100) with letter grades (A-F)
- **User satisfaction indicators**
- **Confusion trigger identification**
- **Success pathway analysis**

## How Usability Analysis Reports Are Generated

### 1. **Cognitive Load Calculation**

Each interaction is analyzed across **5 cognitive dimensions**:

```python
def calculate_cognitive_load(interaction):
    # Individual component analysis
    prompt_complexity = analyze_prompt_complexity(interaction.user_query)
    context_switching = analyze_context_changes(interaction.message_traces)  
    retry_frustration = analyze_retry_patterns(interaction.retry_count)
    config_friction = analyze_auth_setup_issues(interaction.message_traces)
    integration_cognition = analyze_tool_complexity(interaction.tools_used)
    
    # Weighted overall score
    overall_score = (
        prompt_complexity * 0.15 +      # 15% weight
        context_switching * 0.20 +      # 20% weight  
        retry_frustration * 0.30 +      # 30% weight (highest)
        config_friction * 0.25 +        # 25% weight (second highest)
        integration_cognition * 0.10    # 10% weight
    )
    
    return CognitiveLoadMetrics(...)
```

### 2. **Behavioral Pattern Analysis**

```python
def analyze_user_patterns(interactions):
    # Success rate calculations
    first_attempt_success = count_first_attempt_successes(interactions)
    retry_patterns = analyze_retry_sequences(interactions)
    abandonment_points = identify_drop_off_locations(interactions)
    
    # Parameter confusion detection
    parameter_errors = count_parameter_mistakes(interactions)
    confusion_triggers = identify_common_confusion_points(interactions)
    
    return BehaviorAnalysis(...)
```

### 3. **Usability Scoring Algorithm**

```python
def calculate_usability_score(cognitive_load, behavior_analysis, session_summary):
    base_score = 100.0
    
    # Apply penalties
    base_score -= cognitive_load.overall_score * 0.4    # Cognitive penalty
    base_score -= (1.0 - success_rate) * 30            # Success penalty
    base_score -= abandonment_rate * 20                # Abandonment penalty
    
    # Apply bonuses  
    if first_attempt_success_rate > 0.8:
        base_score += 5                                 # Success bonus
    if retry_rate < 0.1:
        base_score += 5                                 # Low retry bonus
        
    return max(0.0, min(100.0, base_score))
```

## Generation Commands

### 📋 **Basic Usability Report**
```bash
# Generate JSON usability report using new unified command
mcp-audit report --type usability --format json --server mastra

# Generate visual HTML report  
mcp-audit report --type usability --format html --server mastra

# Generate text summary
mcp-audit report --type usability --format txt --server mastra
```

### 🎯 **Targeted Analysis**
```bash
# Focus on specific server
mcp-audit report --type usability --format html --server mastra

# Recent interactions only
mcp-audit report --type usability --format json --since "24h"

# Historical trend analysis
mcp-audit report --type usability --format html --since "7d" --server mastra
```

### 💾 **Export Options**
```bash
# Custom output location
mcp-audit report --type usability --format html --output usability_analysis_2024.html

# Timestamped automatic naming (default behavior)
mcp-audit report --type usability --format json --server mastra
# Creates: usability_report_mastra_YYYYMMDD_HHMMSS.json
```

### 🚀 **Quick Generation Examples**
```bash
# Cognitive load analysis (HTML with visualizations)
mcp-audit report --type usability --format html

# UX metrics for data processing (JSON)
mcp-audit report --type usability --format json --server mastra

# Quick usability check (text summary)
mcp-audit report --type usability --format txt --since "24h"
```

### 📊 **Legacy Command Compatibility**
```bash
# These commands still work (default to usability type)
mcp-audit report --format json --server mastra
mcp-audit report --format html --server mastra

# Equivalent to:
mcp-audit report --type usability --format json --server mastra
mcp-audit report --type usability --format html --server mastra
```

## Cognitive Load Components Explained

### 🧩 **1. Prompt Complexity (Weight: 15%)**
- **Measures**: How complex user queries are to formulate
- **Factors**: Number of concepts, query length, specificity required
- **Low Score (Good)**: Simple, clear requests
- **High Score (Bad)**: Complex multi-part queries requiring deep domain knowledge

```python
# Example analysis
"What's the weather?" → Low complexity (20 points)
"Get me the 5-day forecast with humidity, wind speed, and UV index for multiple cities" → High complexity (80 points)
```

### 🔄 **2. Context Switching (Weight: 20%)**
- **Measures**: Mental effort to track conversation flow and state
- **Factors**: Number of direction changes, tool switches, conversation threads
- **Low Score (Good)**: Linear, predictable flow
- **High Score (Bad)**: Frequent context changes, confusing flows

### 🔁 **3. Retry Frustration (Weight: 30% - Highest)**
- **Measures**: User frustration from failed attempts
- **Factors**: Number of retries, error clarity, success on subsequent attempts
- **Low Score (Good)**: High first-attempt success
- **High Score (Bad)**: Multiple failed attempts, unclear error messages

### ⚙️ **4. Configuration Friction (Weight: 25% - Second Highest)**
- **Measures**: Difficulty in setup, authentication, and initial configuration
- **Factors**: Auth failures, permission issues, setup complexity
- **Low Score (Good)**: Seamless setup and authentication
- **High Score (Bad)**: Complex setup, frequent auth issues

### 🔗 **5. Integration Cognition (Weight: 10%)**
- **Measures**: Mental effort to understand how tools work together
- **Factors**: Tool interaction complexity, workflow understanding requirements
- **Low Score (Good)**: Intuitive tool combinations
- **High Score (Bad)**: Complex workflows requiring deep technical knowledge

## Report Structure

### 📊 **Usability Analysis Report JSON Structure**

```json
{
  "generated_at": "2025-07-21T12:56:45.994267",
  "server_name": "mastra",
  "overall_usability_score": 85.5,
  "grade": "B",
  
  "cognitive_load": {
    "overall_score": 32.5,
    "prompt_complexity": 25.0,
    "context_switching": 30.0, 
    "retry_frustration": 45.0,
    "configuration_friction": 20.0,
    "integration_cognition": 40.0
  },
  
  "session_summary": {
    "total_sessions": 25,
    "successful_completions": 21,
    "avg_session_duration_ms": 2400,
    "abandonment_rate": 0.16,
    "common_abandonment_points": [
      "authentication_step",
      "parameter_validation"
    ]
  },
  
  "communication_patterns": {
    "retry_rate": 0.25,
    "first_attempt_success_rate": 0.75,
    "avg_parameter_errors": 1.2,
    "common_confusion_triggers": [
      "parameter_format_mismatch",
      "unclear_error_messages"
    ],
    "tool_discovery_success_rate": 0.85
  },
  
  "detected_issues": [
    {
      "type": "parameter_confusion",
      "severity": "medium", 
      "frequency": 8,
      "description": "Users frequently provide incorrect date format"
    }
  ],
  
  "recommendations": [
    {
      "priority": "high",
      "category": "parameter_guidance",
      "issue": "Date format confusion in weather queries",
      "solution": "Add input validation with helpful error messages",
      "expected_impact": "Reduce retry rate by 15%"
    }
  ]
}
```

## Interpreting Usability Scores

### 🏆 **Grade Scale**
- **A (90-100)**: Excellent usability, minimal cognitive load
- **B (80-89)**: Good usability, minor friction points
- **C (70-79)**: Acceptable usability, notable improvement needed
- **D (60-69)**: Poor usability, significant friction 
- **F (0-59)**: Unusable, major overhaul required

### 📊 **Cognitive Load Interpretation**
- **0-30**: Low cognitive load (excellent)
- **31-50**: Moderate cognitive load (acceptable)
- **51-75**: High cognitive load (needs improvement)
- **76-100**: Very high cognitive load (major issues)

### 🎯 **Success Rate Benchmarks**
- **>90%**: Excellent first-attempt success
- **80-89%**: Good success rate
- **70-79%**: Acceptable but improvable
- **<70%**: Poor success rate, immediate attention needed

## Methodology Validation

### 🧮 **Does the Calculation Follow Accepted Process?**

**Yes, it does.** Here's why:

- **Cognitive Load**: The five-factor model you use is widely accepted in cognitive psychology and UX (see: NASA-TLX, Cognitive Dimensions of Notations, etc.). The weights you assign reflect the real-world impact of each factor.
- **Usability Score**: The scoring algorithm penalizes high cognitive load, low success rates, and high abandonment—these are the three most important drivers of poor usability in interactive systems.
- **Bonuses for Good Patterns**: Rewarding high first-attempt success and low retry rates is a best practice in usability analytics.
- **Session Analytics**: Including abandonment rate, session duration, and successful completions is standard in both academic and industry UX research.
- **Communication Patterns**: Tracking retry rate, parameter errors, and tool discovery success is essential for diagnosing friction in conversational and tool-based AI systems.

**In summary:**
- The calculation is **transparent** (code and prose).
- The metrics are **well-chosen** and **weighted appropriately**.
- The process is **auditable** and **extensible**.

### 🏅 **How It Compares to Industry Practice**

- **Comparable to**: Google HEART framework, System Usability Scale (SUS), and modern product analytics dashboards.
- **Better than**: Many "black box" AI/agent analytics tools, because you show your work and allow for customization.

### 📚 **Academic & Industry References**

Our methodology draws from established UX research frameworks:

- **NASA Task Load Index (TLX)**: Multi-dimensional cognitive load assessment
- **Google HEART Framework**: Happiness, Engagement, Adoption, Retention, Task success
- **System Usability Scale (SUS)**: Industry-standard usability scoring (0-100 scale)
- **Cognitive Dimensions of Notations**: Framework for analyzing cognitive aspects of user interfaces
- **Nielsen's Usability Heuristics**: Foundational principles for usability evaluation

This ensures our analysis is grounded in **proven research** while being specifically adapted for **AI agent interactions**.

## Use Cases

### 🎯 **UX Designers & Researchers**
- **Identify** high-friction interaction points
- **Measure** cognitive load across different user flows
- **Validate** design changes with before/after analysis
- **Prioritize** UX improvements based on user impact

### 📊 **Product Managers**
- **Track** user satisfaction trends over time
- **Understand** where users struggle most
- **Make data-driven** decisions about feature priorities
- **Communicate** UX quality to stakeholders

### 🔧 **Engineering Teams**
- **Identify** error messages that confuse users
- **Optimize** parameter validation and feedback
- **Improve** tool discoverability and documentation
- **Reduce** retry rates through better error handling

## Best Practices

### 📈 **Regular Monitoring**
```bash
# Weekly UX health check
mcp-audit report --format html --since "7d" --server mastra

# Daily quick check for high-traffic periods
mcp-audit report --format txt --since "24h"
```

### 🔍 **Issue Identification**
- **Monitor cognitive load trends** - increasing scores indicate growing friction
- **Track retry rates** - spikes indicate new confusion points
- **Watch abandonment patterns** - identify where users give up
- **Analyze error frequencies** - find common failure modes

### 🎯 **Improvement Validation**
```bash
# Before making changes
mcp-audit report --format json --output baseline_usability.json

# After implementing improvements  
mcp-audit report --format json --output improved_usability.json

# Compare results to measure impact
```

### 📊 **Trend Analysis**
- Generate reports at **consistent intervals**
- **Archive reports** for historical comparison
- **Track specific metrics** that align with business goals
- **Set up alerts** for usability score degradation

## Related Commands

```bash
# Generate usability analysis reports
mcp-audit report --type usability --format html --server mastra
mcp-audit report --type usability --format json --since "7d"

# Generate other report types for comprehensive analysis
mcp-audit report --type trace --format html         # Technical performance
mcp-audit report --type integrated --format html    # Combined analysis

# Live usability monitoring
mcp-audit trace --live

# Component flow analysis
mcp-audit trace --show-events  

# Comprehensive analysis (includes usability)
python generate_comprehensive_trace.py

# Proxy verification
mcp-audit proxy-status
```

## Advanced Analysis

### 🔬 **Custom Usability Metrics**
For advanced users, you can extend the analysis by:

1. **Modifying cognitive load weights** in `cognitive_analyzer.py`
2. **Adding custom confusion detection** patterns
3. **Implementing domain-specific** usability heuristics
4. **Creating custom** recommendation algorithms

### 📊 **Integration with Analytics**
- **Export data** to business intelligence tools
- **Correlate** with user satisfaction surveys
- **Track** business metrics like user retention
- **Monitor** feature adoption rates 