export interface MCPHost {
    name: string;
    type: 'ide' | 'desktop' | 'custom';
    configPath: string;
    exists: boolean;
    enabled: boolean;
    proxyPort?: number;
    servers?: Record<string, any>;
}
export interface MCPServerConfig {
    command: string;
    args: string[];
    env?: Record<string, string>;
}
export declare class MCPHostDiscovery {
    private readonly homeDir;
    /**
     * Discover all available MCP hosts on the system
     */
    discoverAllHosts(): Promise<MCPHost[]>;
    /**
     * Discover Cursor IDE MCP configuration
     */
    discoverCursor(): Promise<MCPHost>;
    /**
     * Discover Claude Desktop MCP configuration
     */
    discoverClaudeDesktop(): Promise<MCPHost>;
    /**
     * Discover Windsurf IDE MCP configuration
     */
    discoverWindsurf(): Promise<MCPHost>;
    /**
     * Discover custom MCP host configurations
     */
    discoverCustomHosts(): Promise<MCPHost>;
    /**
     * Read and parse MCP configuration file
     */
    private readMCPConfig;
    /**
     * Watch for changes in MCP host configurations
     */
    watchForChanges(hosts: MCPHost[], callback: (changedHost: MCPHost) => void): Promise<void>;
    /**
     * Get detailed information about a specific host
     */
    getHostDetails(hostName: string): Promise<MCPHost | null>;
    /**
     * Check if a host has any MCP servers configured
     */
    hasActiveServers(host: MCPHost): boolean;
    /**
     * Get all configured MCP servers across all hosts
     */
    getAllMCPServers(): Promise<Record<string, {
        host: string;
        config: MCPServerConfig;
    }>>;
}
//# sourceMappingURL=host-discovery.d.ts.map