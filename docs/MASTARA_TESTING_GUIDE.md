# 🧪 Testing MCP Audit Agent with Mastara.ai Docs Server

Perfect choice for real-world testing! Documentation servers often reveal interesting cognitive patterns.

## 🎯 Pre-Test Setup

### 1. Install the Plugin First
```bash
cd cursor-plugin
./install.sh
# Restart Cursor
```

### 2. Verify Mastara.ai Integration
- Ensure Mastara.ai docs server is configured in Cursor
- Test basic docs queries work before starting audit
- Check MCP server connection status

### 3. Configure Audit Agent for Docs Testing
```json
// In Cursor Settings or ~/.mcp_audit/config.json
{
  "reportsDirectory": "./mastara_audit_reports",
  "retentionDays": 7,
  "cognitiveLoadThreshold": 70,
  "debugMode": true,  // For detailed logs during testing
  "anonymizeData": false  // To see actual query patterns
}
```

## 🧪 Testing Scenarios

### Scenario 1: Simple Documentation Queries
**Goal**: Baseline cognitive load measurement

**Test queries**:
```
1. "How do I authenticate with the API?"
2. "Show me the rate limiting documentation"
3. "What are the available endpoints?"
4. "Explain the error codes"
```

**Expected insights**:
- Low prompt complexity (simple questions)
- Low context switching (single domain)
- Should reveal parameter clarity issues if any

### Scenario 2: Complex Multi-Step Documentation Tasks
**Goal**: Measure context switching and integration cognition

**Test workflows**:
```
1. "Find authentication docs, then show me how to make my first API call"
2. "I need to implement webhooks - show setup, configuration, and testing"
3. "Help me troubleshoot a 401 error with step-by-step debugging"
4. "Compare different authentication methods and recommend one"
```

**Expected insights**:
- Higher context switching scores
- Integration cognition patterns
- Documentation organization effectiveness

### Scenario 3: Retry and Error Scenarios
**Goal**: Measure retry frustration and configuration friction

**Test patterns**:
```
1. Ask intentionally vague questions: "How does this work?"
2. Ask about non-existent features: "How do I use GraphQL subscriptions?"
3. Ask ambiguous questions: "What's the best way to optimize?"
4. Follow up with clarifying questions based on responses
```

**Expected insights**:
- Retry frustration when docs are unclear
- Configuration friction with ambiguous instructions
- Error recovery patterns

## 📊 What to Watch For

### Positive Indicators (Good Docs UX)
- **Low Cognitive Load (0-40)**: Questions get clear, direct answers
- **Low Retry Frustration (0-20)**: First answers are usually sufficient
- **Low Configuration Friction (0-30)**: Setup instructions are clear
- **High Success Rate**: Agent finds relevant docs quickly

### Red Flags (Poor Docs UX)
- **High Prompt Complexity (60+)**: Agent struggles to understand docs structure
- **High Context Switching (70+)**: Jumping between many different doc sections
- **High Retry Frustration (50+)**: Multiple attempts needed for satisfactory answers
- **High Configuration Friction (60+)**: Setup/auth instructions are confusing

### Interesting Patterns to Look For
- **Documentation Gaps**: High retry rates on specific topics
- **Structure Issues**: High context switching suggests poor organization
- **Language Problems**: High prompt complexity might indicate jargon/complexity
- **Missing Examples**: High configuration friction often means lack of examples

## 🔍 Real-Time Monitoring

### During Testing - Watch These:

1. **Status Bar Indicator**:
   - `$(pulse) MCP Audit` = Actively capturing data ✅
   - `$(circle-outline) MCP Audit` = Not running ❌

2. **Output Panel** (`Ctrl+Shift+U` → "MCP Audit"):
   ```
   📊 Agent: tools/list called on mastara server
   📊 Agent: tools/call - search_docs(query="authentication")
   📊 Agent: Response received in 245ms
   📊 Agent: Cognitive load calculated: 45.2/100
   ```

3. **Real-Time Dashboard** (`Ctrl+Shift+P` → "MCP Audit: Open Dashboard"):
   - Live cognitive load scores
   - Interaction count
   - Performance trends

## 📋 Testing Checklist

### Phase 1: Basic Validation (5-10 minutes)
- [ ] Plugin shows active status
- [ ] Make 3-5 simple docs queries
- [ ] Check Output panel for trace capture
- [ ] Generate first report: `Ctrl+Shift+P` → "MCP Audit: Generate Report"

### Phase 2: Pattern Testing (15-20 minutes)
- [ ] Test each scenario above
- [ ] Vary query complexity
- [ ] Try follow-up questions
- [ ] Mix successful and unsuccessful queries

### Phase 3: Analysis (5 minutes)
- [ ] Generate comprehensive report
- [ ] Review cognitive load breakdown
- [ ] Check for detected issues
- [ ] Read recommendations

## 🎯 Expected Results for Mastara.ai

### Likely Good Scores
- **Prompt Complexity**: Should be low (20-40) for well-structured docs
- **Integration Cognition**: Should be low since it's a single docs domain

### Likely Challenge Areas
- **Context Switching**: Might be higher if docs are fragmented
- **Configuration Friction**: Common issue with API documentation
- **Retry Frustration**: Depends on completeness of examples

## 📊 Interpreting Your Results

### Sample Good Result
```json
{
  "overall_usability_score": 82.3,
  "cognitive_load": {
    "prompt_complexity": 28.5,      // ✅ Clear queries
    "context_switching": 35.2,      // ✅ Good organization  
    "retry_frustration": 15.8,      // ✅ Helpful responses
    "configuration_friction": 45.1, // 🟡 Room for improvement
    "integration_cognition": 22.3   // ✅ Single domain
  }
}
```

### Sample Poor Result
```json
{
  "overall_usability_score": 45.2,
  "cognitive_load": {
    "prompt_complexity": 72.1,      // 🔴 Complex/unclear docs
    "context_switching": 85.3,      // 🔴 Fragmented structure
    "retry_frustration": 68.7,      // 🔴 Incomplete answers
    "configuration_friction": 78.9, // 🔴 Poor setup docs
    "integration_cognition": 41.2   // 🟡 Moderate complexity
  }
}
```

## 🚀 Quick Start Commands

```bash
# 1. Start monitoring
# Ctrl+Shift+P → "MCP Audit: Start"

# 2. Test basic docs query in Cursor
"How do I authenticate with Mastara.ai API?"

# 3. Check output panel
# Ctrl+Shift+U → Select "MCP Audit"

# 4. Generate report after 5+ queries  
# Ctrl+Shift+P → "MCP Audit: Generate Report"

# 5. View dashboard for live metrics
# Ctrl+Shift+P → "MCP Audit: Open Dashboard"
```

## 💡 Pro Tips

1. **Test with Real Use Cases**: Use actual documentation tasks you'd normally do
2. **Compare Before/After**: Generate reports, improve docs, test again
3. **Share Results**: The Mastara.ai team would probably love this feedback!
4. **Try Different Question Styles**: Formal vs casual, detailed vs brief
5. **Test Error Scenarios**: See how well docs handle edge cases

## 🎉 Expected Insights

You'll likely discover:
- **🔍 Documentation blind spots** (high retry frustration areas)
- **📚 Structure optimization opportunities** (high context switching)
- **⚙️ Setup process friction points** (configuration issues)
- **💡 Language/clarity improvements** (prompt complexity patterns)
- **🎯 User journey optimization** (integration cognition insights)

---

**🧠 This will be fascinating! Documentation usability is often overlooked but crucial for developer experience. Your test will provide unique cognitive insights into how AI agents interact with docs.**

**Go for it and let me know what patterns you discover! 🚀** 