#!/usr/bin/env python3
"""
MCP Audit Daemon - Continuous background monitoring of MCP interactions
"""
import asyncio
import signal
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..core.audit_agent import MCPUsabilityAuditAgent
from ..interceptors.live_interceptor import LiveMCPInterceptor
from ..analyzers.cognitive_analyzer import CognitiveAnalyzer


class MCPAuditDaemon:
    """Background daemon for continuous MCP monitoring."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".mcp-audit" / "daemon.json"
        self.config = self._load_config()
        self.running = False
        
        # Initialize components
        self.agent = MCPUsabilityAuditAgent()
        self.interceptor = LiveMCPInterceptor()
        self.analyzer = CognitiveAnalyzer()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> dict:
        """Load daemon configuration."""
        default_config = {
            "monitoring": {
                "enabled": True,
                "hosts": ["cursor", "claude-desktop"],
                "servers": ["mastra", "filesystem"],
                "interval_seconds": 30
            },
            "analysis": {
                "enabled": True,
                "cognitive_load_threshold": 70.0,
                "report_interval_hours": 6,
                "auto_recommendations": True
            },
            "alerts": {
                "enabled": False,
                "webhook_url": None,
                "email": None,
                "high_cognitive_load_threshold": 80.0
            },
            "storage": {
                "data_retention_days": 30,
                "max_file_size_mb": 100,
                "compression": True
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                return {**default_config, **user_config}
        else:
            # Create default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down daemon...")
        self.running = False
    
    async def start(self):
        """Start the daemon."""
        print("🚀 Starting MCP Audit Daemon...")
        print(f"📁 Config: {self.config_path}")
        print(f"⚙️  Monitoring: {', '.join(self.config['monitoring']['hosts'])}")
        
        self.running = True
        
        # Start monitoring tasks
        tasks = []
        
        if self.config["monitoring"]["enabled"]:
            tasks.append(asyncio.create_task(self._monitoring_loop()))
        
        if self.config["analysis"]["enabled"]:
            tasks.append(asyncio.create_task(self._analysis_loop()))
        
        # Start status reporting
        tasks.append(asyncio.create_task(self._status_loop()))
        
        try:
            # Run until shutdown
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("📊 Daemon tasks cancelled")
        finally:
            print("🏁 MCP Audit Daemon stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        interval = self.config["monitoring"]["interval_seconds"]
        
        while self.running:
            try:
                # Detect active MCP processes
                active_hosts = await self.interceptor.detect_active_hosts()
                
                if active_hosts:
                    print(f"🔍 Monitoring {len(active_hosts)} active MCP hosts")
                    
                    # Capture recent interactions
                    for host in active_hosts:
                        await self.interceptor.capture_interactions(host)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _analysis_loop(self):
        """Periodic analysis loop."""
        interval_hours = self.config["analysis"]["report_interval_hours"]
        interval_seconds = interval_hours * 3600
        
        while self.running:
            try:
                print("🧠 Running cognitive load analysis...")
                
                # Load recent messages
                messages = await self.agent.load_recent_messages(hours=interval_hours)
                
                if messages:
                    # Analyze for each monitored server
                    for server in self.config["monitoring"]["servers"]:
                        server_messages = [m for m in messages if server in str(m)]
                        
                        if server_messages:
                            analysis = await self.analyzer.analyze_cognitive_load(
                                server_messages, server
                            )
                            
                            # Check thresholds
                            threshold = self.config["analysis"]["cognitive_load_threshold"]
                            if analysis.overall_score > threshold:
                                await self._handle_high_cognitive_load(server, analysis)
                            
                            # Auto-generate recommendations
                            if self.config["analysis"]["auto_recommendations"]:
                                await self._generate_recommendations(server, analysis)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                print(f"❌ Analysis error: {e}")
                await asyncio.sleep(60)  # Wait longer on analysis errors
    
    async def _status_loop(self):
        """Status reporting loop."""
        while self.running:
            try:
                # Report status every 5 minutes
                await asyncio.sleep(300)
                
                if self.running:  # Check if still running
                    status = await self._get_daemon_status()
                    print(f"💓 Daemon Status: {status['uptime']}, Messages: {status['total_messages']}")
                
            except Exception as e:
                print(f"❌ Status error: {e}")
    
    async def _handle_high_cognitive_load(self, server: str, analysis):
        """Handle high cognitive load alerts."""
        print(f"⚠️  HIGH COGNITIVE LOAD detected for {server}: {analysis.overall_score:.1f}")
        
        if self.config["alerts"]["enabled"]:
            alert_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "server": server,
                "cognitive_load": analysis.overall_score,
                "threshold": self.config["analysis"]["cognitive_load_threshold"],
                "recommendations": analysis.recommendations[:3]  # Top 3
            }
            
            # Send webhook alert
            if self.config["alerts"]["webhook_url"]:
                await self._send_webhook_alert(alert_data)
    
    async def _generate_recommendations(self, server: str, analysis):
        """Generate and save recommendations."""
        recommendations_dir = Path.home() / ".mcp-audit" / "recommendations"
        recommendations_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = recommendations_dir / f"{server}_recommendations_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "server": server,
                "timestamp": datetime.utcnow().isoformat(),
                "cognitive_load": analysis.overall_score,
                "recommendations": analysis.recommendations
            }, f, indent=2)
    
    async def _send_webhook_alert(self, alert_data: dict):
        """Send webhook alert for high cognitive load."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.config["alerts"]["webhook_url"],
                    json=alert_data,
                    headers={"Content-Type": "application/json"}
                )
            print("📨 Alert sent via webhook")
        except Exception as e:
            print(f"❌ Failed to send webhook alert: {e}")
    
    async def _get_daemon_status(self) -> dict:
        """Get current daemon status."""
        # Count captured messages
        messages_file = Path.home() / ".cursor" / "mcp_audit_messages.jsonl"
        total_messages = 0
        
        if messages_file.exists():
            with open(messages_file, 'r') as f:
                total_messages = sum(1 for _ in f)
        
        return {
            "running": self.running,
            "uptime": "active",
            "total_messages": total_messages,
            "config_path": str(self.config_path),
            "monitoring_enabled": self.config["monitoring"]["enabled"],
            "analysis_enabled": self.config["analysis"]["enabled"]
        }


def main():
    """Main entry point for the daemon CLI."""
    import asyncio
    import click
    
    @click.group()
    def daemon_cli():
        """MCP Audit Daemon - Background monitoring service."""
        pass
    
    @daemon_cli.command()
    def start():
        """Start the daemon."""
        click.echo("🚀 Starting MCP Audit Daemon...")
        daemon = MCPAuditDaemon()
        asyncio.run(daemon.start())
    
    @daemon_cli.command()
    def stop():
        """Stop the daemon."""
        click.echo("🛑 Stopping MCP Audit Daemon...")
        daemon = MCPAuditDaemon()
        asyncio.run(daemon.stop())
    
    @daemon_cli.command()
    def status():
        """Check daemon status."""
        click.echo("📊 MCP Audit Daemon Status")
        daemon = MCPAuditDaemon()
        asyncio.run(daemon.get_status())
    
    daemon_cli()


if __name__ == "__main__":
    main() 