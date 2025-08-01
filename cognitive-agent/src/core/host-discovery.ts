import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs/promises';
import { logger } from '../utils/logger';

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

export class MCPHostDiscovery {
  private readonly homeDir = os.homedir();

  /**
   * Discover all available MCP hosts on the system
   */
  async discoverAllHosts(): Promise<MCPHost[]> {
    logger.info('🔍 Discovering MCP hosts...');

    const discoveryPromises = [
      this.discoverCursor(),
      this.discoverClaudeDesktop(), 
      this.discoverWindsurf(),
      this.discoverCustomHosts()
    ];

    const hosts = await Promise.allSettled(discoveryPromises);
    const validHosts = hosts
      .filter((result): result is PromiseFulfilledResult<MCPHost> => 
        result.status === 'fulfilled' && result.value.exists
      )
      .map(result => result.value);

    logger.info(`✅ Discovered ${validHosts.length} MCP hosts:`, 
      validHosts.map(h => `${h.name} (${h.type})`));

    return validHosts;
  }

  /**
   * Discover Cursor IDE MCP configuration
   */
  async discoverCursor(): Promise<MCPHost> {
    const globalConfigPath = path.join(this.homeDir, '.cursor', 'mcp.json');
    const projectConfigPath = path.join(process.cwd(), '.cursor', 'mcp.json');
    const projectRootConfigPath = path.join(process.cwd(), '..', '.cursor', 'mcp.json');
    
    // Try project root first (for when agent runs from subdirectory), then current dir, then global
    const configPaths = [projectRootConfigPath, projectConfigPath, globalConfigPath];
    
    for (const configPath of configPaths) {
      try {
        await fs.access(configPath);
        const config = await this.readMCPConfig(configPath);
        
        const host: MCPHost = {
          name: 'cursor',
          type: 'ide',
          configPath: path.resolve(configPath),
          exists: true,
          enabled: true,
          proxyPort: 8001,
          servers: config.mcpServers || {}
        };
        
        const serverCount = Object.keys(host.servers || {}).length;
        const configType = configPath.includes(this.homeDir) ? 'global' : 'project-level';
        logger.debug(`📱 Cursor found (${configType}): ${serverCount} servers configured at ${host.configPath}`);
        return host;
      } catch (error) {
        logger.debug(`📱 Cursor config not found at ${configPath}`);
      }
    }

    // Return default if not found
    return {
      name: 'cursor',
      type: 'ide',
      configPath: globalConfigPath,
      exists: false,
      enabled: true,
      proxyPort: 8001
    };
  }

  /**
   * Discover Claude Desktop MCP configuration
   */
  async discoverClaudeDesktop(): Promise<MCPHost> {
    // Try common Claude Desktop paths across platforms
    const possiblePaths = [
      path.join(this.homeDir, '.config', 'claude', 'mcp.json'),
      path.join(this.homeDir, 'Library', 'Application Support', 'Claude', 'mcp.json'),
      path.join(this.homeDir, 'AppData', 'Roaming', 'Claude', 'mcp.json')
    ];

    for (const configPath of possiblePaths) {
      try {
        await fs.access(configPath);
        const config = await this.readMCPConfig(configPath);
        
        const host: MCPHost = {
          name: 'claude-desktop',
          type: 'desktop',
          configPath,
          exists: true,
          enabled: true,
          proxyPort: 8002,
          servers: config.mcpServers || {}
        };

        logger.debug(`🎯 Claude Desktop found: ${Object.keys(host.servers || {}).length} servers configured`);
        return host;
      } catch {
        continue;
      }
    }

    // Return default with first path as fallback
    const defaultPath = possiblePaths[0] || path.join(this.homeDir, '.config', 'claude', 'mcp.json');
    return {
      name: 'claude-desktop',
      type: 'desktop', 
      configPath: defaultPath,
      exists: false,
      enabled: true,
      proxyPort: 8002
    };
  }

  /**
   * Discover Windsurf IDE MCP configuration
   */
  async discoverWindsurf(): Promise<MCPHost> {
    const configPath = path.join(this.homeDir, '.windsurf', 'mcp.json');
    const host: MCPHost = {
      name: 'windsurf',
      type: 'ide',
      configPath,
      exists: false,
      enabled: true,
      proxyPort: 8003
    };

    try {
      await fs.access(configPath);
      const config = await this.readMCPConfig(configPath);
      
      host.exists = true;
      host.servers = config.mcpServers || {};
      
      logger.debug(`🌊 Windsurf found: ${Object.keys(host.servers || {}).length} servers configured`);
      return host;
    } catch (error) {
      logger.debug(`🌊 Windsurf not found at ${configPath}`);
      return host;
    }
  }

  /**
   * Discover custom MCP host configurations
   */
  async discoverCustomHosts(): Promise<MCPHost> {
    // For now, return a placeholder for custom hosts
    // In the future, this could read from a config file or registry
    return {
      name: 'custom',
      type: 'custom',
      configPath: path.join(this.homeDir, '.cognitive-obs', 'custom-hosts.json'),
      exists: false,
      enabled: false,
      proxyPort: 8004
    };
  }

  /**
   * Read and parse MCP configuration file
   */
  private async readMCPConfig(configPath: string): Promise<any> {
    try {
      const content = await fs.readFile(configPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      logger.error(`Failed to read MCP config at ${configPath}:`, error);
      throw error;
    }
  }

  /**
   * Watch for changes in MCP host configurations
   */
  async watchForChanges(hosts: MCPHost[], callback: (changedHost: MCPHost) => void): Promise<void> {
    const chokidar = await import('chokidar');
    
    const watchPaths = hosts
      .filter(host => host.exists)
      .map(host => host.configPath);

    if (watchPaths.length === 0) {
      logger.warn('⚠️ No MCP host configurations to watch');
      return;
    }

    const watcher = chokidar.watch(watchPaths, {
      persistent: true,
      ignoreInitial: true
    });

    watcher.on('change', async (changedPath) => {
      logger.info(`🔄 MCP config changed: ${changedPath}`);
      
      const changedHost = hosts.find(host => host.configPath === changedPath);
      if (changedHost) {
        // Re-read the configuration
        try {
          const config = await this.readMCPConfig(changedPath);
          changedHost.servers = config.mcpServers || {};
          callback(changedHost);
        } catch (error) {
          logger.error(`Failed to reload config for ${changedHost.name}:`, error);
        }
      }
    });

    logger.info(`👀 Watching ${watchPaths.length} MCP configurations for changes`);
  }

  /**
   * Get detailed information about a specific host
   */
  async getHostDetails(hostName: string): Promise<MCPHost | null> {
    const hosts = await this.discoverAllHosts();
    return hosts.find(host => host.name === hostName) || null;
  }

  /**
   * Check if a host has any MCP servers configured
   */
  hasActiveServers(host: MCPHost): boolean {
    return Boolean(host.servers && Object.keys(host.servers).length > 0);
  }

  /**
   * Get all configured MCP servers across all hosts
   */
  async getAllMCPServers(): Promise<Record<string, { host: string; config: MCPServerConfig }>> {
    const hosts = await this.discoverAllHosts();
    const allServers: Record<string, { host: string; config: MCPServerConfig }> = {};

    for (const host of hosts) {
      if (host.servers) {
        for (const [serverName, serverConfig] of Object.entries(host.servers)) {
          const key = `${host.name}:${serverName}`;
          allServers[key] = {
            host: host.name,
            config: serverConfig as MCPServerConfig
          };
        }
      }
    }

    return allServers;
  }
} 