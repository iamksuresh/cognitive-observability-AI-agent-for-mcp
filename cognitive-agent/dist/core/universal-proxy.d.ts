import { EventEmitter } from 'events';
import { MCPHost } from './host-discovery';
import { CognitiveAnalyzer } from './cognitive-analyzer';
export interface MCPMessage {
    id: string;
    timestamp: Date;
    host: string;
    server: string;
    direction: 'inbound' | 'outbound';
    payload: any;
    latencyMs?: number;
}
export interface ProxyStatus {
    isRunning: boolean;
    activeProxies: string[];
    messageCount: number;
    lastMessageTime: string | null;
}
export declare class UniversalProxy extends EventEmitter {
    private isRunning;
    private activeProxies;
    private messageStream;
    private cognitiveAnalyzer?;
    private messageCount;
    private lastMessageTime;
    private mcpInterceptors;
    private realMessageBuffer;
    private availableTools;
    constructor();
    /**
     * Connect cognitive analyzer for real-time message analysis
     */
    connectCognitiveAnalyzer(analyzer: CognitiveAnalyzer): void;
    /**
     * Start the universal proxy system with REAL MCP traffic interception
     */
    start(hosts: MCPHost[]): Promise<void>;
    /**
     * Stop the universal proxy system
     */
    stop(): Promise<void>;
    /**
     * Setup REAL MCP traffic interception for a host
     */
    private setupRealMCPInterception;
    /**
     * Create an MCP interceptor that captures real stdio communication
     */
    private createMCPInterceptor;
    /**
     * Setup stdio capture to intercept actual MCP JSON-RPC messages
     */
    private setupStdioCapture;
    /**
     * Process real stdio data to extract JSON-RPC messages
     */
    private processRealStdioData;
    /**
     * Check if a line contains valid JSON-RPC
     */
    private isValidJSONRPC;
    /**
     * Capture a real MCP message from stdio
     */
    private captureRealMCPMessage;
    /**
     * Update available tools for a server based on tools/list response
     */
    private updateAvailableTools;
    /**
     * Get available tools for a server
     */
    private getAvailableTools;
    /**
     * Enhanced console monitoring as fallback for capturing tool calls
     */
    private setupConsoleMonitoring;
    /**
     * Scan console output for MCP activity patterns
     */
    private scanForMCPActivity;
    /**
     * Process a real MCP message
     */
    private processRealMCPMessage;
    /**
     * Process an intercepted MCP message
     */
    private processMessage;
    /**
     * Get proxy status
     */
    getStatus(): ProxyStatus;
    /**
     * Get message stream for analysis
     */
    getMessageStream(): MCPMessage[];
    /**
     * Get recent messages for live display
     */
    getRecentMessages(limit?: number): any[];
}
//# sourceMappingURL=universal-proxy.d.ts.map