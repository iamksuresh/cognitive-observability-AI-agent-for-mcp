import { MCPHost } from './host-discovery';
export interface GlobalAgentConfig {
    mode: 'daemon' | 'interactive';
    dashboardPort: number;
    apiPort: number;
    enableProactiveAlerts: boolean;
    analysisInterval: string;
    enterpriseIntegrations: {
        posthog?: {
            apiKey: string;
        };
        langsmith?: {
            apiKey: string;
        };
        opentelemetry?: {
            endpoint: string;
        };
        custom?: {
            webhookUrl: string;
        };
    };
}
export declare class GlobalCognitiveAgent {
    private hostDiscovery;
    private universalProxy;
    private cognitiveAnalyzer;
    private enterpriseIntegrations;
    private dashboard;
    private config;
    private discoveredHosts;
    private isRunning;
    constructor(config: GlobalAgentConfig);
    /**
     * Start the global cognitive observability agent
     */
    start(): Promise<void>;
    /**
     * Stop the global cognitive observability agent
     */
    stop(): Promise<void>;
    /**
     * Discover MCP hosts and set up monitoring
     */
    private discoverAndSetupHosts;
    /**
     * Start universal proxy system
     */
    private startUniversalProxy;
    /**
     * Start cognitive analysis engine
     */
    private startCognitiveAnalysis;
    /**
     * Start enterprise integrations
     */
    private startEnterpriseIntegrations;
    /**
     * Start dashboard and API
     */
    private startDashboard;
    /**
     * Setup proactive monitoring with scheduled analysis
     */
    private setupProactiveMonitoring;
    /**
     * Watch for changes in host configurations
     */
    private watchForHostChanges;
    /**
     * Print startup summary
     */
    private printStartupSummary;
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
    };
    /**
     * Force refresh host discovery
     */
    refreshHosts(): Promise<void>;
    /**
     * Handle host configuration changes
     */
    private handleHostConfigurationChange;
    /**
     * Handle newly discovered hosts
     */
    private handleNewHost;
    /**
     * Handle removed hosts
     */
    private handleRemovedHost;
}
//# sourceMappingURL=global-agent.d.ts.map