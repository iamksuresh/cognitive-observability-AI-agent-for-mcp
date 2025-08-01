import { MCPHost } from './host-discovery';
import { CognitiveAnalyzer } from './cognitive-analyzer';
import { UniversalProxy } from './universal-proxy';
import { EnterpriseIntegrations } from './enterprise-integrations';
export interface DashboardDataSources {
    hosts: MCPHost[];
    cognitiveAnalyzer: CognitiveAnalyzer;
    universalProxy: UniversalProxy;
    enterpriseIntegrations: EnterpriseIntegrations;
}
export declare class Dashboard {
    private dashboardApp;
    private apiApp;
    private dashboardServer;
    private apiServer;
    private io;
    private dashboardPort;
    private apiPort;
    private dataSources?;
    private isRunning;
    constructor(dashboardPort: number, apiPort: number);
    /**
     * Connect data sources to the dashboard
     */
    connectDataSources(dataSources: DashboardDataSources): void;
    /**
     * Start both dashboard and API servers
     */
    start(): Promise<void>;
    /**
     * Stop both servers
     */
    stop(): Promise<void>;
    /**
     * Setup Express middleware for both servers
     */
    private setupMiddleware;
    /**
     * Setup routes for both servers
     */
    private setupRoutes;
    /**
     * Setup API routes on the API server
     */
    private setupAPIRoutes;
    /**
     * Setup Socket.IO for real-time updates
     */
    private setupSocketIO;
    /**
     * Generate dashboard HTML with live logs and download buttons
     */
    private getDashboardHTML;
    /**
     * Update host data
     */
    updateHostData(hosts: MCPHost | MCPHost[]): void;
}
//# sourceMappingURL=dashboard.d.ts.map