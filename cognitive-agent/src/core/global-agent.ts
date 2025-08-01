import { MCPHostDiscovery, MCPHost } from './host-discovery';
import { UniversalProxy } from './universal-proxy';
import { CognitiveAnalyzer } from './cognitive-analyzer';
import { EnterpriseIntegrations } from './enterprise-integrations';
import { Dashboard } from './dashboard';
import { logger } from '../utils/logger';
import * as cron from 'node-cron';

export interface GlobalAgentConfig {
  mode: 'daemon' | 'interactive';
  dashboardPort: number;
  apiPort: number;
  enableProactiveAlerts: boolean;
  analysisInterval: string; // cron expression
  enterpriseIntegrations: {
    posthog?: { apiKey: string };
    langsmith?: { apiKey: string };
    opentelemetry?: { endpoint: string };
    custom?: { webhookUrl: string };
  };
}

export class GlobalCognitiveAgent {
  private hostDiscovery: MCPHostDiscovery;
  private universalProxy: UniversalProxy;
  private cognitiveAnalyzer: CognitiveAnalyzer;
  private enterpriseIntegrations: EnterpriseIntegrations;
  private dashboard: Dashboard;
  private config: GlobalAgentConfig;
  private discoveredHosts: MCPHost[] = [];
  private isRunning = false;

  constructor(config: GlobalAgentConfig) {
    this.config = config;
    this.hostDiscovery = new MCPHostDiscovery();
    this.universalProxy = new UniversalProxy();
    this.cognitiveAnalyzer = new CognitiveAnalyzer();
    this.enterpriseIntegrations = new EnterpriseIntegrations(config.enterpriseIntegrations);
    this.dashboard = new Dashboard(config.dashboardPort, config.apiPort);
  }

  /**
   * Start the global cognitive observability agent
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('⚠️ Agent is already running');
      return;
    }

    logger.info('🚀 Starting Global Cognitive Observability Agent...');

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
      logger.info('✅ Global Cognitive Observability Agent started successfully');
      
      this.printStartupSummary();

    } catch (error) {
      logger.error('❌ Failed to start agent:', error);
      await this.stop();
      throw error;
    }
  }

  /**
   * Stop the global cognitive observability agent
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    logger.info('🛑 Stopping Global Cognitive Observability Agent...');

    try {
      await this.dashboard.stop();
      await this.universalProxy.stop();
      await this.enterpriseIntegrations.stop();
      
      this.isRunning = false;
      logger.info('✅ Agent stopped successfully');
    } catch (error) {
      logger.error('❌ Error stopping agent:', error);
    }
  }

  /**
   * Discover MCP hosts and set up monitoring
   */
  private async discoverAndSetupHosts(): Promise<void> {
    logger.info('🔍 Discovering MCP hosts...');

    this.discoveredHosts = await this.hostDiscovery.discoverAllHosts();

    if (this.discoveredHosts.length === 0) {
      logger.warn('⚠️ No MCP hosts found. Agent will run in standby mode.');
      return;
    }

    logger.info(`✅ Found ${this.discoveredHosts.length} MCP hosts:`);
    for (const host of this.discoveredHosts) {
      const serverCount = host.servers ? Object.keys(host.servers).length : 0;
      logger.info(`  📱 ${host.name} (${host.type}): ${serverCount} servers`);
    }
  }

  /**
   * Start universal proxy system
   */
  private async startUniversalProxy(): Promise<void> {
    logger.info('🔗 Starting universal MCP proxy...');

    await this.universalProxy.start(this.discoveredHosts);
    logger.info('✅ Universal MCP proxy started');
  }

  /**
   * Start cognitive analysis engine
   */
  private async startCognitiveAnalysis(): Promise<void> {
    logger.info('🧠 Starting cognitive analysis engine...');

    // Start analysis engine
    this.cognitiveAnalyzer.start();
    
    // Connect cognitive analyzer to universal proxy for real-time message processing
    this.universalProxy.connectCognitiveAnalyzer(this.cognitiveAnalyzer);
    
    logger.info('✅ Cognitive analysis engine started');
  }

  /**
   * Start enterprise integrations
   */
  private async startEnterpriseIntegrations(): Promise<void> {
    logger.info('🔗 Starting enterprise integrations...');

    // Connect cognitive analyzer output to enterprise integrations
    this.cognitiveAnalyzer.onInsight((insight) => {
      this.enterpriseIntegrations.sendInsight(insight);
    });

    await this.enterpriseIntegrations.start();
    logger.info('✅ Enterprise integrations started');
  }

  /**
   * Start dashboard and API
   */
  private async startDashboard(): Promise<void> {
    logger.info('📊 Starting dashboard and API...');

    // Connect all data sources to dashboard
    this.dashboard.connectDataSources({
      hosts: this.discoveredHosts,
      cognitiveAnalyzer: this.cognitiveAnalyzer,
      universalProxy: this.universalProxy,
      enterpriseIntegrations: this.enterpriseIntegrations
    });

    await this.dashboard.start();
    logger.info(`✅ Dashboard available at http://localhost:${this.config.dashboardPort}`);
    logger.info(`✅ API available at http://localhost:${this.config.apiPort}`);
  }

  /**
   * Setup proactive monitoring with scheduled analysis
   */
  private setupProactiveMonitoring(): void {
    logger.info('🔔 Setting up proactive monitoring...');

    // Schedule regular cognitive analysis
    cron.schedule(this.config.analysisInterval, async () => {
      try {
        // Generate proactive reports
        const traceReport = await this.cognitiveAnalyzer.generateTraceReport();
        
        if (traceReport.cognitiveAnalysis.usabilityScore < 70) {
          logger.warn(`🚨 Proactive Alert - LOW USABILITY: Score ${traceReport.cognitiveAnalysis.usabilityScore}/100`);
          
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
      } catch (error) {
        logger.error('❌ Error in proactive monitoring:', error);
      }
    });

    logger.info(`✅ Proactive monitoring scheduled (${this.config.analysisInterval})`);
  }

  /**
   * Watch for changes in host configurations
   */
  private async watchForHostChanges(): Promise<void> {
    await this.hostDiscovery.watchForChanges(
      this.discoveredHosts,
      async (changedHost) => {
        if (changedHost.exists && this.hostDiscovery.hasActiveServers(changedHost)) {
          logger.info(`🔄 Host ${changedHost.name} configuration updated`);
          
          // Restart the proxy system to pick up changes
          await this.universalProxy.stop();
          await this.universalProxy.start(this.discoveredHosts);
          
          // Update dashboard
          this.dashboard.updateHostData(changedHost);
        } else {
          logger.info(`🔄 Host ${changedHost.name} disabled or has no active servers`);
        }
      }
    );
  }

  /**
   * Print startup summary
   */
  private printStartupSummary(): void {
    const activeHosts = this.discoveredHosts.filter(h => 
      this.hostDiscovery.hasActiveServers(h)
    );

    logger.info('\n🎯 === COGNITIVE OBSERVABILITY AGENT READY ===');
    logger.info(`📊 Dashboard: http://localhost:${this.config.dashboardPort}`);
    logger.info(`🔌 API: http://localhost:${this.config.apiPort}`);
    logger.info(`🖥️  Active Hosts: ${activeHosts.map(h => h.name).join(', ')}`);
    logger.info(`🧠 Cognitive Analysis: ${this.config.enableProactiveAlerts ? 'Proactive' : 'Reactive'}`);
    logger.info(`🔗 Enterprise Integrations: ${Object.keys(this.config.enterpriseIntegrations).length}`);
    logger.info('================================================\n');
  }

  /**
   * Get current status
   */
  getStatus(): {
    isRunning: boolean;
    hosts: MCPHost[];
    proxyStatus: any;
    analysisStatus: any;
    dashboardUrl: string;
    apiUrl: string;
  } {
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
  async refreshHosts(): Promise<void> {
    logger.info('🔄 Refreshing host discovery...');
    
    const newHosts = await this.hostDiscovery.discoverAllHosts();
    
    // Find newly added hosts
    const newHostNames = newHosts.map(h => h.name);
    const currentHostNames = this.discoveredHosts.map(h => h.name);
    const addedHosts = newHosts.filter(h => !currentHostNames.includes(h.name));
    const removedHosts = this.discoveredHosts.filter(h => !newHostNames.includes(h.name));

    if (addedHosts.length > 0) {
      logger.info(`✅ New hosts found: ${addedHosts.map(h => h.name).join(', ')}`);
    }

    if (removedHosts.length > 0) {
      logger.info(`⚠️ Hosts removed: ${removedHosts.map(h => h.name).join(', ')}`);
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
  private async handleHostConfigurationChange(changedHost: MCPHost): Promise<void> {
    try {
      logger.info(`🔄 Host configuration changed: ${changedHost.name}`);
      
      // Restart the proxy system to pick up changes
      await this.universalProxy.stop();
      await this.universalProxy.start(this.discoveredHosts);
      
      logger.info(`✅ Updated proxy configuration for ${changedHost.name}`);
    } catch (error) {
      logger.error(`❌ Failed to update proxy for ${changedHost.name}:`, error);
    }
  }

  /**
   * Handle newly discovered hosts
   */
  private async handleNewHost(host: MCPHost): Promise<void> {
    try {
      logger.info(`🆕 New host discovered: ${host.name}`);
      
      this.discoveredHosts.push(host);
      
      // Restart proxy with new host
      await this.universalProxy.stop();
      await this.universalProxy.start(this.discoveredHosts);
      
      // Update dashboard
      this.dashboard.updateHostData(this.discoveredHosts);
    } catch (error) {
      logger.error(`❌ Failed to add new host ${host.name}:`, error);
    }
  }

  /**
   * Handle removed hosts
   */
  private async handleRemovedHost(host: MCPHost): Promise<void> {
    try {
      logger.info(`🗑️ Host removed: ${host.name}`);
      
      this.discoveredHosts = this.discoveredHosts.filter(h => h.name !== host.name);
      
      // Restart proxy without removed host
      await this.universalProxy.stop();
      await this.universalProxy.start(this.discoveredHosts);
      
      // Update dashboard
      this.dashboard.updateHostData(this.discoveredHosts);
    } catch (error) {
      logger.error(`❌ Failed to remove host ${host.name}:`, error);
    }
  }
} 