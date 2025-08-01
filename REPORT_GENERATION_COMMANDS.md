# 📊 MCP Report Generation Commands Reference

> **📌 CLI Usage Note:** All commands can be run using either:
> - `mcp-audit <command>` (recommended - installed CLI entry point)  
> - `python -m mcp_audit.cli <command>` (alternative - direct module access)

## ✅ **What Auto-Starts (No Commands Needed)**

When you install the Cursor plugin, **monitoring automatically starts**:
- ✅ **MCP proxy** captures all messages automatically
- ✅ **Real data collection** runs in background  
- ✅ **Multi-server support** tracks all connected MCP servers
- ✅ **Zero configuration** required after installation

**You can verify auto-monitoring with:**
```bash
mcp-audit proxy-status  # Shows captured messages count
```

## 🔴 **Manual Commands (For Viewing & Analysis)**

### Start Live Monitoring (Background)
```bash
# Activate environment and start live trace monitoring
source .venv/bin/activate && mcp-audit trace --live
```

### Check Monitoring Status
```bash
# Check proxy connection and message count
mcp-audit proxy-status

# Count captured messages
wc -l ~/.cursor/mcp_audit_messages.jsonl

# View latest captured messages
tail -5 ~/.cursor/mcp_audit_messages.jsonl
```

## 📊 **Report Generation Commands**

### 🎯 **New Unified Report Commands (Recommended)**

#### Generate Specific Report Types
```bash
# Component Trace Reports (technical performance)
mcp-audit report --type trace --format json
mcp-audit report --type trace --format html --server mastra
mcp-audit report --type trace --format txt --since "24h"

# Usability Analysis Reports (cognitive load & UX)
mcp-audit report --type usability --format json --server mastra  
mcp-audit report --type usability --format html --since "7d"
mcp-audit report --type usability --format txt

# Complete Observability Reports (integrated technical + UX)
mcp-audit report --type integrated --format json
mcp-audit report --type integrated --format html --server mastra
mcp-audit report --type integrated --format txt --since "24h"
```

#### Custom Output and Filtering
```bash
# Custom output locations
mcp-audit report --type trace --format json --output my_trace_report.json
mcp-audit report --type usability --format html --output ux_analysis.html
mcp-audit report --type integrated --format html --output complete_report.html

# Time-based filtering
mcp-audit report --type trace --format json --since "24h"
mcp-audit report --type usability --format html --since "7d" --server mastra
mcp-audit report --type integrated --format json --since "2024-01-01"

# Server-specific analysis
mcp-audit report --type trace --format html --server mastra
mcp-audit report --type usability --format json --server openweather
mcp-audit report --type integrated --format html --server mastra
```

#### Generated File Naming
```bash
# Default timestamped naming:
# trace_report_[server_]YYYYMMDD_HHMMSS.json
# usability_report_[server_]YYYYMMDD_HHMMSS.html  
# integrated_report_[server_]YYYYMMDD_HHMMSS.json

# Examples:
# trace_report_mastra_20240721_143052.json
# usability_report_20240721_143052.html
# integrated_report_mastra_20240721_143052.json
```

### 📋 **Legacy Report Commands (Still Supported)**

### 1. 🔄 Real Component Trace Reports
```bash
# ✅ NEW: CLI now uses real data by default (no separate script needed!)
mcp-audit trace --show-events --export component_trace_$(date +%Y%m%d_%H%M%S).json

# Filter by specific MCP server
mcp-audit trace --server "Mastra" --show-events

# Generate all reports (still available for comprehensive analysis)
python generate_real_traces.py
```

### 2. 📈 Real Usability Analysis Reports
```bash
# Generate usability report for specific server (defaults to --type usability)
mcp-audit report --format json --server mastra

# Generate general usability report
mcp-audit report --format json

# Generate with custom output path
mcp-audit report --format json --output ./reports/
```

### 3. 🔍 Complete Observability Reports
```bash
# Generate integrated reports (component traces + usability)
python generate_real_traces.py  # Creates all three report types

# Manual integration (run both separately)
mcp-audit trace --export trace.json --show-events
mcp-audit report --format json --server mastra
```

## 🔍 **Data Analysis Commands**

### View Raw Captured Data
```bash
# Show all captured messages
cat ~/.cursor/mcp_audit_messages.jsonl

# Show first 10 messages
head -10 ~/.cursor/mcp_audit_messages.jsonl

# Show last 10 messages  
tail -10 ~/.cursor/mcp_audit_messages.jsonl

# Count total messages
wc -l ~/.cursor/mcp_audit_messages.jsonl
```

### Pretty-Print MCP Messages
```bash
# Format latest 3 messages nicely
python -c "
import json
with open('/Users/sureshjain/.cursor/mcp_audit_messages.jsonl', 'r') as f:
    lines = f.readlines()
    for line in lines[-3:]:
        data = json.loads(line.strip())
        print('='*80)
        print(f'⏰ {data[\"timestamp\"]}')
        print(f'🔄 {data[\"direction\"]}')
        print(f'📋 Method: {data[\"payload\"].get(\"method\", \"N/A\")}')
        if 'params' in data['payload']:
            print(f'📥 Params: {str(data[\"payload\"][\"params\"])[:200]}...')
        if 'result' in data['payload']:
            print(f'📤 Result: {str(data[\"payload\"][\"result\"])[:200]}...')
        print()
"
```

### Show Message Timeline
```bash
# Show timeline of all captured messages
python -c "
import json
with open('/Users/sureshjain/.cursor/mcp_audit_messages.jsonl', 'r') as f:
    for i, line in enumerate(f, 1):
        data = json.loads(line.strip())
        timestamp = data['timestamp'][:19]
        direction = data['direction']
        payload = data['payload']
        method = payload.get('method', 'response')
        
        if method == 'tools/call':
            tool_name = payload.get('params', {}).get('name', '')
            print(f'{i:2d}. {timestamp} → {method} ({tool_name})')
        elif 'result' in payload and 'content' in str(payload.get('result', {})):
            result_text = str(payload.get('result', {}))
            if 'Step' in result_text and 'completed' in result_text:
                step_info = '→ Course step completed'
            else:
                step_info = '→ Response'
            print(f'{i:2d}. {timestamp} → {method} {step_info}')
        else:
            print(f'{i:2d}. {timestamp} → {method}')
"
```

### Count Messages by Type
```bash
# Count message directions
python -c "
import json
from collections import Counter
with open('/Users/sureshjain/.cursor/mcp_audit_messages.jsonl', 'r') as f:
    directions = [json.loads(line.strip())['direction'] for line in f]
    print('Message Directions:')
    for direction, count in Counter(directions).items():
        print(f'  {direction}: {count}')
"
```

## 📁 **File Output Locations**

### Generated Report Files
```bash
# Real component traces
real_component_trace_YYYYMMDD_HHMMSS.json

# Real usability analysis  
audit_report_mastra_YYYYMMDD_HHMMSS.json
real_usability_report_YYYYMMDD_HHMMSS.json

# Complete observability
real_complete_observability_YYYYMMDD_HHMMSS.json
```

### Source Data Files
```bash
# Captured MCP messages
~/.cursor/mcp_audit_messages.jsonl

# Proxy logs
~/.cursor/mcp_audit_proxy.log
```

## 🔧 **Advanced Analysis Commands**

### Compare Report Contents
```bash
# Show key differences between reports
echo "=== COMPONENT TRACE ===" && head -20 real_component_trace_*.json
echo "=== USABILITY ANALYSIS ===" && head -20 audit_report_mastra_*.json  
echo "=== COMPLETE OBSERVABILITY ===" && head -20 real_complete_observability_*.json
```

### Extract Specific Data
```bash
# Show cognitive load scores from all reports
grep -r "cognitive_load" audit_report_*.json

# Show data sources to verify real vs demo
grep -r "data_source" real_*.json

# Show captured tool names
grep -o '"name":"[^"]*"' ~/.cursor/mcp_audit_messages.jsonl | sort | uniq
```

### Generate Fresh Reports with Latest Data
```bash
# Complete workflow to get latest analysis
echo "Current message count:" && wc -l ~/.cursor/mcp_audit_messages.jsonl
echo "Generating fresh reports..." && python generate_real_traces.py
echo "Latest usability analysis..." && mcp-audit report --format json --server mastra
echo "All reports updated!"
```

## ⚙️ **Environment Setup Commands**

### Activate Environment
```bash
# Always run this first
source .venv/bin/activate
```

### Check Installation
```bash
# Verify CLI is working
mcp-audit --help

# Check proxy connection
mcp-audit status
```

### Environment Variables (Optional)
```bash
# Set custom report directory
export MCP_AUDIT_REPORTS_DIR="./my_reports"

# Enable real-time monitoring
export MCP_AUDIT_REAL_TIME="true"
```

## 🚀 **One-Liner Report Generation**

### Generate All Reports Quickly
```bash
# Generate all three report types in one command
source .venv/bin/activate && echo "📊 Generating complete reports..." && python generate_real_traces.py && mcp-audit report --format json --server mastra && echo "✅ All reports generated!"
```

### Monitor + Generate Loop
```bash
# Start monitoring, wait, then generate reports
source .venv/bin/activate && echo "🔴 Starting monitoring..." && mcp-audit trace --live &
# (Do some MCP interactions in Cursor)
# Then: python generate_real_traces.py && mcp-audit report --format json --server mastra
```

## 📋 **Quick Reference Summary**

| Task | Unified Command (Recommended) | Legacy Command |
|------|-------------------------------|----------------|
| **Component Trace Report** | `mcp-audit report --type trace --format json` | `python generate_real_traces.py` |
| **Usability Analysis Report** | `mcp-audit report --type usability --format json --server mastra` | `mcp-audit report --format json --server mastra` |
| **Complete Observability Report** | `mcp-audit report --type integrated --format html` | `python generate_real_traces.py` |
| **Start monitoring** | `mcp-audit trace --live` | `mcp-audit trace --live` |
| **Check status** | `mcp-audit proxy-status` | `mcp-audit proxy-status` |
| **View captured data** | `cat ~/.cursor/mcp_audit_messages.jsonl` | `cat ~/.cursor/mcp_audit_messages.jsonl` |
| **Count messages** | `wc -l ~/.cursor/mcp_audit_messages.jsonl` | `wc -l ~/.cursor/mcp_audit_messages.jsonl` |
| **Latest messages** | `tail -5 ~/.cursor/mcp_audit_messages.jsonl` | `tail -5 ~/.cursor/mcp_audit_messages.jsonl` |

### 🎯 **Report Type Selection Guide**

| Use Case | Report Type | Command |
|----------|-------------|---------|
| **Performance optimization** | Component Trace | `mcp-audit report --type trace --format html` |
| **UX improvement** | Usability Analysis | `mcp-audit report --type usability --format html` |
| **Executive dashboard** | Complete Observability | `mcp-audit report --type integrated --format html` |
| **Technical debugging** | Component Trace | `mcp-audit report --type trace --format json` |
| **Cognitive load analysis** | Usability Analysis | `mcp-audit report --type usability --format json` |
| **Comprehensive monitoring** | Complete Observability | `mcp-audit report --type integrated --format json` |

## 🔗 **Multiple MCP Server Support**

### Automatic Multi-Server Tracking
```bash
# The system automatically tracks ALL connected MCP servers
# No configuration needed - just connect servers to Cursor and they're monitored

# View all detected servers
python -c "
import json
servers = set()
with open('/Users/sureshjain/.cursor/mcp_audit_messages.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line.strip())
        payload = data.get('payload', {})
        if 'result' in payload and 'serverInfo' in str(payload['result']):
            result = payload['result']
            if isinstance(result, dict) and 'serverInfo' in result:
                server_name = result['serverInfo'].get('name', 'Unknown')
                servers.add(server_name)
print('Detected MCP servers:')
for server in servers:
    print(f'  • {server}')
"
```

### Server-Specific Filtering
```bash
# View traces for specific server only
mcp-audit trace --server "Mastra" --show-events
mcp-audit trace --server "OpenWeather" --show-events

# Generate reports for specific server
mcp-audit report --format json --server mastra
mcp-audit report --format json --server openweather

# View all servers in sequence (automatically captured)
mcp-audit trace --show-events  # Shows all servers
```

### Communication Flow Handling
- ✅ **Sequential flows**: Each MCP interaction traced in order
- ✅ **Parallel servers**: Multiple servers can be active simultaneously  
- ✅ **Flow isolation**: Each server's interactions tracked separately
- ✅ **Cross-server analysis**: Compare usability across different servers

## 🧹 **Reset & Uninstall Commands**

### Reset All Captured Data
```bash
# Interactive script to reset all data
./reset_data.sh

# Manual reset (immediate, no prompts)
rm -f ~/.cursor/mcp_audit_messages.jsonl
rm -f ~/.cursor/mcp_audit_proxy.log
rm -f audit_report_*.json real_*.json component_trace_*.json
rm -f complete_observability_*.json integrated_*.json

# Check what will be deleted first
echo "Messages: $(wc -l < ~/.cursor/mcp_audit_messages.jsonl 2>/dev/null || echo '0')"
echo "Reports: $(ls -1 *audit*.json *real_*.json 2>/dev/null | wc -l)"
```

### Uninstall Agent from Cursor
```bash
# Interactive uninstall script
./uninstall_cursor_agent.sh

# Manual uninstall steps
# 1. Stop processes
pkill -f "mcp_proxy"
pkill -f "trace --live"

# 2. Restore original MCP config
cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "mastra": {
      "command": "pnpx",
      "args": ["@mastra/mcp-docs-server"]
    }
  }
}
EOF

# 3. Clean up data files
rm -f ~/.cursor/mcp_audit_*

# 4. Restart Cursor to apply changes
```

### Check Installation Status
```bash
# Check what's currently installed/active
echo "📊 Current Status:"
echo "Proxy config: $(grep -q mcp_proxy_runner ~/.cursor/mcp.json && echo 'ACTIVE' || echo 'Not found')"
echo "Messages: $(wc -l < ~/.cursor/mcp_audit_messages.jsonl 2>/dev/null || echo '0')"
echo "Proxy processes: $(ps aux | grep mcp_proxy | grep -v grep | wc -l)"
echo "Reports: $(ls -1 *audit*.json *real_*.json 2>/dev/null | wc -l)"
```

---

**💡 Pro Tips:**
1. Always run `source .venv/bin/activate` first
2. Use `python generate_real_traces.py` for real data reports  
3. Monitor live with `trace --live` for real-time insights
4. Generate fresh reports after course interactions for updated analysis
5. **Reset data** to start fresh monitoring sessions
6. **Uninstall safely** - your original Mastra MCP server will work normally 