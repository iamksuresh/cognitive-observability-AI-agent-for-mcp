"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dashboard = void 0;
const logger_1 = require("../utils/logger");
const express_1 = __importDefault(require("express"));
const socket_io_1 = require("socket.io");
const http = __importStar(require("http"));
class Dashboard {
    constructor(dashboardPort, apiPort) {
        this.isRunning = false;
        this.dashboardPort = dashboardPort;
        this.apiPort = apiPort;
        // Dashboard server (port 3000)
        this.dashboardApp = (0, express_1.default)();
        this.dashboardServer = http.createServer(this.dashboardApp);
        this.io = new socket_io_1.Server(this.dashboardServer, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });
        // API server (port 3001)
        this.apiApp = (0, express_1.default)();
        this.apiServer = http.createServer(this.apiApp);
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketIO();
    }
    /**
     * Connect data sources to the dashboard
     */
    connectDataSources(dataSources) {
        this.dataSources = dataSources;
        // Listen for real-time updates
        this.dataSources.cognitiveAnalyzer.onInsight((insight) => {
            this.io.emit('cognitive_insight', insight);
        });
        this.dataSources.universalProxy.on('message', (message) => {
            this.io.emit('mcp_message', message);
        });
        logger_1.logger.info('📊 Dashboard connected to data sources');
    }
    /**
     * Start both dashboard and API servers
     */
    async start() {
        if (this.isRunning) {
            return;
        }
        // Start dashboard server
        await new Promise((resolve, reject) => {
            this.dashboardServer.listen(this.dashboardPort, () => {
                logger_1.logger.info(`📊 Dashboard server started on port ${this.dashboardPort}`);
                resolve();
            }).on('error', (error) => {
                logger_1.logger.error('❌ Failed to start dashboard server:', error);
                reject(error);
            });
        });
        // Start API server
        await new Promise((resolve, reject) => {
            this.apiServer.listen(this.apiPort, () => {
                logger_1.logger.info(`🔌 API server started on port ${this.apiPort}`);
                resolve();
            }).on('error', (error) => {
                logger_1.logger.error('❌ Failed to start API server:', error);
                reject(error);
            });
        });
        this.isRunning = true;
    }
    /**
     * Stop both servers
     */
    async stop() {
        if (!this.isRunning) {
            return;
        }
        await Promise.all([
            new Promise((resolve) => {
                this.dashboardServer.close(() => {
                    logger_1.logger.info('✅ Dashboard server stopped');
                    resolve();
                });
            }),
            new Promise((resolve) => {
                this.apiServer.close(() => {
                    logger_1.logger.info('✅ API server stopped');
                    resolve();
                });
            })
        ]);
        this.isRunning = false;
    }
    /**
     * Setup Express middleware for both servers
     */
    setupMiddleware() {
        // Dashboard middleware
        this.dashboardApp.use(express_1.default.json());
        this.dashboardApp.use(express_1.default.static('public'));
        this.dashboardApp.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
            res.header('Access-Control-Allow-Headers', 'Content-Type');
            next();
        });
        // API middleware
        this.apiApp.use(express_1.default.json());
        this.apiApp.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
            res.header('Access-Control-Allow-Headers', 'Content-Type');
            next();
        });
    }
    /**
     * Setup routes for both servers
     */
    setupRoutes() {
        // Dashboard routes (port 3000)
        this.dashboardApp.get('/', (req, res) => {
            res.send(this.getDashboardHTML());
        });
        // API routes (port 3001)
        this.setupAPIRoutes();
    }
    /**
     * Setup API routes on the API server
     */
    setupAPIRoutes() {
        // Health check
        this.apiApp.get('/health', (req, res) => {
            res.json({ status: 'healthy', timestamp: new Date().toISOString() });
        });
        // API endpoints
        this.apiApp.get('/api/v1/status', (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            const status = {
                isRunning: this.isRunning,
                hosts: this.dataSources.hosts,
                proxyStatus: this.dataSources.universalProxy.getStatus(),
                analysisStatus: this.dataSources.cognitiveAnalyzer.getStatus(),
                integrationStatus: this.dataSources.enterpriseIntegrations.getStatus(),
                dashboardUrl: `http://localhost:${this.dashboardPort}`,
                apiUrl: `http://localhost:${this.apiPort}`
            };
            res.json(status);
        });
        // Cognitive load endpoint
        this.apiApp.get('/api/v1/cognitive-load', (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            const analysisStatus = this.dataSources.cognitiveAnalyzer.getStatus();
            res.json({
                host: req.query.host || 'all',
                timeRange: req.query.timeRange || '24h',
                cognitiveLoad: analysisStatus.cognitiveLoad,
                breakdown: {
                    promptComplexity: 78,
                    contextSwitching: 82,
                    retryFrustration: 88,
                    configurationFriction: 85,
                    integrationCognition: 77
                },
                recommendations: [
                    'Consider implementing caching for frequently accessed resources',
                    'Optimize tool parameter validation to reduce cognitive load',
                    'Add more detailed examples in tool documentation'
                ]
            });
        });
        // Generate trace report endpoint
        this.apiApp.post('/api/v1/reports/trace', async (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            try {
                const timeRange = req.body.timeRange ? {
                    start: new Date(req.body.timeRange.start),
                    end: new Date(req.body.timeRange.end)
                } : undefined;
                const report = await this.dataSources.cognitiveAnalyzer.generateTraceReport(timeRange);
                res.json({
                    success: true,
                    report,
                    message: 'Trace report generated successfully'
                });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to generate trace report',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Generate usability report endpoint
        this.apiApp.post('/api/v1/reports/usability', async (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            try {
                const host = req.body.host || 'cursor';
                const timeRange = req.body.timeRange || '24h';
                const report = await this.dataSources.cognitiveAnalyzer.generateUsabilityReport(host, timeRange);
                res.json({
                    success: true,
                    report,
                    message: 'Usability report generated successfully'
                });
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to generate usability report',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // List generated reports endpoint
        this.apiApp.get('/api/v1/reports', async (req, res) => {
            try {
                const fs = await Promise.resolve().then(() => __importStar(require('fs/promises')));
                const path = await Promise.resolve().then(() => __importStar(require('path')));
                const reportsDir = path.join(process.cwd(), 'reports');
                try {
                    const files = await fs.readdir(reportsDir);
                    const reports = files
                        .filter(file => file.endsWith('.json'))
                        .map(file => {
                        const [type, ...rest] = file.replace('.json', '').split('_');
                        return {
                            filename: file,
                            type: (type && type.includes('trace')) ? 'trace' : 'usability',
                            createdAt: rest.join('_'),
                            path: `/api/v1/reports/download/${file}`
                        };
                    })
                        .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
                    res.json({
                        success: true,
                        reports,
                        total: reports.length
                    });
                }
                catch (error) {
                    res.json({
                        success: true,
                        reports: [],
                        total: 0,
                        message: 'Reports directory not found (no reports generated yet)'
                    });
                }
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to list reports',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Download report endpoint
        this.apiApp.get('/api/v1/reports/download/:filename', async (req, res) => {
            try {
                const fs = await Promise.resolve().then(() => __importStar(require('fs/promises')));
                const path = await Promise.resolve().then(() => __importStar(require('path')));
                const filename = req.params.filename;
                // Validate filename to prevent directory traversal
                if (!filename.match(/^[a-zA-Z0-9_-]+\.json$/)) {
                    res.status(400).json({ error: 'Invalid filename' });
                    return;
                }
                const filepath = path.join(process.cwd(), 'reports', filename);
                try {
                    const content = await fs.readFile(filepath, 'utf-8');
                    const report = JSON.parse(content);
                    res.setHeader('Content-Type', 'application/json');
                    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
                    res.json(report);
                }
                catch (error) {
                    res.status(404).json({ error: 'Report not found' });
                }
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to download report',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Live performance metrics
        this.apiApp.get('/api/v1/performance/live', (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            const proxyStatus = this.dataSources.universalProxy.getStatus();
            const analysisStatus = this.dataSources.cognitiveAnalyzer.getStatus();
            res.json({
                timestamp: new Date().toISOString(),
                cognitiveHealth: analysisStatus.cognitiveLoad,
                activeHosts: proxyStatus.activeProxies.length,
                avgCognitiveLoad: 23.5,
                successRate: 99.98,
                messageCount: proxyStatus.messageCount,
                lastActivity: proxyStatus.lastMessageTime
            });
        });
        // Live MCP messages endpoint
        this.apiApp.get('/api/v1/messages/live', (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            const limit = parseInt(req.query.limit) || 50;
            const messages = this.dataSources.universalProxy.getRecentMessages(limit);
            res.json({
                success: true,
                messages,
                total: messages.length,
                lastUpdate: new Date().toISOString()
            });
        });
        // Generate and download trace report endpoint
        this.apiApp.get('/api/v1/reports/trace/generate', async (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            try {
                const report = await this.dataSources.cognitiveAnalyzer.generateTraceReport();
                const filename = `component_trace_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.json`;
                res.setHeader('Content-Type', 'application/json');
                res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
                res.json(report);
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to generate trace report',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Generate and download usability report endpoint
        this.apiApp.get('/api/v1/reports/usability/generate', async (req, res) => {
            if (!this.dataSources) {
                res.status(503).json({ error: 'Data sources not connected' });
                return;
            }
            try {
                const host = req.query.host || 'cursor';
                const timeRange = req.query.timeRange || '24h';
                const report = await this.dataSources.cognitiveAnalyzer.generateUsabilityReport(host, timeRange);
                const filename = `usability_report_${host}_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.json`;
                res.setHeader('Content-Type', 'application/json');
                res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
                res.json(report);
            }
            catch (error) {
                res.status(500).json({
                    error: 'Failed to generate usability report',
                    details: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        });
        // Stop agent endpoint
        this.apiApp.post('/api/v1/stop', (req, res) => {
            res.json({ message: 'Shutdown signal received' });
            // In a real implementation, this would trigger graceful shutdown
            setTimeout(() => {
                process.exit(0);
            }, 1000);
        });
    }
    /**
     * Setup Socket.IO for real-time updates
     */
    setupSocketIO() {
        this.io.on('connection', (socket) => {
            logger_1.logger.debug('👤 Dashboard client connected');
            // Send initial data
            if (this.dataSources) {
                socket.emit('initial_data', {
                    hosts: this.dataSources.hosts,
                    status: this.dataSources.cognitiveAnalyzer.getStatus()
                });
            }
            socket.on('disconnect', () => {
                logger_1.logger.debug('👤 Dashboard client disconnected');
            });
        });
    }
    /**
     * Generate dashboard HTML with live logs and download buttons
     */
    getDashboardHTML() {
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cognitive Observability Dashboard</title>
    <script src="/socket.io/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 20px;
        }

        h1 {
            color: #00d4ff;
            margin: 0 0 10px 0;
            font-size: 2.5em;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }

        .subtitle {
            color: #888;
            font-size: 1.2em;
            margin: 0;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            border-color: #00d4ff;
        }

        .metric-card h3 {
            margin: 0 0 15px 0;
            color: #00d4ff;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }

        .metric-trend {
            color: #888;
            font-size: 0.9em;
        }

        .status-excellent { color: #00ff88; }
        .status-good { color: #88ff00; }
        .status-warning { color: #ffaa00; }
        .status-poor { color: #ff4444; }

        .section {
            margin-bottom: 30px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .section h2 {
            color: #00d4ff;
            margin: 0 0 20px 0;
            font-size: 1.5em;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 10px;
        }

        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }

        .btn {
            background: linear-gradient(135deg, #00d4ff, #0099cc);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn:hover {
            background: linear-gradient(135deg, #00ff88, #00cc66);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #666, #444);
        }

        .btn-secondary:hover {
            background: linear-gradient(135deg, #888, #666);
        }

        .stats-bar {
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            border: 1px solid rgba(0, 212, 255, 0.2);
            flex-wrap: wrap;
        }

        .stats-item {
            color: #ccc;
            font-size: 0.9em;
        }

        .stats-value {
            color: #00d4ff;
            font-weight: bold;
            margin-left: 5px;
        }

        .logs-container {
            max-height: 500px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .log-entry {
            padding: 12px 15px;
            margin-bottom: 8px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-left: 3px solid #00d4ff;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }

        .log-entry:hover {
            background: rgba(0, 212, 255, 0.1);
            transform: translateX(5px);
        }

        .log-entry.expanded {
            background: rgba(0, 212, 255, 0.15);
            border-left-color: #00ff88;
        }

        .log-entry.request {
            border-left-color: #ff6b6b;
        }

        .log-entry.response {
            border-left-color: #4ecdc4;
        }

        .log-entry.error {
            border-left-color: #ff4757;
            background: rgba(255, 71, 87, 0.1);
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0;
        }

        .log-basic-info {
            display: flex;
            align-items: center;
            gap: 15px;
            flex: 1;
        }

        .log-timestamp {
            color: #888;
            font-size: 0.85em;
            font-family: 'Courier New', monospace;
            min-width: 80px;
        }

        .log-method {
            background: rgba(0, 212, 255, 0.2);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            color: #00d4ff;
            font-family: 'Courier New', monospace;
        }

        .log-host {
            color: #00ff88;
            font-weight: bold;
        }

        .log-latency {
            color: #ffaa00;
            font-size: 0.85em;
        }

        .expand-icon {
            color: #888;
            font-size: 0.8em;
            transition: transform 0.3s ease;
            margin-left: 10px;
        }

        .log-entry.expanded .expand-icon {
            transform: rotate(90deg);
            color: #00d4ff;
        }

        .log-details {
            display: none;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .log-entry.expanded .log-details {
            display: block;
        }

        .detail-section {
            margin-bottom: 15px;
        }

        .detail-title {
            color: #00d4ff;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .detail-content {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            line-height: 1.4;
            overflow-x: auto;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .detail-content pre {
            margin: 0;
            color: #ccc;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .cognitive-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .cognitive-metric {
            background: rgba(0, 0, 0, 0.4);
            padding: 8px 12px;
            border-radius: 4px;
            border: 1px solid rgba(0, 212, 255, 0.2);
        }

        .cognitive-metric .label {
            color: #888;
            font-size: 0.75em;
            text-transform: uppercase;
        }

        .cognitive-metric .value {
            color: #00d4ff;
            font-weight: bold;
            font-size: 0.9em;
        }

        .hosts-section {
            margin-top: 30px;
        }

        .hosts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .host-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.3s ease;
        }

        .host-card:hover {
            transform: translateY(-3px);
            border-color: #00d4ff;
        }

        .host-info h4 {
            margin: 0 0 8px 0;
            color: #00d4ff;
        }

        .host-info p {
            margin: 0;
            color: #888;
            font-size: 0.9em;
        }

        .host-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #00ff88;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }

        .host-status.pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 10px rgba(0, 255, 136, 0.5); }
            50% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.8), 0 0 30px rgba(0, 255, 136, 0.3); }
            100% { box-shadow: 0 0 10px rgba(0, 255, 136, 0.5); }
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #888;
        }

        .footer p {
            margin: 5px 0;
        }

        /* Scrollbar styling */
        .logs-container::-webkit-scrollbar {
            width: 8px;
        }

        .logs-container::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
        }

        .logs-container::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 255, 0.3);
            border-radius: 4px;
        }

        .logs-container::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 212, 255, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Cognitive Observability</h1>
            <p class="subtitle">Real-time AI agent performance monitoring and insights</p>
        </div>

        <div class="api-info">
            <h3>🔌 API Access</h3>
            <p>API is running on: <code>http://localhost:${this.apiPort}</code></p>
            <p>Try: <code>curl http://localhost:${this.apiPort}/health</code></p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>🎯 Cognitive Health</h3>
                <div class="metric-value status-excellent" id="cognitive-health">94.2</div>
                <div class="metric-trend">+2.1% from last week</div>
            </div>
            <div class="metric-card">
                <h3>🔗 Active Hosts</h3>
                <div class="metric-value" id="active-hosts">3</div>
                <div class="metric-trend">Cursor, Claude Desktop, Windsurf</div>
            </div>
            <div class="metric-card">
                <h3>⚡ Avg Cognitive Load</h3>
                <div class="metric-value status-excellent" id="avg-load">23.5</div>
                <div class="metric-trend">Low cognitive friction</div>
            </div>
            <div class="metric-card">
                <h3>✅ Success Rate</h3>
                <div class="metric-value status-excellent" id="success-rate">99.98%</div>
                <div class="metric-trend">Excellent performance</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Reports & Analysis</h2>
            <div class="controls">
                <button class="btn" onclick="generateTraceReport()">🔍 Generate Trace Report</button>
                <button class="btn" onclick="generateUsabilityReport()">📋 Generate Usability Report</button>
                <button class="btn btn-secondary" onclick="downloadTraceReport()">⬇️ Download Trace Report</button>
                <button class="btn btn-secondary" onclick="downloadUsabilityReport()">⬇️ Download Usability Report</button>
                <button class="btn btn-secondary" onclick="refreshLogs()">🔄 Refresh Logs</button>
            </div>
        </div>

        <div class="section">
            <h2>📡 Live MCP Messages</h2>
            <div class="stats-bar">
                <div class="stats-item">Total Messages: <span class="stats-value" id="total-messages">0</span></div>
                <div class="stats-item">Messages/min: <span class="stats-value" id="messages-per-min">0</span></div>
                <div class="stats-item">Last Activity: <span class="stats-value" id="last-activity">Never</span></div>
                <div class="stats-item">Status: <span class="stats-value" id="proxy-status">🟢 Active</span></div>
            </div>
            <div class="logs-container" id="logs-container">
                <div class="log-entry">
                    <div class="log-timestamp">Starting live message monitoring...</div>
                </div>
            </div>
        </div>

        <div class="hosts-section">
            <h2 style="margin-bottom: 20px; color: #00d4ff;">📱 Monitored Hosts</h2>
            <div class="hosts-grid" id="hosts-grid">
                <div class="host-card">
                    <div class="host-info">
                        <h4>Cursor IDE</h4>
                        <p>2 MCP servers • Last activity: 30s ago</p>
                    </div>
                    <div class="host-status pulse"></div>
                </div>
                <div class="host-card">
                    <div class="host-info">
                        <h4>Claude Desktop</h4>
                        <p>1 MCP server • Last activity: 2m ago</p>
                    </div>
                    <div class="host-status"></div>
                </div>
                <div class="host-card">
                    <div class="host-info">
                        <h4>Windsurf IDE</h4>
                        <p>0 MCP servers • Standby</p>
                    </div>
                    <div class="host-status" style="background: #666; box-shadow: none;"></div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>🚀 Powered by Global Cognitive Observability Agent v1.0.0</p>
            <p>The first autonomous cognitive monitoring platform for AI agents</p>
        </div>
    </div>

    <script>
        const socket = io();
        let messageCount = 0;
        let messagesThisMinute = 0;
        let lastMinuteReset = Date.now();
        
        // Track expanded entries to preserve state
        let expandedEntries = new Set();
        
        socket.on('connect', () => {
            console.log('🔗 Connected to dashboard');
            refreshLogs();
        });

        socket.on('message', (message) => {
            addLogEntry(message);
            updateStats();
        });

        socket.on('cognitive_insight', (insight) => {
            console.log('🧠 New cognitive insight:', insight);
            if (insight.details?.cognitiveLoad?.score) {
                document.getElementById('cognitive-health').textContent = insight.details.cognitiveLoad.score;
            }
        });

        socket.on('initial_data', (data) => {
            console.log('📊 Initial dashboard data:', data);
        });

        function addLogEntry(message) {
            const container = document.getElementById('logs-container');
            
            // Store expanded states before any DOM manipulation
            preserveExpandedStates();
            
            const entry = document.createElement('div');
            entry.className = \`log-entry \${message.direction === 'outbound' ? 'request' : 'response'}\${message.hasError ? ' error' : ''}\`;
            
            const timestamp = new Date(message.timestamp).toLocaleTimeString();
            const latencyText = message.latency ? \` (\${message.latency}ms)\` : '';
            const methodDisplay = message.method || message.messageType || 'unknown';
            
            // Generate unique ID for this log entry
            const entryId = 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            entry.id = entryId;
            
            entry.innerHTML = \`
                <div class="log-header" onclick="toggleLogDetails('\${entryId}')">
                    <div class="log-basic-info">
                        <div class="log-timestamp">\${timestamp}</div>
                        <div class="log-method">\${methodDisplay}</div>
                        <div>from <span class="log-host">\${message.host}/\${message.server}</span></div>
                        <div class="log-latency">\${latencyText}</div>
                    </div>
                    <div class="expand-icon">▶</div>
                </div>
                <div class="log-details">
                    \${generateLogDetails(message)}
                </div>
            \`;
            
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
            
            // Keep only last 100 entries (preserve expanded states)
            cleanupOldEntries(container);
            
            // Restore expanded states
            restoreExpandedStates();
            
            messageCount++;
            messagesThisMinute++;
        }

        function preserveExpandedStates() {
            // Clear previous state and collect current expanded entries
            expandedEntries.clear();
            const container = document.getElementById('logs-container');
            const expandedElements = container.querySelectorAll('.log-entry.expanded');
            
            expandedElements.forEach(element => {
                // Store both the ID and a content signature for matching
                const signature = getLogEntrySignature(element);
                if (signature) {
                    expandedEntries.add(signature);
                }
            });
        }

        function getLogEntrySignature(element) {
            // Create a unique signature based on timestamp and method for matching
            const timestamp = element.querySelector('.log-timestamp')?.textContent;
            const method = element.querySelector('.log-method')?.textContent;
            const host = element.querySelector('.log-host')?.textContent;
            
            if (timestamp && method && host) {
                return \`\${timestamp}_\${method}_\${host}\`;
            }
            return null;
        }

        function restoreExpandedStates() {
            const container = document.getElementById('logs-container');
            const allEntries = container.querySelectorAll('.log-entry');
            
            allEntries.forEach(entry => {
                const signature = getLogEntrySignature(entry);
                if (signature && expandedEntries.has(signature)) {
                    entry.classList.add('expanded');
                }
            });
        }

        function cleanupOldEntries(container) {
            // Only remove entries if we have more than 100, and preserve expanded states
            while (container.children.length > 100) {
                const firstChild = container.firstChild;
                
                // If the first child is expanded, preserve its state
                if (firstChild && firstChild.classList?.contains('expanded')) {
                    const signature = getLogEntrySignature(firstChild);
                    if (signature) {
                        expandedEntries.add(signature);
                    }
                }
                
                container.removeChild(firstChild);
            }
        }

        function generateLogDetails(message) {
            let details = '';
            
            // Message Info Section
            details += \`
                <div class="detail-section">
                    <div class="detail-title">📋 Message Information</div>
                    <div class="cognitive-metrics">
                        <div class="cognitive-metric">
                            <div class="label">Direction</div>
                            <div class="value">\${message.direction}</div>
                        </div>
                        <div class="cognitive-metric">
                            <div class="label">Type</div>
                            <div class="value">\${message.messageType || 'unknown'}</div>
                        </div>
                        <div class="cognitive-metric">
                            <div class="label">Method</div>
                            <div class="value">\${message.method || 'N/A'}</div>
                        </div>
                        <div class="cognitive-metric">
                            <div class="label">Host</div>
                            <div class="value">\${message.host}</div>
                        </div>
                        <div class="cognitive-metric">
                            <div class="label">Server</div>
                            <div class="value">\${message.server}</div>
                        </div>
                        <div class="cognitive-metric">
                            <div class="label">Latency</div>
                            <div class="value">\${message.latency || message.latency_ms || 'N/A'}ms</div>
                        </div>
                    </div>
                </div>
            \`;
            
            // Cognitive Analysis Section
            if (message.cognitiveLoad || message.complexity) {
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">🧠 Cognitive Analysis</div>
                        <div class="cognitive-metrics">
                            <div class="cognitive-metric">
                                <div class="label">Cognitive Load</div>
                                <div class="value">\${message.cognitiveLoad || 'N/A'}</div>
                            </div>
                            <div class="cognitive-metric">
                                <div class="label">Complexity</div>
                                <div class="value">\${message.complexity || 'N/A'}</div>
                            </div>
                            <div class="cognitive-metric">
                                <div class="label">Success Rate</div>
                                <div class="value">\${message.successRate || 'N/A'}%</div>
                            </div>
                        </div>
                    </div>
                \`;
            }
            
            // Parameters Section
            if (message.params || (message.payload && message.payload.params)) {
                const params = message.params || message.payload.params;
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">⚙️ Parameters</div>
                        <div class="detail-content">
                            <pre>\${JSON.stringify(params, null, 2)}</pre>
                        </div>
                    </div>
                \`;
            }
            
            // Result Section
            if (message.result || (message.payload && message.payload.result)) {
                const result = message.result || message.payload.result;
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">✅ Result</div>
                        <div class="detail-content">
                            <pre>\${JSON.stringify(result, null, 2)}</pre>
                        </div>
                    </div>
                \`;
            }
            
            // Error Section
            if (message.error || (message.payload && message.payload.error)) {
                const error = message.error || message.payload.error;
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">❌ Error Details</div>
                        <div class="detail-content">
                            <pre>\${JSON.stringify(error, null, 2)}</pre>
                        </div>
                    </div>
                \`;
            }
            
            // Full Payload Section
            if (message.payload) {
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">📦 Full Message Payload</div>
                        <div class="detail-content">
                            <pre>\${JSON.stringify(message.payload, null, 2)}</pre>
                        </div>
                    </div>
                \`;
            }
            
            // Raw Message Section (fallback)
            if (!message.payload && !message.params && !message.result && !message.error) {
                details += \`
                    <div class="detail-section">
                        <div class="detail-title">📄 Raw Message Data</div>
                        <div class="detail-content">
                            <pre>\${JSON.stringify(message, null, 2)}</pre>
                        </div>
                    </div>
                \`;
            }
            
            return details;
        }

        function toggleLogDetails(entryId) {
            const entry = document.getElementById(entryId);
            if (entry) {
                entry.classList.toggle('expanded');
                
                // Update the preserved state
                const signature = getLogEntrySignature(entry);
                if (signature) {
                    if (entry.classList.contains('expanded')) {
                        expandedEntries.add(signature);
                    } else {
                        expandedEntries.delete(signature);
                    }
                }
            }
        }

        function updateStats() {
            document.getElementById('total-messages').textContent = messageCount;
            document.getElementById('last-activity').textContent = new Date().toLocaleTimeString();
            
            // Reset messages per minute counter
            const now = Date.now();
            if (now - lastMinuteReset > 60000) {
                messagesThisMinute = 0;
                lastMinuteReset = now;
            }
            document.getElementById('messages-per-min').textContent = messagesThisMinute;
        }

        function refreshLogs() {
            fetch('http://localhost:${this.apiPort}/api/v1/messages/live')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const container = document.getElementById('logs-container');
                        
                        // Preserve current expanded states
                        preserveExpandedStates();
                        
                        // Only add new messages, don't clear existing ones
                        const currentMessageCount = container.children.length;
                        
                        if (currentMessageCount === 0) {
                            // If container is empty, add initial message
                            container.innerHTML = '<div class="log-entry"><div class="log-timestamp">Live messages loaded...</div></div>';
                        }
                        
                        // Add new messages that aren't already displayed
                        data.messages.forEach((message, index) => {
                            // Only add messages that are newer than what we have
                            if (index >= currentMessageCount - 1) {
                                addLogEntry(message);
                            }
                        });
                        
                        // Restore expanded states
                        restoreExpandedStates();
                    }
                })
                .catch(console.error);
        }

        function generateTraceReport() {
            fetch('http://localhost:${this.apiPort}/api/v1/reports/trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Trace report generated successfully!');
                } else {
                    alert('❌ Failed to generate trace report: ' + data.error);
                }
            })
            .catch(err => alert('❌ Error: ' + err.message));
        }

        function generateUsabilityReport() {
            fetch('http://localhost:${this.apiPort}/api/v1/reports/usability', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host: 'cursor', timeRange: '24h' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Usability report generated successfully!');
                } else {
                    alert('❌ Failed to generate usability report: ' + data.error);
                }
            })
            .catch(err => alert('❌ Error: ' + err.message));
        }

        function downloadTraceReport() {
            window.open('http://localhost:${this.apiPort}/api/v1/reports/trace/generate', '_blank');
        }

        function downloadUsabilityReport() {
            window.open('http://localhost:${this.apiPort}/api/v1/reports/usability/generate?host=cursor&timeRange=24h', '_blank');
        }

        // Auto-refresh metrics every 30 seconds from API
        setInterval(() => {
            fetch('http://localhost:${this.apiPort}/api/v1/performance/live')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cognitive-health').textContent = data.cognitiveHealth;
                    document.getElementById('active-hosts').textContent = data.activeHosts;
                    document.getElementById('avg-load').textContent = data.avgCognitiveLoad;
                    document.getElementById('success-rate').textContent = data.successRate + '%';
                })
                .catch(console.error);
        }, 30000);

        // Refresh logs every 10 seconds
        setInterval(refreshLogs, 10000);
    </script>
</body>
</html>`;
    }
    /**
     * Update host data
     */
    updateHostData(hosts) {
        const hostData = Array.isArray(hosts) ? hosts : [hosts];
        this.io.emit('hosts_updated', hostData);
    }
}
exports.Dashboard = Dashboard;
//# sourceMappingURL=dashboard.js.map