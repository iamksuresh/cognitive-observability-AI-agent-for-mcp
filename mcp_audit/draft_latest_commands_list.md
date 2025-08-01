# 🚀 **MCP Audit Agent - One-Liner Commands**

## 📦 **Installation**

```bash
# Clone and install
git clone <your-repo-url> && cd mcp-useability-audit-agent && python -m venv .venv && source .venv/bin/activate && pip install -e .
```

## 🔧 **Quick Setup**

```bash
# Setup MCP proxy in one command
mcp-audit proxy
```

## 📊 **Dashboard & Monitoring**

```bash
# Launch web dashboard (default port 8000)
mcp-audit dashboard

# Launch dashboard on custom port
mcp-audit dashboard --port 8080

# Launch dashboard with auto-reload for development
mcp-audit dashboard --reload
```

## 📈 **Report Generation**

```bash
# Generate usability report
mcp-audit report --type usability

# Generate trace report with export
mcp-audit trace --export json

# Generate integrated report (all data)
mcp-audit report --type integrated

# Generate complete observability report
mcp-audit report --type trace
```

## 🔗 **Enterprise Integrations**

```bash
# Setup LangSmith integration with test
mcp-audit integrate langsmith --api-key "lsv2_pt_your_key_here" --project "mcp-analysis" --test

# Setup Mixpanel integration with test
mcp-audit integrate mixpanel --api-key "your_mixpanel_key" --project-token "your_project_token" --test

# Setup PostHog integration with test
mcp-audit integrate posthog --api-key "phc_your_key_here" --test

# Check all integration status
mcp-audit integrate status
```

## 🕵️ **Status & Monitoring**

```bash
# Check proxy status and captured messages
mcp-audit proxy-status

# View recent proxy logs
mcp-audit proxy-logs

# Check overall system status
mcp-audit status

# Monitor live interactions for 60 seconds
mcp-audit monitor --duration 60
```

## 🔄 **Daemon Operations**

```bash
# Start background daemon
mcp-audit-daemon start

# Stop background daemon
mcp-audit-daemon stop

# Check daemon status
mcp-audit-daemon status
```

## 🧪 **Testing & Demo**

```bash
# Run demo simulation
mcp-audit demo mastra-docs

# Generate comprehensive trace (includes latest interactions)
python generate_comprehensive_trace.py

# Test specific server monitoring
mcp-audit monitor --server mastra-docs --duration 30
```

## 🔥 **Complete Workflow One-Liners**

### **Full Setup + Dashboard**
```bash
mcp-audit proxy && mcp-audit dashboard &
```

### **Setup + Integration + Dashboard**
```bash
mcp-audit proxy && mcp-audit integrate langsmith --api-key "your_key" --test && mcp-audit dashboard
```

### **Generate All Reports**
```bash
mcp-audit report --type usability && mcp-audit report --type trace && mcp-audit report --type integrated
```

### **Complete Monitoring Setup**
```bash
mcp-audit proxy && mcp-audit-daemon start && mcp-audit dashboard --port 8000 &
```

## 🐛 **Troubleshooting**

```bash
# Reset proxy configuration
mcp-audit proxy --restore

# View detailed logs with verbose output
mcp-audit -v status

# Check captured message count
cat ~/.cursor/mcp_audit_messages.jsonl | wc -l

# Verify dashboard is accessible
curl -s http://localhost:8000/api/status | python -m json.tool
```

## 🔍 **Quick Checks**

```bash
# Check if proxy is capturing messages
tail -5 ~/.cursor/mcp_audit_messages.jsonl

# Test dashboard API endpoints
curl http://localhost:8000/api/cognitive-metrics

# Verify integrations are working
mcp-audit integrate status

# Check daemon health
mcp-audit-daemon status
```

## 📱 **URLs & Endpoints**

```bash
# Web Dashboard
open http://localhost:8000

# API Status
curl http://localhost:8000/api/status

# Cognitive Metrics
curl http://localhost:8000/api/cognitive-metrics

# Recent Activity
curl http://localhost:8000/api/recent-activity
```

---

## 🎯 **Most Common Workflows**

### **Development Testing**
```bash
mcp-audit proxy && mcp-audit dashboard && echo "✅ Ready! Use Cursor with MCP servers, monitor at http://localhost:8000"
```

### **Production Monitoring**
```bash
mcp-audit-daemon start && mcp-audit integrate langsmith --api-key "your_key" --test && echo "✅ Production monitoring active"
```

### **Quick Report Generation**
```bash
mcp-audit report --type usability && echo "✅ Usability report generated"
```

### **Complete Setup & Test**
```bash
mcp-audit proxy && mcp-audit demo mastra-docs && mcp-audit report --type usability && mcp-audit dashboard
``` 