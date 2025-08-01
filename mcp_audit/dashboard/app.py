"""
FastAPI web dashboard for MCP audit monitoring.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..core.audit_agent import MCPUsabilityAuditAgent
from ..core.models import UsabilityReport, MCPMessageTrace
from ..integrations import LangSmithIntegration, MixpanelIntegration, PostHogIntegration


class DashboardApp:
    """Web dashboard application for MCP audit monitoring."""
    
    def __init__(self):
        self.app = FastAPI(title="MCP Audit Dashboard", version="0.1.0")
        self.audit_agent = MCPUsabilityAuditAgent()
        self.websocket_connections: List[WebSocket] = []
        self.integrations: Dict[str, Any] = {}
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup all dashboard routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard page."""
            return await self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_status():
            """Get current system status."""
            try:
                # Count captured messages
                messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
                message_count = 0
                if messages_file.exists():
                    with open(messages_file, 'r') as f:
                        message_count = sum(1 for _ in f)
                
                # Get recent activity
                recent_interactions = await self.audit_agent._load_proxy_interactions(hours_back=1)
                
                return {
                    "status": "running",
                    "total_messages": message_count,
                    "recent_activity": len(recent_interactions),
                    "integrations": {
                        "langsmith": "langsmith" in self.integrations,
                        "mixpanel": "mixpanel" in self.integrations,
                        "posthog": "posthog" in self.integrations
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/cognitive-metrics")
        async def get_cognitive_metrics():
            """Get current cognitive load metrics."""
            try:
                interactions = await self.audit_agent._load_proxy_interactions(hours_back=24)
                
                if not interactions:
                    return {
                        "cognitive_load": 0,
                        "usability_score": 0,
                        "message_count": 0,
                        "recommendations": []
                    }
                
                # Generate real-time analysis
                report = await self.audit_agent.generate_report(server_name=None, hours_back=24)
                
                return {
                    "cognitive_load": report.cognitive_load.overall_score,
                    "usability_score": report.overall_usability_score,
                    "grade": report.grade,
                    "message_count": len(interactions),
                    "breakdown": {
                        "prompt_complexity": report.cognitive_load.prompt_complexity,
                        "context_switching": report.cognitive_load.context_switching,
                        "retry_frustration": report.cognitive_load.retry_frustration,
                        "configuration_friction": report.cognitive_load.configuration_friction,
                        "integration_cognition": report.cognitive_load.integration_cognition
                    },
                    "recommendations": report.recommendations[:5],
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/recent-activity")
        async def get_recent_activity():
            """Get recent MCP activity."""
            try:
                interactions = await self.audit_agent._load_proxy_interactions(hours_back=6)
                
                # Group by hour for timeline
                activity_by_hour = {}
                for interaction in interactions[-50:]:  # Last 50 interactions
                    hour = interaction.start_time.replace(minute=0, second=0, microsecond=0)
                    hour_key = hour.isoformat()
                    
                    if hour_key not in activity_by_hour:
                        activity_by_hour[hour_key] = {
                            "timestamp": hour_key,
                            "interaction_count": 0,
                            "servers": set(),
                            "success_rate": []
                        }
                    
                    activity_by_hour[hour_key]["interaction_count"] += 1
                    activity_by_hour[hour_key]["servers"].add(interaction.server_name)
                    activity_by_hour[hour_key]["success_rate"].append(interaction.success)
                
                # Convert sets to lists and calculate success rates
                for data in activity_by_hour.values():
                    data["servers"] = list(data["servers"])
                    success_rate = sum(data["success_rate"]) / len(data["success_rate"]) * 100
                    data["success_rate"] = round(success_rate, 1)
                
                return {
                    "activity": list(activity_by_hour.values()),
                    "total_interactions": len(interactions)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/integrations/setup")
        async def setup_integration(integration_data: Dict[str, Any]):
            """Setup enterprise integrations."""
            try:
                integration_type = integration_data.get("type")
                api_key = integration_data.get("api_key")
                
                if integration_type == "langsmith":
                    project_name = integration_data.get("project_name", "mcp-audit")
                    integration = LangSmithIntegration(api_key, project_name)
                    
                elif integration_type == "mixpanel":
                    project_token = integration_data.get("project_token")
                    integration = MixpanelIntegration(api_key, project_token)
                    
                elif integration_type == "posthog":
                    host = integration_data.get("host", "https://app.posthog.com")
                    integration = PostHogIntegration(api_key, host)
                    
                else:
                    raise HTTPException(status_code=400, detail="Unsupported integration type")
                
                # Test connection
                if await integration.test_connection():
                    self.integrations[integration_type] = integration
                    return {"success": True, "message": f"{integration_type} integration configured"}
                else:
                    return {"success": False, "message": f"Failed to connect to {integration_type}"}
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/favicon.ico")
        async def favicon():
            """Return a simple favicon to prevent 404s."""
            return HTMLResponse(content="", status_code=204)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    await asyncio.sleep(5)
                    
                    # Get current metrics
                    metrics = await get_cognitive_metrics()
                    
                    await websocket.send_json({
                        "type": "metrics_update",
                        "data": metrics
                    })
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Audit Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #0f1419; color: #e6edf3; }
        .header { background: #161b22; padding: 1rem 2rem; border-bottom: 1px solid #30363d; }
        .header h1 { color: #7c3aed; font-size: 1.5rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.5rem; }
        .metric { text-align: center; }
        .metric-value { font-size: 2.5rem; font-weight: bold; color: #7c3aed; }
        .metric-label { color: #8b949e; margin-top: 0.5rem; }
        .status-good { color: #3fb950; }
        .status-warning { color: #d29922; }
        .status-error { color: #f85149; }
        .chart { height: 200px; background: #0d1117; border-radius: 4px; margin-top: 1rem; }
        .activity-item { padding: 0.5rem; border-bottom: 1px solid #30363d; }
        .timestamp { color: #8b949e; font-size: 0.875rem; }
        .loading { text-align: center; color: #8b949e; padding: 2rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 MCP Cognitive Observability Dashboard</h1>
        <p>Real-time monitoring of AI agent interactions</p>
    </div>
    
    <div class="container">
        <div class="grid">
            <div class="card metric">
                <div class="metric-value" id="cognitive-load">--</div>
                <div class="metric-label">Cognitive Load</div>
                <div id="cognitive-status" class="timestamp">Loading...</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value" id="usability-score">--</div>
                <div class="metric-label">Usability Score</div>
                <div id="usability-grade" class="timestamp">--</div>
            </div>
            
            <div class="card metric">
                <div class="metric-value" id="message-count">--</div>
                <div class="metric-label">Messages Captured</div>
                <div id="last-update" class="timestamp">--</div>
            </div>
            
            <div class="card">
                <h3>Cognitive Load Breakdown</h3>
                <div id="breakdown-chart" class="chart loading">Loading breakdown...</div>
            </div>
            
            <div class="card">
                <h3>Recent Activity</h3>
                <div id="activity-feed">
                    <div class="loading">Loading activity...</div>
                </div>
            </div>
            
            <div class="card">
                <h3>System Status</h3>
                <div id="system-status">
                    <div class="loading">Loading status...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${location.host}/ws`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update') {
                updateMetrics(data.data);
            }
        };
        
        function updateMetrics(metrics) {
            document.getElementById('cognitive-load').textContent = metrics.cognitive_load.toFixed(1);
            document.getElementById('usability-score').textContent = metrics.usability_score.toFixed(1);
            document.getElementById('message-count').textContent = metrics.message_count;
            document.getElementById('usability-grade').textContent = `Grade: ${metrics.grade}`;
            document.getElementById('last-update').textContent = `Updated: ${new Date().toLocaleTimeString()}`;
            
            // Update cognitive load status
            const cognitiveStatus = document.getElementById('cognitive-status');
            if (metrics.cognitive_load < 30) {
                cognitiveStatus.textContent = 'Excellent - Low friction';
                cognitiveStatus.className = 'status-good';
            } else if (metrics.cognitive_load < 70) {
                cognitiveStatus.textContent = 'Good - Moderate friction';
                cognitiveStatus.className = 'status-warning';
            } else {
                cognitiveStatus.textContent = 'High friction detected';
                cognitiveStatus.className = 'status-error';
            }
            
            // Update breakdown
            const breakdown = metrics.breakdown;
            document.getElementById('breakdown-chart').innerHTML = `
                <div style="padding: 1rem;">
                    <div>Prompt Complexity: ${breakdown.prompt_complexity}</div>
                    <div>Context Switching: ${breakdown.context_switching}</div>
                    <div>Retry Frustration: ${breakdown.retry_frustration}</div>
                    <div>Config Friction: ${breakdown.configuration_friction}</div>
                    <div>Integration Cognition: ${breakdown.integration_cognition}</div>
                </div>
            `;
        }
        
        // Initial load
        fetch('/api/cognitive-metrics')
            .then(response => response.json())
            .then(data => updateMetrics(data))
            .catch(error => console.error('Error:', error));
        
        // Load system status
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('system-status').innerHTML = `
                    <div>Status: <span class="status-good">${data.status}</span></div>
                    <div>Total Messages: ${data.total_messages}</div>
                    <div>Recent Activity: ${data.recent_activity}</div>
                    <div>Integrations: ${Object.keys(data.integrations).filter(k => data.integrations[k]).join(', ') || 'None'}</div>
                `;
            });
        
        // Load recent activity
        fetch('/api/recent-activity')
            .then(response => response.json())
            .then(data => {
                const feed = document.getElementById('activity-feed');
                feed.innerHTML = data.activity.slice(-10).map(item => `
                    <div class="activity-item">
                        <div>${item.message_count} messages</div>
                        <div class="timestamp">${new Date(item.timestamp).toLocaleTimeString()}</div>
                    </div>
                `).join('');
            });
    </script>
</body>
</html>
        """
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected websockets."""
        if self.websocket_connections:
            message = json.dumps(data)
            for websocket in self.websocket_connections[:]:
                try:
                    await websocket.send_text(message)
                except:
                    self.websocket_connections.remove(websocket)


def create_dashboard_app() -> FastAPI:
    """Create and configure the dashboard application."""
    dashboard = DashboardApp()
    return dashboard.app 


def main():
    """Main entry point for dashboard command."""
    import uvicorn
    
    app = create_dashboard_app()
    
    print("🧠 MCP Audit Dashboard")
    print("🚀 Starting at http://127.0.0.1:8000")
    print("📊 Real-time cognitive observability")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main() 