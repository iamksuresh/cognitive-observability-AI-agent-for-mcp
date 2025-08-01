#!/bin/bash
# Reset All MCP Usability Audit Data

echo "🧹 Resetting MCP Usability Audit Data..."
echo "========================================"

# Check if files exist and show what will be deleted
echo "📊 Current data status:"

# Check captured messages
if [ -f ~/.cursor/mcp_audit_messages.jsonl ]; then
    MESSAGE_COUNT=$(wc -l < ~/.cursor/mcp_audit_messages.jsonl)
    echo "  📨 Captured messages: $MESSAGE_COUNT"
else
    echo "  📨 Captured messages: None"
fi

# Check proxy logs
if [ -f ~/.cursor/mcp_audit_proxy.log ]; then
    LOG_SIZE=$(du -h ~/.cursor/mcp_audit_proxy.log | cut -f1)
    echo "  📋 Proxy logs: $LOG_SIZE"
else
    echo "  📋 Proxy logs: None"
fi

# Check report files
REPORT_COUNT=$(ls -1 audit_report_*.json real_*.json component_trace_*.json complete_observability_*.json integrated_*.json 2>/dev/null | wc -l)
echo "  📊 Generated reports: $REPORT_COUNT files"

echo ""
read -p "⚠️  Do you want to delete ALL this data? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting captured data..."
    
    # Remove captured messages
    if [ -f ~/.cursor/mcp_audit_messages.jsonl ]; then
        rm ~/.cursor/mcp_audit_messages.jsonl
        echo "  ✅ Deleted captured messages"
    fi
    
    # Remove proxy logs
    if [ -f ~/.cursor/mcp_audit_proxy.log ]; then
        rm ~/.cursor/mcp_audit_proxy.log
        echo "  ✅ Deleted proxy logs"
    fi
    
    # Remove generated reports
    rm -f audit_report_*.json
    rm -f real_*.json
    rm -f component_trace_*.json
    rm -f complete_observability_*.json
    rm -f integrated_*.json
    rm -f trace_*.json
    echo "  ✅ Deleted generated reports"
    
    # Remove demo/temp files
    rm -f *.jsonl
    rm -f demo_*.json
    echo "  ✅ Deleted temporary files"
    
    echo ""
    echo "🎉 All data reset successfully!"
    echo "💡 Monitoring will start fresh on next MCP interaction"
    
else
    echo "❌ Reset cancelled"
fi 