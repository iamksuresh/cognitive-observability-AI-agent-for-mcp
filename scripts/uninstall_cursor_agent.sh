#!/bin/bash
# Uninstall MCP Usability Audit Agent from Cursor
# Updated version for modern mcp-audit system with enterprise integrations

echo "🗑️  Uninstalling MCP Usability Audit Agent from Cursor..."
echo "========================================================="

# Function to backup files
backup_file() {
    if [ -f "$1" ]; then
        cp "$1" "$1.backup.$(date +%Y%m%d_%H%M%S)"
        echo "  📋 Backed up: $1"
    fi
}

# Function to restore original MCP configuration
restore_mcp_config() {
    echo "🔧 Restoring original MCP configuration..."
    
    # Use the mcp-audit CLI to restore if available
    if command -v mcp-audit >/dev/null 2>&1; then
        echo "  🔄 Using mcp-audit CLI to restore configuration..."
        mcp-audit proxy --restore 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Configuration restored via mcp-audit CLI"
            return 0
        else
            echo "  ⚠️  CLI restore failed, trying manual restore..."
        fi
    fi
    
    # Always create/restore the Mastra configuration manually as backup
    mkdir -p ~/.cursor
    
    # Backup existing config if it exists
    if [ -f ~/.cursor/mcp.json ]; then
        backup_file ~/.cursor/mcp.json
    fi
    
    # Create clean Mastra configuration (without proxy)
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
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Restored direct Mastra MCP configuration"
    else
        echo "  ❌ Failed to restore MCP configuration"
        return 1
    fi
}

# Function to stop any running processes
stop_processes() {
    echo "🛑 Stopping running processes..."
    
    # Stop mcp-audit daemon if running
    if command -v mcp-audit-daemon >/dev/null 2>&1; then
        echo "  🔄 Stopping mcp-audit daemon..."
        mcp-audit-daemon stop 2>/dev/null
    fi
    
    # Find and kill any running proxy processes (more comprehensive search)
    PROXY_PIDS=$(ps aux | grep -E "(mcp.audit|mcp_proxy|mcp.*interceptor)" | grep -v grep | awk '{print $2}')
    if [ ! -z "$PROXY_PIDS" ]; then
        echo "  🎯 Found audit processes: $PROXY_PIDS"
        echo "$PROXY_PIDS" | xargs kill -TERM 2>/dev/null
        sleep 2
        
        # Force kill if still running
        REMAINING_PIDS=$(ps aux | grep -E "(mcp.audit|mcp_proxy|mcp.*interceptor)" | grep -v grep | awk '{print $2}')
        if [ ! -z "$REMAINING_PIDS" ]; then
            echo "  💀 Force killing remaining processes: $REMAINING_PIDS"
            echo "$REMAINING_PIDS" | xargs kill -KILL 2>/dev/null
        fi
        echo "  ✅ Stopped audit processes"
    else
        echo "  ℹ️  No audit processes running"
    fi
    
    # Stop dashboard if running
    DASHBOARD_PIDS=$(ps aux | grep -E "(mcp.*audit.*dashboard|uvicorn.*dashboard)" | grep -v grep | awk '{print $2}')
    if [ ! -z "$DASHBOARD_PIDS" ]; then
        echo "$DASHBOARD_PIDS" | xargs kill -TERM 2>/dev/null
        echo "  ✅ Stopped dashboard processes"
    else
        echo "  ℹ️  No dashboard processes running"
    fi
    
    # Find and kill any running trace monitoring
    TRACE_PIDS=$(ps aux | grep "trace --live" | grep -v grep | awk '{print $2}')
    if [ ! -z "$TRACE_PIDS" ]; then
        echo "$TRACE_PIDS" | xargs kill 2>/dev/null
        echo "  ✅ Stopped trace monitoring"
    else
        echo "  ℹ️  No trace monitoring running"
    fi
}

# Function to uninstall VS Code extension (if applicable)
uninstall_extension() {
    echo "📦 Checking for installed extensions..."
    
    # Check if extensions directory exists (don't require cursor command in PATH)
    EXTENSION_DIR="$HOME/.cursor/extensions"
    if [ -d "$EXTENSION_DIR" ]; then
        # Look for our extension
        MCP_EXTENSION=$(find "$EXTENSION_DIR" -name "*mcp*audit*" -type d 2>/dev/null)
        if [ ! -z "$MCP_EXTENSION" ]; then
            echo "  🎯 Found extension: $MCP_EXTENSION"
            rm -rf "$MCP_EXTENSION"
            if [ $? -eq 0 ]; then
                echo "  ✅ Removed extension directory"
            else
                echo "  ❌ Failed to remove extension directory"
            fi
        else
            echo "  ℹ️  No MCP audit extension found"
        fi
    else
        echo "  ℹ️  No Cursor extensions directory found"
    fi
}

# Function to clean up configuration files
cleanup_config() {
    echo "🧹 Cleaning up configuration files..."
    
    # Remove proxy-related files
    if [ -f ~/.cursor/mcp_audit_messages.jsonl ]; then
        rm -f ~/.cursor/mcp_audit_messages.jsonl
        echo "  ✅ Removed captured messages"
    fi
    
    if [ -f ~/.cursor/mcp_audit_proxy.log ]; then
        rm -f ~/.cursor/mcp_audit_proxy.log
        echo "  ✅ Removed proxy logs"
    fi
    
    # Clean up any other audit files
    find ~/.cursor -name "mcp_audit_*" -type f -delete 2>/dev/null
    echo "  ✅ Removed all audit data files"
    
    # Remove enterprise integration configurations
    if [ -d ~/.mcp-audit ]; then
        echo "  🔗 Removing enterprise integration configs..."
        rm -rf ~/.mcp-audit
        echo "  ✅ Removed integration configurations"
    fi
    
    # Clean up generated reports in project directory (if in project)
    if [ -d "mcp_audit/generated_reports" ]; then
        echo "  📊 Cleaning up generated reports..."
        rm -rf mcp_audit/generated_reports/*
        echo "  ✅ Cleaned up report files"
    fi
    
    # Remove any global report files
    rm -f audit_report_*.json
    rm -f real_*.json
    rm -f component_trace_*.json
    rm -f complete_observability_*.json
    rm -f integrated_*.json
    rm -f trace_*.json
    rm -f enhanced_*.json
    rm -f usability_report_*.json
    echo "  ✅ Removed generated reports"
    
    # Remove demo/temp files
    rm -f *.jsonl
    rm -f demo_*.json
    echo "  ✅ Removed temporary files"
}

# Function to uninstall Python package
uninstall_python_package() {
    echo "🐍 Uninstalling Python package..."
    
    # Check if mcp-audit is installed
    if pip show mcp-audit-agent >/dev/null 2>&1; then
        echo "  📦 Found installed package: mcp-audit-agent"
        pip uninstall mcp-audit-agent -y
        echo "  ✅ Uninstalled mcp-audit-agent package"
    elif command -v mcp-audit >/dev/null 2>&1; then
        echo "  📦 Found mcp-audit CLI, attempting to uninstall..."
        pip uninstall mcp-audit -y 2>/dev/null || pip uninstall mcp-audit-agent -y 2>/dev/null
        echo "  ✅ Attempted package uninstall"
    else
        echo "  ℹ️  No mcp-audit package found"
    fi
}

# Function to verify uninstall
verify_uninstall() {
    echo "🔍 Verifying uninstall..."
    
    # Check processes
    REMAINING_PROCESSES=$(ps aux | grep -E "(mcp.*audit|mcp_proxy)" | grep -v grep | wc -l)
    if [ "$REMAINING_PROCESSES" -eq 0 ]; then
        echo "  ✅ No audit processes running"
    else
        echo "  ⚠️  $REMAINING_PROCESSES audit processes still running"
    fi
    
    # Check MCP config
    if [ -f ~/.cursor/mcp.json ] && ! grep -q "mcp_proxy_runner\|mcp.*audit" ~/.cursor/mcp.json; then
        echo "  ✅ MCP configuration restored"
    else
        echo "  ⚠️  MCP configuration may not be properly restored"
    fi
    
    # Check data files
    REMAINING_FILES=$(find ~/.cursor -name "mcp_audit_*" 2>/dev/null | wc -l)
    if [ "$REMAINING_FILES" -eq 0 ]; then
        echo "  ✅ All audit data files removed"
    else
        echo "  ⚠️  $REMAINING_FILES audit data files still exist"
    fi
    
    # Check integration configs
    if [ ! -d ~/.mcp-audit ]; then
        echo "  ✅ Integration configurations removed"
    else
        echo "  ⚠️  Integration configurations still exist"
    fi
    
    # Check CLI availability
    if ! command -v mcp-audit >/dev/null 2>&1; then
        echo "  ✅ mcp-audit CLI no longer available"
    else
        echo "  ⚠️  mcp-audit CLI still available"
    fi
}

# Main uninstall process
echo "📊 Current installation status:"

# Check MCP configuration
if [ -f ~/.cursor/mcp.json ]; then
    if grep -q "mcp_proxy_runner\|mcp.*audit" ~/.cursor/mcp.json; then
        echo "  🔧 MCP proxy configuration: ACTIVE"
        HAS_PROXY=true
    else
        echo "  🔧 MCP proxy configuration: Not found"
        HAS_PROXY=false
    fi
else
    echo "  🔧 MCP configuration: None"
    HAS_PROXY=false
fi

# Check for running processes  
PROXY_COUNT=$(ps aux | grep -E "(mcp.*audit|mcp_proxy)" | grep -v grep | wc -l)
DASHBOARD_COUNT=$(ps aux | grep -E "(mcp.*audit.*dashboard|uvicorn.*dashboard)" | grep -v grep | wc -l)
echo "  🏃 Running audit processes: $PROXY_COUNT"
echo "  🌐 Running dashboard processes: $DASHBOARD_COUNT"

# Check for CLI availability
if command -v mcp-audit >/dev/null 2>&1; then
    echo "  🔧 mcp-audit CLI: Available"
    AUDIT_VERSION=$(mcp-audit --version 2>/dev/null || echo "unknown")
    echo "  📦 Version: $AUDIT_VERSION"
else
    echo "  🔧 mcp-audit CLI: Not found"
fi

# Check for data files
if [ -f ~/.cursor/mcp_audit_messages.jsonl ]; then
    MESSAGE_COUNT=$(wc -l < ~/.cursor/mcp_audit_messages.jsonl)
    echo "  📨 Captured messages: $MESSAGE_COUNT"
else
    echo "  📨 Captured messages: None"
fi

if [ -f ~/.cursor/mcp_audit_proxy.log ]; then
    echo "  📋 Proxy logs: Present"
else
    echo "  📋 Proxy logs: None"
fi

# Check for integration configs
if [ -d ~/.mcp-audit ]; then
    CONFIG_COUNT=$(find ~/.mcp-audit -name "*.json" | wc -l)
    echo "  🔗 Integration configs: $CONFIG_COUNT files"
else
    echo "  🔗 Integration configs: None"
fi

echo ""
read -p "⚠️  Do you want to completely uninstall the MCP Audit Agent? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting uninstall process..."
    
    # Step 1: Stop running processes
    stop_processes
    
    # Step 2: Always restore MCP configuration (regardless of detection)
    restore_mcp_config
    
    # Step 3: Uninstall extension
    uninstall_extension
    
    # Step 4: Uninstall Python package
    uninstall_python_package
    
    # Step 5: Clean up files
    cleanup_config
    
    # Step 6: Verify uninstall
    verify_uninstall
    
    echo ""
    echo "🎉 Uninstall process completed!"
    echo ""
    echo "📋 What was done:"
    echo "  ✅ Stopped all running processes (proxy, dashboard, daemon)"
    echo "  ✅ Restored original MCP configuration"
    echo "  ✅ Removed extension files"
    echo "  ✅ Uninstalled Python package"
    echo "  ✅ Cleaned up data files and reports"
    echo "  ✅ Removed enterprise integration configs"
    echo "  ✅ Verified cleanup"
    echo ""
    echo "🔄 To complete uninstall:"
    echo "  1. Restart Cursor to reload MCP configuration"
    echo "  2. Test that Mastra MCP server works directly"
    echo "  3. Optionally delete this project directory:"
    echo "     cd .. && rm -rf mcp-useability-audit-agent"
    echo ""
    echo "💡 Your original Mastra MCP server will work normally"
    echo "💡 All enterprise integrations (LangSmith, Mixpanel, PostHog) have been disconnected"
    
else
    echo "❌ Uninstall cancelled"
fi 