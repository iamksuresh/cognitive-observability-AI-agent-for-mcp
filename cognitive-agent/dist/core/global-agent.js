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
Object.defineProperty(exports, "__esModule", { value: true });
exports.GlobalCognitiveAgent = void 0;
const host_discovery_1 = require("./host-discovery");
const universal_proxy_1 = require("./universal-proxy");
const cognitive_analyzer_1 = require("./cognitive-analyzer");
const enterprise_integrations_1 = require("./enterprise-integrations");
const dashboard_1 = require("./dashboard");
const logger_1 = require("../utils/logger");
const cron = __importStar(require("node-cron"));
class GlobalCognitiveAgent {
    constructor(config) {
        this.discoveredHosts = [];
        this.isRunning = false;
        this.config = config;
        this.hostDiscovery = new host_discovery_1.MCPHostDiscovery();
        this.universalProxy = new universal_proxy_1.UniversalProxy();
        this.cognitiveAnalyzer = new cognitive_analyzer_1.CognitiveAnalyzer();
        this.enterpriseIntegrations = new enterprise_integrations_1.EnterpriseIntegrations(config.enterpriseIntegrations);
        this.dashboard = new dashboard_1.Dashboard(config.dashboardPort, config.apiPort);
    }
    /**
     * Start the global cognitive observability agent
     */
    async start() {
        if (this.isRunning) {
            logger_1.logger.warn('⚠️ Agent is already running');
            return;
        }
        logger_1.logger.info('🚀 Starting Global Cognitive Observability Agent...');
        try {
            // 1. Discover all MCP hosts
            await this.discoverAndSetupHosts();
            // 2. Start universal proxy for all hosts
            await this.startUniversalProxy();
            // 3. Start cognitive analysis engine
            await this.startCognitiveAnalysis();
            // 4. Start enterprise integrations
            await this.startEnterpriseIntegrations();
            // 5. Start dashboard and API
            await this.startDashboard();
            // 6. Setup proactive monitoring
            if (this.config.enableProactiveAlerts) {
                this.setupProactiveMonitoring();
            }
            // 7. Watch for host configuration changes
            await this.watchForHostChanges();
            this.isRunning = true;
            logger_1.logger.info('✅ Global Cognitive Observability Agent started successfully');
            this.printStartupSummary();
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to start agent:', error);
            await this.stop();
            throw error;
        }
    }
    /**
     * Stop the global cognitive observability agent
     */
    async stop() {
        if (!this.isRunning) {
            return;
        }
        logger_1.logger.info('🛑 Stopping Global Cognitive Observability Agent...');
        try {
            await this.dashboard.stop();
            await this.universalProxy.stop();
            await this.enterpriseIntegrations.stop();
            this.isRunning = false;
            logger_1.logger.info('✅ Agent stopped successfully');
        }
        catch (error) {
            logger_1.logger.error('❌ Error stopping agent:', error);
        }
    }
    /**
     * Discover MCP hosts and set up monitoring
     */
    async discoverAndSetupHosts() {
        logger_1.logger.info('🔍 Discovering MCP hosts...');
        this.discoveredHosts = await this.hostDiscovery.discoverAllHosts();
        if (this.discoveredHosts.length === 0) {
            logger_1.logger.warn('⚠️ No MCP hosts found. Agent will run in standby mode.');
            return;
        }
        logger_1.logger.info(`✅ Found ${this.discoveredHosts.length} MCP hosts:`);
        for (const host of this.discoveredHosts) {
            const serverCount = host.servers ? Object.keys(host.servers).length : 0;
            logger_1.logger.info(`  📱 ${host.name} (${host.type}): ${serverCount} servers`);
        }
    }
    /**
     * Start universal proxy system
     */
    async startUniversalProxy() {
        logger_1.logger.info('🔗 Starting universal MCP proxy...');
        await this.universalProxy.start(this.discoveredHosts);
        logger_1.logger.info('✅ Universal MCP proxy started');
    }
    /**
     * Start cognitive analysis engine
     */
    async startCognitiveAnalysis() {
        logger_1.logger.info('🧠 Starting cognitive analysis engine...');
        // Start analysis engine
        this.cognitiveAnalyzer.start();
        // Connect cognitive analyzer to universal proxy for real-time message processing
        this.universalProxy.connectCognitiveAnalyzer(this.cognitiveAnalyzer);
        logger_1.logger.info('✅ Cognitive analysis engine started');
    }
    /**
     * Start enterprise integrations
     */
    async startEnterpriseIntegrations() {
        logger_1.logger.info('🔗 Starting enterprise integrations...');
        // Connect cognitive analyzer output to enterprise integrations
        this.cognitiveAnalyzer.onInsight((insight) => {
            this.enterpriseIntegrations.sendInsight(insight);
        });
        await this.enterpriseIntegrations.start();
        logger_1.logger.info('✅ Enterprise integrations started');
    }
    /**
     * Start dashboard and API
     */
    async startDashboard() {
        logger_1.logger.info('📊 Starting dashboard and API...');
        // Connect all data sources to dashboard
        this.dashboard.connectDataSources({
            hosts: this.discoveredHosts,
            cognitiveAnalyzer: this.cognitiveAnalyzer,
            universalProxy: this.universalProxy,
            enterpriseIntegrations: this.enterpriseIntegrations
        });
        await this.dashboard.start();
        logger_1.logger.info(`✅ Dashboard available at http://localhost:${this.config.dashboardPort}`);
        logger_1.logger.info(`✅ API available at http://localhost:${this.config.apiPort}`);
    }
    /**
     * Setup proactive monitoring with scheduled analysis
     */
    setupProactiveMonitoring() {
        logger_1.logger.info('🔔 Setting up proactive monitoring...');
        // Schedule regular cognitive analysis
        cron.schedule(this.config.analysisInterval, async () => {
            try {
                // Generate proactive reports
                const traceReport = await this.cognitiveAnalyzer.generateTraceReport();
                if (traceReport.cognitiveAnalysis.usabilityScore < 70) {
                    logger_1.logger.warn(`🚨 Proactive Alert - LOW USABILITY: Score ${traceReport.cognitiveAnalysis.usabilityScore}/100`);
                    // Emit to dashboard
                    this.dashboard.updateHostData(this.discoveredHosts);
                    // Send to enterprise integrations if high friction detected
                    if (traceReport.cognitiveAnalysis.frictionPoints.length > 0) {
                        await this.enterpriseIntegrations.sendProactiveAlert({
                            severity: 'high',
                            summary: `${traceReport.cognitiveAnalysis.frictionPoints.length} friction points detected`,
                            recommendations: traceReport.cognitiveAnalysis.frictionPoints.map(fp => fp.recommendation)
                        });
                    }
                }
            }
            catch (error) {
                logger_1.logger.error('❌ Error in proactive monitoring:', error);
            }
        });
        logger_1.logger.info(`✅ Proactive monitoring scheduled (${this.config.analysisInterval})`);
    }
    /**
     * Watch for changes in host configurations
     */
    async watchForHostChanges() {
        await this.hostDiscovery.watchForChanges(this.discoveredHosts, async (changedHost) => {
            if (changedHost.exists && this.hostDiscovery.hasActiveServers(changedHost)) {
                logger_1.logger.info(`🔄 Host ${changedHost.name} configuration updated`);
                // Restart the proxy system to pick up changes
                await this.universalProxy.stop();
                await this.universalProxy.start(this.discoveredHosts);
                // Update dashboard
                this.dashboard.updateHostData(changedHost);
            }
            else {
                logger_1.logger.info(`🔄 Host ${changedHost.name} disabled or has no active servers`);
            }
        });
    }
    /**
     * Print startup summary
     */
    printStartupSummary() {
        const activeHosts = this.discoveredHosts.filter(h => this.hostDiscovery.hasActiveServers(h));
        logger_1.logger.info('\n🎯 === COGNITIVE OBSERVABILITY AGENT READY ===');
        logger_1.logger.info(`📊 Dashboard: http://localhost:${this.config.dashboardPort}`);
        logger_1.logger.info(`🔌 API: http://localhost:${this.config.apiPort}`);
        logger_1.logger.info(`🖥️  Active Hosts: ${activeHosts.map(h => h.name).join(', ')}`);
        logger_1.logger.info(`🧠 Cognitive Analysis: ${this.config.enableProactiveAlerts ? 'Proactive' : 'Reactive'}`);
        logger_1.logger.info(`🔗 Enterprise Integrations: ${Object.keys(this.config.enterpriseIntegrations).length}`);
        logger_1.logger.info('================================================\n');
    }
    /**
     * Get current status
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            hosts: this.discoveredHosts,
            proxyStatus: this.universalProxy.getStatus(),
            analysisStatus: this.cognitiveAnalyzer.getStatus(),
            dashboardUrl: `http://localhost:${this.config.dashboardPort}`,
            apiUrl: `http://localhost:${this.config.apiPort}`
        };
    }
    /**
     * Force refresh host discovery
     */
    async refreshHosts() {
        logger_1.logger.info('🔄 Refreshing host discovery...');
        const newHosts = await this.hostDiscovery.discoverAllHosts();
        // Find newly added hosts
        const newHostNames = newHosts.map(h => h.name);
        const currentHostNames = this.discoveredHosts.map(h => h.name);
        const addedHosts = newHosts.filter(h => !currentHostNames.includes(h.name));
        const removedHosts = this.discoveredHosts.filter(h => !newHostNames.includes(h.name));
        if (addedHosts.length > 0) {
            logger_1.logger.info(`✅ New hosts found: ${addedHosts.map(h => h.name).join(', ')}`);
        }
        if (removedHosts.length > 0) {
            logger_1.logger.info(`⚠️ Hosts removed: ${removedHosts.map(h => h.name).join(', ')}`);
        }
        // Update hosts and restart proxy system
        this.discoveredHosts = newHosts;
        if (addedHosts.length > 0 || removedHosts.length > 0) {
            await this.universalProxy.stop();
            await this.universalProxy.start(this.discoveredHosts);
        }
        this.dashboard.updateHostData(this.discoveredHosts);
    }
    /**
     * Handle host configuration changes
     */
    async handleHostConfigurationChange(changedHost) {
        try {
            logger_1.logger.info(`🔄 Host configuration changed: ${changedHost.name}`);
            // Restart the proxy system to pick up changes
            await this.universalProxy.stop();
            await this.universalProxy.start(this.discoveredHosts);
            logger_1.logger.info(`✅ Updated proxy configuration for ${changedHost.name}`);
        }
        catch (error) {
            logger_1.logger.error(`❌ Failed to update proxy for ${changedHost.name}:`, error);
        }
    }
    /**
     * Handle newly discovered hosts
     */
    async handleNewHost(host) {
        try {
            logger_1.logger.info(`🆕 New host discovered: ${host.name}`);
            this.discoveredHosts.push(host);
            // Restart proxy with new host
            await this.universalProxy.stop();
            await this.universalProxy.start(this.discoveredHosts);
            // Update dashboard
            this.dashboard.updateHostData(this.discoveredHosts);
        }
        catch (error) {
            logger_1.logger.error(`❌ Failed to add new host ${host.name}:`, error);
        }
    }
    /**
     * Handle removed hosts
     */
    async handleRemovedHost(host) {
        try {
            logger_1.logger.info(`🗑️ Host removed: ${host.name}`);
            this.discoveredHosts = this.discoveredHosts.filter(h => h.name !== host.name);
            // Restart proxy without removed host
            await this.universalProxy.stop();
            await this.universalProxy.start(this.discoveredHosts);
            // Update dashboard
            this.dashboard.updateHostData(this.discoveredHosts);
        }
        catch (error) {
            logger_1.logger.error(`❌ Failed to remove host ${host.name}:`, error);
        }
    }
}
exports.GlobalCognitiveAgent = GlobalCognitiveAgent;
//# sourceMappingURL=global-agent.js.map