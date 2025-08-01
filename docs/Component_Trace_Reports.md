# Component Trace Reports

## Overview

**Component Trace Reports** provide detailed technical analysis of MCP system flows, performance metrics, and component interactions. These reports focus on the **technical performance** aspects of your MCP system, helping you identify bottlenecks, optimize latency, and ensure reliable operation.

## What Component Trace Reports Include

### 🔄 **Flow Visualization**
- **Component interaction diagrams** showing data flow between system parts
- **Timeline analysis** with precise timing of each operation
- **Request/response tracking** through the entire MCP stack
- **Protocol-level message analysis** (JSON-RPC, WebSocket, etc.)

### ⚡ **Performance Metrics**
- **Latency measurements** for each component and operation
- **Throughput analysis** and request processing rates
- **Bottleneck identification** and critical path analysis
- **Efficiency scoring** based on industry benchmarks

### 🔧 **Technical Health Indicators**
- **Error rates** and failure patterns by component
- **Retry patterns** and recovery mechanisms
- **Resource utilization** and system load analysis
- **Protocol compliance** and specification adherence

## How Component Trace Reports Are Generated

### 1. **Real-Time Message Capture**

The MCP proxy intercepts all communications:

```python
# Message interception in mcp_proxy.py
async def _capture_message(self, direction: MCPMessageDirection, data: dict):
    """Capture and log MCP messages with timing."""
    message_trace = MCPMessageTrace(
        timestamp=datetime.utcnow(),
        direction=direction,
        protocol=MCPProtocol.JSON_RPC,
        payload=data,
        latency_ms=self._calculate_latency(),
        error_code=self._detect_errors(data)
    )
    
    await self._save_trace(message_trace)
```

### 2. **Component Flow Analysis**

Messages are grouped and analyzed by flow:

```python
def analyze_component_flows(messages):
    """Convert raw MCP messages into component interaction flows."""
    flows = []
    
    for message_group in group_by_interaction(messages):
        flow = RequestFlow(
            flow_id=generate_flow_id(),
            user_query=extract_user_intent(message_group),
            start_time=message_group[0]['timestamp'],
            components=map_to_components(message_group)
        )
        
        # Add component interactions
        for msg in message_group:
            interaction = ComponentInteraction(
                source=map_source_component(msg['direction']),
                target=map_target_component(msg['direction']),
                operation=msg['payload'].get('method', 'unknown'),
                latency_ms=msg.get('latency_ms', 0),
                success=not bool(msg.get('error_code'))
            )
            flow.add_interaction(interaction)
            
        flows.append(flow)
    
    return flows
```

### 3. **Performance Calculation**

```python
def calculate_performance_metrics(flow):
    """Calculate comprehensive performance metrics for a flow."""
    total_latency = sum(interaction.latency_ms for interaction in flow.interactions)
    critical_path = calculate_critical_path(flow.interactions)
    
    # Component performance analysis
    component_stats = {}
    for interaction in flow.interactions:
        component = interaction.target.component
        if component not in component_stats:
            component_stats[component] = ComponentStats()
        
        component_stats[component].add_measurement(
            latency=interaction.latency_ms,
            success=interaction.success
        )
    
    # Efficiency scoring
    efficiency_score = calculate_efficiency_score(
        total_latency=total_latency,
        critical_path=critical_path,
        error_count=count_errors(flow.interactions)
    )
    
    return PerformanceMetrics(
        total_latency_ms=total_latency,
        critical_path_ms=critical_path,
        efficiency_score=efficiency_score,
        component_stats=component_stats
    )
```

## Generation Commands

### 📊 **Visual Component Traces**
```bash
# Interactive visual trace with component flow diagrams
mcp-audit trace

# Detailed trace with event information
mcp-audit trace --show-events

# Live monitoring for real-time component analysis
mcp-audit trace --live
```

### 💾 **Exported Component Trace Reports (New Unified Commands)**
```bash
# Generate comprehensive trace report using new unified command
mcp-audit report --type trace --format json

# Generate HTML trace report with visualizations
mcp-audit report --type trace --format html --server mastra

# Generate text trace summary
mcp-audit report --type trace --format txt --server mastra

# Custom output location
mcp-audit report --type trace --format json --output my_component_analysis.json

# Server-specific component analysis
mcp-audit report --type trace --format json --server mastra
# Creates: trace_report_mastra_YYYYMMDD_HHMMSS.json
```

### 🔍 **Advanced Component Analysis**
```bash
# Generate comprehensive trace with ALL interactions (alternative method)
python generate_comprehensive_trace.py

# Real-time component monitoring
mcp-audit trace --live --server mastra

# Time-filtered component analysis
mcp-audit report --type trace --format html --since "24h"

# Multiple format generation
mcp-audit report --type trace --format json --output trace_data.json
mcp-audit report --type trace --format html --output trace_report.html
```

### 🚀 **Quick Generation Examples**
```bash
# Technical performance analysis (JSON for processing)
mcp-audit report --type trace --format json

# Component flow visualization (HTML with diagrams)  
mcp-audit report --type trace --format html

# Quick performance check (text summary)
mcp-audit report --type trace --format txt --since "24h"

# Live component monitoring
mcp-audit trace --live
```

### 📊 **Legacy Export Commands**
```bash
# These commands still work for backward compatibility
mcp-audit trace --export component_trace_report.json
mcp-audit trace --export my_component_analysis.json

# But the new unified approach is recommended:
mcp-audit report --type trace --format json --output component_trace_report.json
```

## Component Mapping

### 🎯 **MCP System Components**

The system maps raw MCP messages to logical components:

| **Component Type** | **Description** | **Responsibilities** |
|---|---|---|
| **User Interface** | Cursor IDE, VS Code | User input collection, result display |
| **MCP Host** | Cursor's MCP client | Protocol handling, tool management |
| **LLM Engine** | Claude, GPT-4, etc. | Query understanding, response generation |
| **MCP Client** | JSON-RPC client | Protocol communication, message formatting |
| **MCP Server** | Mastra, custom servers | Tool execution, resource access |
| **External API** | Weather APIs, databases | External service integration |

### 🔄 **Message Direction Mapping**

```python
# Direction mapping in component analysis
DIRECTION_TO_COMPONENTS = {
    'llm→mcp_client': {
        'source': {'component': 'llm_engine', 'name': 'Claude/GPT'},
        'target': {'component': 'mcp_client', 'name': 'MCP Client'}
    },
    'mcp_client→server': {
        'source': {'component': 'mcp_client', 'name': 'MCP Client'},
        'target': {'component': 'mcp_server', 'name': 'Mastra MCP Server'}
    }
}
```

## Report Structure

### 📊 **Component Trace Report JSON Structure**

```json
{
  "comprehensive_trace_report": {
    "generated_at": "2025-07-21T13:36:52.123456Z",
    "total_messages_processed": 25,
    "distinct_interactions": 6,
    "data_source": "real_mcp_capture_comprehensive"
  },
  
  "interactions": [
    {
      "flow_metadata": {
        "flow_id": "flow_12345",
        "user_query": "User Tool Call: mastraDocs",
        "status": "completed",
        "total_latency_ms": 2367,
        "component_count": 4,
        "start_time": "2025-07-21T13:31:53.082510",
        "end_time": "2025-07-21T13:31:55.449511"
      },
      
      "component_interactions": [
        {
          "source": {"component": "llm_engine", "name": "Claude/GPT"},
          "target": {"component": "mcp_client", "name": "MCP Client"},
          "operation": "tools/call",
          "latency_ms": 50,
          "success": true,
          "request_data": {
            "timestamp": "2025-07-21T13:31:53.082510",
            "protocol": "JSON-RPC",
            "payload_summary": "Tool call to mastraDocs with paths parameter"
          }
        },
        {
          "source": {"component": "mcp_client", "name": "MCP Client"},
          "target": {"component": "mcp_server", "name": "Mastra MCP Server"},
          "operation": "response",
          "latency_ms": 2317,
          "success": true,
          "request_data": {
            "timestamp": "2025-07-21T13:31:55.449511",
            "protocol": "JSON-RPC",
            "payload_summary": "Response with documentation content"
          }
        }
      ],
      
      "raw_mcp_messages": [
        {
          "timestamp": "2025-07-21T13:31:53.082510",
          "direction": "llm→mcp_client",
          "protocol": "JSON-RPC",
          "payload": {
            "method": "tools/call",
            "params": {"name": "mastraDocs", "arguments": {"paths": ["agents/overview.mdx"]}},
            "jsonrpc": "2.0",
            "id": 6
          },
          "latency_ms": null,
          "error_code": null
        }
      ]
    }
  ]
}
```

### 🎨 **Visual Component Flow Diagram**

When you run `mcp-audit trace`, you get:

```
🔄 Component Flow Diagram
   ┌─ Claude/GPT
   │ ✅ tools/call ──> MCP Client (50ms)
   └─ MCP Client
   │ ✅ response ──> Mastra MCP Server (2317ms)
   └─ Mastra MCP Server

⏱️  Interaction Timeline
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Time         ┃ Source          ┃  →  ┃ Target          ┃ Operation            ┃   Duration ┃  Status  ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ +0ms         │ Claude/GPT      │  →  │ MCP Client      │ tools/call           │       50ms │  ✅ OK   │
│ +50ms        │ MCP Client      │  →  │ Mastra MCP      │ response             │     2317ms │  ✅ OK   │
│              │                 │     │ Server          │                      │            │          │
└──────────────┴─────────────────┴─────┴─────────────────┴──────────────────────┴────────────┴──────────┘
```

## Performance Analysis

### ⚡ **Latency Analysis**

Component traces provide detailed latency breakdown:

```python
# Performance calculation example
{
  "total_duration_ms": 2367,
  "critical_path_ms": 2367,
  "network_latency_ms": 2317,  # Slowest component
  "processing_time_ms": 50,
  
  "efficiency_score": 75.5,    # Based on industry benchmarks
  "bottleneck_component": "Mastra MCP Server",
  "optimization_opportunity": "Network/processing delay in documentation retrieval"
}
```

### 📊 **Component Performance Table**

```
🔧 Component Performance
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Component            ┃    Calls ┃   Total Time ┃  Avg Latency ┃   Errors ┃   Status   ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Claude/GPT           │        1 │         50ms │         50ms │        0 │ EFFICIENT  │
│ MCP Client           │        2 │        100ms │         50ms │        0 │ EFFICIENT  │
│ Mastra MCP Server    │        1 │       2317ms │       2317ms │        0 │   SLOW     │
└──────────────────────┴──────────┴──────────────┴──────────────┴──────────┴────────────┘
```

### 🎯 **Efficiency Scoring**

```python
def calculate_efficiency_score(total_latency, component_count, error_count):
    """Calculate efficiency score based on performance metrics."""
    # Base efficiency starts at 100%
    efficiency = 100.0
    
    # Latency penalties
    if total_latency > 5000:      # >5s is slow
        efficiency -= 30
    elif total_latency > 2000:    # >2s is moderate
        efficiency -= 15
    elif total_latency > 1000:    # >1s is acceptable
        efficiency -= 5
    
    # Error penalties
    efficiency -= error_count * 10
    
    # Component complexity penalty
    if component_count > 5:
        efficiency -= (component_count - 5) * 2
    
    return max(0.0, min(100.0, efficiency))
```

## Use Cases

### 🔧 **Performance Optimization**
- **Identify bottlenecks** in MCP communication chains
- **Measure latency** across different components
- **Track performance** improvements after optimizations
- **Monitor** system degradation over time

### 🛠️ **System Architecture Analysis**
- **Understand data flow** through your MCP system
- **Identify unnecessary** component interactions
- **Optimize** message routing and protocol usage
- **Plan** system scaling and architecture changes

### 🔍 **Debugging and Troubleshooting**
- **Trace failures** through the component stack
- **Identify** which component caused errors
- **Analyze** retry patterns and recovery mechanisms
- **Debug** protocol-level communication issues

### 📊 **DevOps and Monitoring**
- **Monitor** system health in production
- **Set up alerts** for performance degradation
- **Track** SLA compliance and response times
- **Generate** technical reports for stakeholders

## Best Practices

### ⏰ **Regular Performance Monitoring**
```bash
# Daily performance check
mcp-audit trace --export daily_performance_$(date +%Y%m%d).json

# Live monitoring during high-traffic periods
mcp-audit trace --live

# Weekly comprehensive analysis
python generate_comprehensive_trace.py
```

### 🎯 **Bottleneck Identification**
- **Monitor component latency** trends over time
- **Identify** consistently slow components
- **Analyze** critical path optimizations
- **Track** improvement after changes

### 📈 **Performance Benchmarking**
```bash
# Before optimization
mcp-audit trace --export baseline_performance.json

# After optimization  
mcp-audit trace --export optimized_performance.json

# Compare improvements
diff -u baseline_performance.json optimized_performance.json
```

### 🔧 **System Health Monitoring**
- **Set up automated** report generation
- **Monitor error rates** by component
- **Track** overall system efficiency scores
- **Alert** on performance threshold breaches

## Advanced Features

### 🔬 **Custom Component Analysis**
For advanced users, extend component analysis by:

1. **Adding custom component types** in the mapping configuration
2. **Implementing custom** performance metrics
3. **Creating specialized** flow analysis for your use case
4. **Integrating** with external monitoring systems

### 📊 **Integration with Monitoring Tools**
- **Export** to Prometheus/Grafana for visualization
- **Send** metrics to Datadog or New Relic
- **Integrate** with existing APM solutions
- **Create** custom dashboards from JSON exports

## Related Commands

```bash
# Generate component trace reports  
mcp-audit report --type trace --format json
mcp-audit report --type trace --format html --server mastra

# Generate other report types for comprehensive analysis
mcp-audit report --type usability --format html     # UX analysis
mcp-audit report --type integrated --format html    # Combined technical + UX

# Quick visual analysis
mcp-audit trace

# Detailed component export
mcp-audit trace --export component_analysis.json   # Legacy export method

# Live component monitoring  
mcp-audit trace --live

# Proxy status and health
mcp-audit proxy-status

# Raw message inspection
tail -f ~/.cursor/mcp_audit_messages.jsonl
```

## Technical Implementation

### 🔄 **Message Processing Pipeline**

```python
# Simplified processing pipeline
def process_component_traces():
    # 1. Load raw MCP messages
    messages = load_from_jsonl("~/.cursor/mcp_audit_messages.jsonl")
    
    # 2. Group by user interactions  
    interactions = group_messages_by_interaction(messages)
    
    # 3. Map to components
    component_flows = map_to_component_flows(interactions)
    
    # 4. Calculate performance metrics
    performance_data = calculate_performance_metrics(component_flows)
    
    # 5. Generate visualizations
    visual_traces = generate_flow_diagrams(component_flows)
    
    # 6. Export results
    export_component_trace_report(performance_data, visual_traces)
```

This technical foundation enables comprehensive component analysis and performance optimization for MCP systems. 