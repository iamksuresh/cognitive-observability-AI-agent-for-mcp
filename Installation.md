# 🚀 Team Setup Guide - MCP Audit Agent

## Internal Distribution Options

### Option A: Direct Git Installation (Fastest)

Team members can install directly from your repository:

```bash
# Install latest version
pip install git+https://github.com/NapthaAI/mcp-useability-audit-agent.git

# Install with all features
pip install "git+https://github.com/NapthaAI/mcp-useability-audit-agent.git[all]"

# Install specific branch/tag
pip install git+https://github.com/NapthaAI/mcp-useability-audit-agent.git@main
```

### Option B: Build and Share Wheel Files

```bash
# Build the package
python -m build

# Share the generated wheel
# dist/mcp_audit_agent-0.1.0-py3-none-any.whl

# Team installs from wheel
pip install mcp_audit_agent-0.1.0-py3-none-any.whl

# Fix PATH issue if commands not found (macOS common issue)
echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Option C: Internal PyPI Server (Enterprise)

```bash
# Upload to internal PyPI
twine upload --repository-url https://pypi.internal.company.com dist/*

# Team installs from internal PyPI
pip install -i https://pypi.internal.company.com mcp-audit-agent
```

## Quick Team Onboarding

### 1. Installation

```bash
# One-liner for team members
pip install "git+https://github.com/NapthaAI/mcp-useability-audit-agent.git[all]"

# If commands not found (macOS), add Python framework to PATH:
echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Verify Installation

```bash
# Check if tools are available
mcp-audit status
mcp-audit-daemon --help
```

### 3. Basic Usage

```bash
# Start monitoring (team's most common use case)
mcp-audit proxy

# Generate report (for managers/leads)  
mcp-audit report --output-file weekly_usability.json

# View dashboard (for debugging sessions)
mcp-audit dashboard --port 8000
```

## Development Setup

For team members who want to contribute:

```bash
# Clone and setup dev environment
git clone https://github.com/NapthaAI/mcp-useability-audit-agent.git
cd mcp-useability-audit-agent

# Install in development mode
pip install -e ".[dev,all]"

# Run tests
pytest

# Format code
black mcp_audit/
isort mcp_audit/
```

## Environment Variables

Team members should set these environment variables:

```bash
# Optional: Configure default settings
export MCP_AUDIT_HOST="cursor"
export MCP_AUDIT_PORT="3001"
export MCP_AUDIT_OUTPUT_DIR="./audit_reports"

# For integrations (optional)
export LANGSMITH_API_KEY="your-key"
export MIXPANEL_TOKEN="your-token"
export POSTHOG_API_KEY="your-key"
```

## Common Team Use Cases

### 1. QA Engineers
```bash
# Monitor during testing sessions
mcp-audit proxy --target-host cursor --save-interactions
```

### 2. Product Managers
```bash
# Generate weekly usability reports
mcp-audit report --analysis-window-hours 168 --output weekly_report.json
```

### 3. Developers
```bash
# Debug MCP performance issues
mcp-audit dashboard --debug-mode
```

### 4. DevOps/SRE
```bash
# Run as background service
mcp-audit-daemon --monitor-all-hosts
```

## Troubleshooting

### Common Issues

1. **"Command not found: mcp-audit"**
   ```bash
   # Check which Python is installing to
   which pip
   
   # Add Python framework bin to PATH (macOS)
   echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   
   # Alternative: Use full path
   /Library/Frameworks/Python.framework/Versions/3.12/bin/mcp-audit status
   ```

2. **Missing dependencies (watchdog, uvicorn)**
   ```bash
   # Ensure you have the latest wheel with all dependencies
   pip install --force-reinstall mcp_audit_agent-0.1.0-py3-none-any.whl
   ```

3. **Permission errors**
   ```bash
   # Install for user only
   pip install --user "git+https://github.com/NapthaAI/mcp-useability-audit-agent.git"
   ```

4. **Dependencies conflicts**
   ```bash
   # Use virtual environment
   python -m venv mcp-audit-env
   source mcp-audit-env/bin/activate  # Linux/Mac
   # mcp-audit-env\Scripts\activate  # Windows
   pip install "git+https://github.com/NapthaAI/mcp-useability-audit-agent.git[all]"
   ```

## Team Slack/Communication

### Useful Commands to Share

```bash
# Get system info for bug reports
mcp-audit info --system

# Generate shareable report
mcp-audit report --format json --output team_report_$(date +%Y%m%d).json

# Quick health check
mcp-audit status --all-hosts
```

### Sharing Reports

```bash
# Generate team-friendly report
mcp-audit report \
  --format markdown \
  --include-charts \
  --output README_weekly_metrics.md
```

### Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run MCP Audit
  run: |
    pip install "git+https://github.com/your-org/mcp-audit-agent.git"
    mcp-audit report --ci-mode --output audit_results.json
    
- name: Upload Audit Results
  uses: actions/upload-artifact@v3
  with:
    name: mcp-audit-results
    path: audit_results.json
```

## Support

- **Documentation**: See `README.md` for detailed feature documentation
- **Issues**: Report bugs in GitHub Issues
- **Slack**: `#mcp-audit-agent` channel
- **Leads**: @your-team-lead for escalations 