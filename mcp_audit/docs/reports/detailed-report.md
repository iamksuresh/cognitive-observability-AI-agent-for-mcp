# Detailed Report

## Report Type
**Timeline-Based Flow Analysis with LLM Reasoning Capture**

The detailed report provides comprehensive end-to-end observability of the complete USER → LLM → MCP workflow using timeline-based analysis with automatic LLM decision tracking and timestamp proximity grouping.

## Command
```bash
mcp-audit report --type detailed
```

## CLI Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--since` | Time window for analysis | `24h` | `--since 2h`, `--since 30m`, `--since 1d` |
| `--server` | Specific MCP server to analyze | All servers | `--server mastra` |
| `--output` | Output file path | Auto-generated | `--output my_report.json` |
| `--format` | Report format | `json` | `--format json` |

### Example Commands
```bash
# Generate detailed report for last 2 hours
mcp-audit report --type detailed --since 2h

# Analyze specific server for last 30 minutes  
mcp-audit report --type detailed --server mastra --since 30m

# Save to custom location
mcp-audit report --type detailed --output /path/to/detailed_analysis.json
```

## When to Use This Report

### Primary Use Cases
- **🔍 Timeline-Based Flow Analysis**: Understanding complete interaction sequences with precise timing
- **🧠 LLM Reasoning Investigation**: Analyzing AI decision-making process, tool selection, and confidence levels
- **⏱️ Timestamp Proximity Grouping**: Correlating related events within configurable time windows
- **📊 Multi-Tool Flow Optimization**: Identifying bottlenecks in sequential tool executions
- **🔗 Cross-Server Flow Detection**: Tracking interactions spanning multiple MCP servers
- **🐛 Complex Debugging**: Investigating multi-step workflow issues with detailed timelines

### Best For
- **Product Managers**: Understanding user behavior and tool adoption patterns
- **AI Engineers**: Optimizing LLM decision-making and tool selection
- **UX Researchers**: Analyzing complete user interaction flows
- **DevOps Teams**: Performance monitoring and optimization
- **Integration Teams**: Understanding how users interact with MCP tools

### Ideal Scenarios
- Investigating why specific tools aren't being used effectively
- Understanding user intent → LLM reasoning → tool execution patterns
- Optimizing the complete AI agent workflow
- Correlating user satisfaction with technical performance
- Debugging complex multi-tool interactions

## Detailed Report Explanation

### Core Components

#### 1. **Report Metadata & Summary**
```json
{
  "generated_at": "2025-07-30T08:52:18.418322",
  "report_type": "timeline_based_with_llm_reasoning",
  "analysis_method": "timestamp_proximity_grouping_with_llm_decisions",
  "time_window_seconds": 30,
  "summary": {
    "total_flows": 2,
    "flows_with_user_context": 2,
    "user_context_rate": 1.0,
    "flows_with_llm_reasoning": 2,
    "llm_reasoning_rate": 1.0,
    "cross_server_flows": 0,
    "successful_flows": 2,
    "success_rate": 1.0,
    "servers_involved": ["mastra"],
    "total_tool_calls": 2,
    "total_llm_decisions": 3
  }
}
```

**Analysis Method Explained:**
- **timestamp_proximity_grouping_with_llm_decisions**: Groups events within configurable time windows and correlates with LLM reasoning
- **time_window_seconds**: Configurable window for grouping related events (default: 30 seconds)
- **flows_with_llm_reasoning**: Percentage of flows with captured AI decision-making
- **cross_server_flows**: Detection of interactions spanning multiple MCP servers

#### 2. **Interaction Flows**
Each flow contains comprehensive timeline and LLM reasoning data:

```json
{
  "flow_id": "flow_1753836487",
  "start_time": "2025-07-30T08:48:07.966674",
  "end_time": "2025-07-30T08:48:31.476958",
  "duration_ms": 23510.284,
  "event_count": 6,
  "servers_involved": ["mastra"],
  "cross_server_flow": false,
  "has_user_context": true,
  "user_prompt": "[Inferred] User request requiring tool usage",
  "user_timestamp": "2025-07-30T08:48:07.967856",
  "llm_reasoning": "Claude selected clearMastraCourseHistory to handle user request",
  "success": true
}
```

**Flow Metadata Fields:**
- **flow_id**: Unique identifier with timestamp-based generation
- **duration_ms**: Precise end-to-end timing with microsecond accuracy
- **event_count**: Number of timeline events captured
- **cross_server_flow**: Boolean indicating multi-server interactions
- **has_user_context**: Whether user intent was successfully inferred
- **llm_reasoning**: AI decision-making summary for the entire flow

#### 3. **LLM Decision Tracking**
Detailed capture of AI reasoning and tool selection:

```json
{
  "llm_decisions": [
    {
      "timestamp": "2025-07-30T08:48:07.967856",
      "user_prompt": "[Inferred] User request requiring tool usage",
      "reasoning": "Claude selected clearMastraCourseHistory to handle user request",
      "tools_considered": ["clearMastraCourseHistory"],
      "tools_selected": ["clearMastraCourseHistory"],
      "tool_calls": [
        {
          "tool_name": "clearMastraCourseHistory",
          "arguments": {"confirm": true},
          "timestamp": "2025-07-30T08:48:07.968004",
          "call_id": "clearMastraCourseHistory_0"
        }
      ],
      "processing_time_ms": 8,
      "confidence_score": 0.8,
      "success": true
    }
  ]
}
```

**LLM Decision Fields:**
- **reasoning**: AI's explanation for tool selection
- **tools_considered**: Tools the LLM evaluated for the task
- **tools_selected**: Final tools chosen by the LLM
- **tool_calls**: Actual tool invocations with arguments
- **processing_time_ms**: Time spent in LLM decision-making
- **confidence_score**: AI's confidence in its decision (0.0-1.0)

#### 4. **MCP Calls & Timeline**
Detailed tracking of MCP tool executions and event timeline:

```json
{
  "mcp_calls": [
    {
      "timestamp": "2025-07-30T08:48:07.966674",
      "server": "mastra",
      "tool": "clearMastraCourseHistory",
      "args": {"confirm": true}
    },
    {
      "timestamp": "2025-07-30T08:48:29.376122",
      "server": "mastra", 
      "tool": "startMastraCourse",
      "args": {}
    }
  ],
  "timeline": [
    {
      "timestamp": "2025-07-30T08:48:07.966674",
      "type": "tool_call",
      "source": "mcp_audit",
      "server": "mastra",
      "content": "Call clearMastraCourseHistory"
    },
    {
      "timestamp": "2025-07-30T08:48:07.967856", 
      "type": "llm_tool_selection",
      "source": "llm_decision",
      "server": "N/A",
      "content": "Selected clearMastraCourseHistory..."
    }
  ]
}
```

**Timeline Event Types:**
- **tool_call**: MCP tool invocation
- **llm_tool_selection**: AI tool selection decision
- **llm_tool_discovery**: AI exploring available tools
- **mcp_response**: Server response to tool calls
- **initialization**: MCP server initialization

#### 5. **Meta Information & Configuration**
```json
{
  "meta": {
    "report_version": "2.1_timeline_with_llm_reasoning",
    "generation_method": "timestamp_proximity_grouping_with_llm_decisions",
    "time_window_seconds": 30,
    "server_filter": null,
    "time_filter_hours": 0.25,
    "data_sources": [
      "mcp_audit_messages",
      "llm_decision_trace"
    ]
  }
}
```

**Meta Configuration:**
- **report_version**: Current version of the detailed report format
- **generation_method**: Algorithm used for flow grouping and analysis
- **time_window_seconds**: Window for grouping related events
- **data_sources**: Sources of data used in analysis
- **server_filter**: Specific server filtering (null = all servers)
- **time_filter_hours**: Time range for the analysis

### Advanced Analytics

#### **Timeline-Based Flow Analysis**
- Timestamp proximity grouping for related events
- Multi-tool sequence analysis with precise timing
- Cross-server flow detection and tracking
- Event correlation within configurable time windows

#### **LLM Reasoning Intelligence**
- Real-time capture of AI decision-making process
- Tool consideration vs. selection analysis
- Confidence score tracking and patterns
- Processing time analysis for optimization

#### **Enhanced Observability**
- Microsecond-precision timing for performance optimization
- Complete event timeline reconstruction
- User intent inference and correlation
- Multi-step workflow success pattern analysis

#### **Flow Pattern Insights**
```json
{
  "advanced_insights": {
    "timeline_analysis": "Events grouped within 30-second windows",
    "llm_reasoning_capture": "100% of flows with AI decision tracking",
    "confidence_patterns": "Average 0.8 confidence on tool selections",
    "multi_tool_sequences": "Sequential tool execution with timing",
    "cross_server_detection": "0 flows spanning multiple servers",
    "precision_timing": "Microsecond accuracy for performance analysis"
  }
}
```

### Key Metrics

#### **Flow Analysis Metrics**
- **total_flows**: Complete interaction sequences analyzed
- **flows_with_user_context**: Flows with successfully inferred user intent
- **flows_with_llm_reasoning**: Flows with captured AI decision-making
- **cross_server_flows**: Multi-server interaction detection
- **success_rate**: Percentage of successful flow completions

#### **LLM Intelligence Metrics**
- **total_llm_decisions**: Individual AI decision points captured
- **confidence_score**: AI confidence in tool selection (0.0-1.0)
- **processing_time_ms**: Time spent in LLM reasoning
- **tools_considered vs. tools_selected**: Decision-making efficiency

#### **Timeline Precision Metrics**
- **duration_ms**: Microsecond-precision flow timing
- **event_count**: Number of timeline events per flow
- **time_window_seconds**: Configurable grouping window
- **timestamp_precision**: Event correlation accuracy

## Sample Generated Reports

### File Location
```
/<PWD>/detailed_report_20250730_165218.json
```

### Key Sections in Sample Report

1. **Timeline-Based Analysis**: 2 flows with timestamp proximity grouping
2. **LLM Reasoning Capture**: Complete AI decision-making process
3. **Event Timeline**: Precise chronological event reconstruction
4. **MCP Call Tracking**: Detailed tool execution with arguments
5. **Meta Configuration**: Report generation methodology and settings

### Sample Interaction Flow
```json
{
  "flow_id": "flow_1753836487",
  "duration_ms": 23510.284,
  "event_count": 6,
  "user_prompt": "[Inferred] User request requiring tool usage",
  "llm_reasoning": "Claude selected clearMastraCourseHistory to handle user request",
  "llm_decisions": [
    {
      "tools_considered": ["clearMastraCourseHistory"],
      "tools_selected": ["clearMastraCourseHistory"],
      "confidence_score": 0.8,
      "processing_time_ms": 8
    }
  ],
  "mcp_calls": [
    {
      "tool": "clearMastraCourseHistory",
      "args": {"confirm": true}
    }
  ],
  "success": true
}
```

### Report Size & Depth
- **241 lines** of comprehensive timeline analysis
- **2 complete flows** with full LLM reasoning capture
- **Microsecond precision timing** for performance optimization
- **Timeline-based event correlation** with configurable grouping windows
- **Real-time LLM decision tracking** with confidence scoring

This detailed report provides the deepest level of insight into AI agent decision-making and MCP tool interactions, with timeline-based analysis that enables precise performance optimization and workflow understanding. 