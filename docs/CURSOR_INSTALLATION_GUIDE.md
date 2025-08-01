# 🚀 MCP Usability Audit Agent - Cursor Installation Guide

Complete step-by-step guide to install and use the MCP Usability Audit Agent plugin in Cursor IDE.

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Cursor IDE** installed ([cursor.sh](https://cursor.sh))
- [ ] **Node.js 18+** ([nodejs.org](https://nodejs.org))
- [ ] **Python 3.9+** with pip
- [ ] **MCP environment** set up in Cursor (with at least one MCP server)
- [ ] **Terminal access** (bash/zsh for macOS/Linux, or PowerShell for Windows)

## 🛠️ Installation Steps

### Step 1: Navigate to Plugin Directory

```bash
cd mcp-useability-audit-agent/cursor-plugin
```

### Step 2: Run Automatic Installation

**For macOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

**For Windows (PowerShell):**
```powershell
# Manual installation required - see step 3
```

### Step 3: Manual Installation (if automatic fails)

If the automatic installation doesn't work, follow these manual steps:

#### 3.1 Install Node.js Dependencies
```bash
npm install
```

#### 3.2 Install Python Audit Agent
```bash
cd ..
# Create/activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
cd cursor-plugin
```

#### 3.3 Build the Extension
```bash
npm run compile
npx vsce package
```

#### 3.4 Install Extension in Cursor
1. Open Cursor IDE
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type: **"Extensions: Install from VSIX"**
4. Select the generated `.vsix` file in the cursor-plugin directory
5. Click **"Install"**
6. **Restart Cursor**

## 🎯 Verification Steps

### Step 1: Check Extension Installation

1. Open Cursor IDE
2. Look for the status bar indicator at the bottom right: `$(pulse) MCP Audit` or `$(circle-outline) MCP Audit`
3. If you see it, the plugin is installed correctly! ✅

### Step 2: Verify Commands

1. Press `Ctrl+Shift+P` to open Command Palette
2. Type "MCP Audit" - you should see these commands:
   - ✅ **MCP Audit: Start**
   - ✅ **MCP Audit: Stop** 
   - ✅ **MCP Audit: Show Status**
   - ✅ **MCP Audit: Generate Report**
   - ✅ **MCP Audit: Open Dashboard**
   - ✅ **MCP Audit: View Live Traces**

### Step 3: Test Basic Functionality

1. Run command: **"MCP Audit: Start"**
2. Check the Output panel:
   - Open Output panel: `Ctrl+Shift+U`
   - Select "MCP Audit" from the dropdown
   - Look for: `✅ MCP Audit Agent started successfully`

## 🚀 First Usage

### Starting Monitoring

**Option 1: Auto-start (Recommended)**
- The agent starts automatically when Cursor launches
- No action needed! 🎉

**Option 2: Manual start**
1. Press `Ctrl+Shift+P`
2. Run: **"MCP Audit: Start"**
3. Look for the green pulse indicator: `$(pulse) MCP Audit`

### Generating Your First Report

1. Use Cursor with MCP tools for a few minutes (to generate data)
2. Press `Ctrl+Shift+P`
3. Run: **"MCP Audit: Generate Report"**
4. Check the `./audit_reports` folder for your report!

### Viewing the Dashboard

1. Press `Ctrl+Shift+P`
2. Run: **"MCP Audit: Open Dashboard"**
3. See real-time metrics and insights

## ⚙️ Configuration

### Quick Settings

Open Cursor Settings (`Ctrl+,`) and search for **"MCP Audit"**:

| Setting | Recommended Value | Description |
|---------|------------------|-------------|
| **Auto Start** | ✅ Enabled | Start monitoring automatically |
| **Reports Directory** | `./audit_reports` | Where to save reports |
| **Cognitive Load Threshold** | `80` | Alert threshold (0-100) |
| **Real-time Alerts** | ✅ Enabled | Show performance alerts |

### Advanced Configuration

Create `~/.mcp_audit/config.json`:

```json
{
  "autoStart": true,
  "reportsDirectory": "./audit_reports",
  "retentionDays": 30,
  "reportFrequency": "daily",
  "cognitiveLoadThreshold": 80,
  "anonymizeData": true,
  "enableRealTimeAlerts": true,
  "debugMode": false
}
```

## 📊 Understanding Your Reports

### Cognitive Load Metrics (0-100 scale)

- **📝 Prompt Complexity**: How hard requests are to understand
- **🔄 Context Switching**: How often you must reorient
- **😤 Retry Frustration**: Struggle before achieving success  
- **⚙️ Configuration Friction**: Difficulty in initial setup
- **🔗 Integration Cognition**: How well tools work together

### Report Locations

- **Default location**: `./audit_reports/`
- **File formats**: JSON, HTML, TXT
- **Naming**: `audit_report_YYYYMMDD_HHMMSS.json`

### Sample Good vs Bad Scores

| Metric | Good (🟢) | Okay (🟡) | Poor (🔴) |
|--------|-----------|-----------|-----------|
| Overall Usability | 80-100 | 60-79 | 0-59 |
| Cognitive Load | 0-40 | 41-70 | 71-100 |
| Prompt Complexity | 0-30 | 31-60 | 61-100 |
| Retry Frustration | 0-20 | 21-50 | 51-100 |

## 🔧 Troubleshooting

### ❌ Plugin Not Appearing

**Check installation:**
```bash
# Verify extension is installed
ls *.vsix  # Should show .vsix file
```

**Reinstall if needed:**
1. In Cursor: `Ctrl+Shift+P` → "Extensions: Show Installed Extensions"
2. Find "MCP Usability Audit Agent" and uninstall
3. Run installation steps again

### ❌ "Failed to start monitoring"

**Check MCP setup:**
1. Verify MCP servers are configured in Cursor
2. Test MCP functionality independently
3. Check Output panel for detailed errors

**Check Python environment:**
```bash
# Verify Python agent is installed
cd mcp-useability-audit-agent
source .venv/bin/activate  # If using venv
mcp-audit --help
```

### ❌ No data in reports

**Generate MCP activity:**
1. Use MCP tools in Cursor (e.g., weather queries, code analysis)
2. Wait for some interactions to be captured
3. Try generating report again

**Check permissions:**
```bash
# Ensure write access to reports directory
mkdir -p ./audit_reports
touch ./audit_reports/test.txt
rm ./audit_reports/test.txt
```

### ❌ High CPU/Memory usage

**Optimize settings:**
1. Lower retention period: `mcpAudit.retentionDays = 7`
2. Reduce max traces: `mcpAudit.maxTraces = 1000`
3. Enable anonymization: `mcpAudit.anonymizeData = true`

## 📋 Daily Usage Tips

### Best Practices

1. **Let it run automatically** - Keep auto-start enabled
2. **Review reports weekly** - Generate reports periodically
3. **Check the dashboard** - Monitor real-time metrics
4. **Act on insights** - Use recommendations to improve workflows

### Useful Workflows

**Performance Investigation:**
1. Notice high cognitive load alert
2. Open dashboard to see current metrics
3. Generate detailed report
4. Review recommendations
5. Make improvements

**Regular Health Check:**
1. Weekly: Generate comprehensive report
2. Review overall usability trends
3. Check for new issues or improvements
4. Share insights with team

## 🎉 Success!

You now have the MCP Usability Audit Agent running in Cursor! 

### What's happening:

- 👁️ **Silent monitoring** of all your MCP interactions
- 📊 **Cognitive load analysis** in real-time
- 📋 **Automatic report generation** (if configured)
- 🎯 **Zero impact** on your normal workflow

### Next steps:

1. **Use Cursor normally** with MCP tools
2. **Check status** occasionally via the status bar
3. **Generate reports** to see insights
4. **Optimize** based on recommendations

---

## 🆘 Need Help?

- 📖 **Documentation**: [Main README](README.md)
- 🐛 **Issues**: Create GitHub issue with logs
- 💬 **Questions**: Check existing issues first

**🧠 Happy cognitive observability!** 