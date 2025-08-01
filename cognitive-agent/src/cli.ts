#!/usr/bin/env node

import { Command } from 'commander';
import { GlobalCognitiveAgent, GlobalAgentConfig } from './core/global-agent';
import { logger } from './utils/logger';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

const program = new Command();

program
  .name('cognitive-agent')
  .description('Global Cognitive Observability Agent for AI agent interactions')
  .version('1.0.0');

// Default configuration
const DEFAULT_CONFIG: GlobalAgentConfig = {
  mode: 'daemon',
  dashboardPort: 3000,
  apiPort: 3001,
  enableProactiveAlerts: true,
  analysisInterval: '*/15 * * * *', // Every 15 minutes
  enterpriseIntegrations: {}
};

/**
 * Start command - Start the global agent
 */
program
  .command('start')
  .description('Start the global cognitive observability agent')
  .option('-d, --daemon', 'Run as daemon process')
  .option('-p, --dashboard-port <port>', 'Dashboard port', '3000')
  .option('-a, --api-port <port>', 'API port', '3001')
  .option('--no-alerts', 'Disable proactive alerts')
  .option('-c, --config <path>', 'Configuration file path')
  .action(async (options) => {
    try {
      const config = await loadConfig(options);
      
      if (options.daemon !== undefined) {
        config.mode = options.daemon ? 'daemon' : 'interactive';
      }
      if (options.dashboardPort) {
        config.dashboardPort = parseInt(options.dashboardPort);
      }
      if (options.apiPort) {
        config.apiPort = parseInt(options.apiPort);
      }
      if (options.alerts === false) {
        config.enableProactiveAlerts = false;
      }

      const agent = new GlobalCognitiveAgent(config);
      
      await agent.start();

      // Handle graceful shutdown
      process.on('SIGINT', async () => {
        logger.info('\n🛑 Received SIGINT, shutting down gracefully...');
        await agent.stop();
        process.exit(0);
      });

      process.on('SIGTERM', async () => {
        logger.info('\n🛑 Received SIGTERM, shutting down gracefully...');
        await agent.stop();
        process.exit(0);
      });

      // Keep process alive in daemon mode
      if (config.mode === 'daemon') {
        process.on('uncaughtException', (error) => {
          logger.error('❌ Uncaught exception:', error);
        });

        process.on('unhandledRejection', (reason, promise) => {
          logger.error('❌ Unhandled rejection at:', promise, 'reason:', reason);
        });
      }

    } catch (error) {
      logger.error('❌ Failed to start agent:', error);
      process.exit(1);
    }
  });

/**
 * Status command - Show current agent status
 */
program
  .command('status')
  .description('Show current agent status and discovered hosts')
  .action(async () => {
    try {
      // Try to connect to running agent API
      const axios = await import('axios');
      const response = await axios.default.get('http://localhost:3001/api/v1/status');
      
      const status = response.data;
      
      console.log('\n🎯 === COGNITIVE OBSERVABILITY AGENT STATUS ===');
      console.log(`Status: ${status.isRunning ? '✅ Running' : '❌ Stopped'}`);
      console.log(`Dashboard: http://localhost:${status.dashboardUrl.split(':')[2]}`);
      console.log(`API: http://localhost:${status.apiUrl.split(':')[2]}`);
      console.log(`\n📱 Discovered Hosts (${status.hosts.length}):`);
      
      for (const host of status.hosts) {
        const serverCount = host.servers ? Object.keys(host.servers).length : 0;
        const statusIcon = host.exists ? '✅' : '❌';
        console.log(`  ${statusIcon} ${host.name} (${host.type}): ${serverCount} servers`);
      }
      
      console.log('\n🧠 Analysis Status:');
      console.log(`  Cognitive Load Score: ${status.analysisStatus.cognitiveLoad}/100`);
      console.log(`  Active Sessions: ${status.analysisStatus.activeSessions}`);
      console.log(`  Insights Generated: ${status.analysisStatus.insightsGenerated}`);
      
      console.log('\n================================================\n');

    } catch (error) {
      console.log('\n❌ Agent is not running or not accessible');
      console.log('💡 Start the agent with: cognitive-agent start --daemon\n');
    }
  });

/**
 * Discover command - Discover available MCP hosts
 */
program
  .command('discover')
  .description('Discover available MCP hosts without starting the agent')
  .action(async () => {
    try {
      const { MCPHostDiscovery } = await import('./core/host-discovery');
      const discovery = new MCPHostDiscovery();
      
      console.log('\n🔍 Discovering MCP hosts...\n');
      
      const hosts = await discovery.discoverAllHosts();
      
      if (hosts.length === 0) {
        console.log('❌ No MCP hosts found');
        console.log('💡 Make sure you have Cursor, Claude Desktop, or Windsurf installed\n');
        return;
      }

      console.log(`✅ Found ${hosts.length} MCP hosts:\n`);
      
      for (const host of hosts) {
        const serverCount = host.servers ? Object.keys(host.servers).length : 0;
        console.log(`📱 ${host.name.toUpperCase()} (${host.type})`);
        console.log(`   Config: ${host.configPath}`);
        console.log(`   Servers: ${serverCount}`);
        
        if (host.servers && serverCount > 0) {
          for (const [name, config] of Object.entries(host.servers)) {
            console.log(`     • ${name}: ${(config as any).command}`);
          }
        }
        console.log();
      }

    } catch (error) {
      logger.error('❌ Failed to discover hosts:', error);
      process.exit(1);
    }
  });

/**
 * Configure command - Set up enterprise integrations
 */
program
  .command('configure')
  .description('Configure enterprise integrations and agent settings')
  .option('--posthog-key <key>', 'PostHog API key')
  .option('--langsmith-key <key>', 'LangSmith API key')
  .option('--opentelemetry-endpoint <url>', 'OpenTelemetry endpoint')
  .option('--webhook-url <url>', 'Custom webhook URL')
  .option('--dashboard-port <port>', 'Dashboard port', '3000')
  .option('--api-port <port>', 'API port', '3001')
  .action(async (options) => {
    try {
      const configPath = path.join(os.homedir(), '.cognitive-obs', 'config.json');
      
      // Ensure config directory exists
      await fs.mkdir(path.dirname(configPath), { recursive: true });
      
      // Load existing config or use defaults
      let config: GlobalAgentConfig;
      try {
        const existing = await fs.readFile(configPath, 'utf-8');
        config = JSON.parse(existing);
      } catch {
        config = { ...DEFAULT_CONFIG };
      }

      // Update with new options
      if (options.posthogKey) {
        config.enterpriseIntegrations.posthog = { apiKey: options.posthogKey };
      }
      if (options.langsmithKey) {
        config.enterpriseIntegrations.langsmith = { apiKey: options.langsmithKey };
      }
      if (options.opentelemetryEndpoint) {
        config.enterpriseIntegrations.opentelemetry = { endpoint: options.opentelemetryEndpoint };
      }
      if (options.webhookUrl) {
        config.enterpriseIntegrations.custom = { webhookUrl: options.webhookUrl };
      }
      if (options.dashboardPort) {
        config.dashboardPort = parseInt(options.dashboardPort);
      }
      if (options.apiPort) {
        config.apiPort = parseInt(options.apiPort);
      }

      // Save updated config
      await fs.writeFile(configPath, JSON.stringify(config, null, 2));
      
      console.log('\n✅ Configuration updated successfully');
      console.log(`📁 Config saved to: ${configPath}`);
      console.log('\n🔗 Enterprise Integrations:');
      
      const integrations = config.enterpriseIntegrations;
      console.log(`  PostHog: ${integrations.posthog ? '✅ Configured' : '❌ Not configured'}`);
      console.log(`  LangSmith: ${integrations.langsmith ? '✅ Configured' : '❌ Not configured'}`);
      console.log(`  OpenTelemetry: ${integrations.opentelemetry ? '✅ Configured' : '❌ Not configured'}`);
      console.log(`  Custom Webhook: ${integrations.custom ? '✅ Configured' : '❌ Not configured'}`);
      
      console.log('\n📊 Ports:');
      console.log(`  Dashboard: ${config.dashboardPort}`);
      console.log(`  API: ${config.apiPort}\n`);

    } catch (error) {
      logger.error('❌ Failed to configure agent:', error);
      process.exit(1);
    }
  });

/**
 * Stop command - Stop the running agent
 */
program
  .command('stop')
  .description('Stop the running agent')
  .action(async () => {
    try {
      const axios = await import('axios');
      await axios.default.post('http://localhost:3001/api/v1/stop');
      console.log('✅ Agent stopped successfully');
    } catch (error) {
      console.log('❌ Agent is not running or not accessible');
    }
  });

/**
 * Dashboard command - Open dashboard in browser
 */
program
  .command('dashboard')
  .description('Open the dashboard in your default browser')
  .action(async () => {
    try {
      const { exec } = await import('child_process');
      const url = 'http://localhost:3000';
      
      // Try to open browser based on platform
      const platform = process.platform;
      let command: string;
      
      if (platform === 'darwin') {
        command = `open ${url}`;
      } else if (platform === 'win32') {
        command = `start ${url}`;
      } else {
        command = `xdg-open ${url}`;
      }
      
      exec(command, (error) => {
        if (error) {
          console.log(`📊 Dashboard available at: ${url}`);
          console.log('💡 Open this URL in your browser manually');
        } else {
          console.log('✅ Dashboard opened in your default browser');
        }
      });

    } catch (error) {
      console.log('📊 Dashboard available at: http://localhost:3000');
      console.log('💡 Open this URL in your browser');
    }
  });

/**
 * Load configuration from file or use defaults
 */
async function loadConfig(options: any): Promise<GlobalAgentConfig> {
  let config = { ...DEFAULT_CONFIG };

  // Try to load from specified config file
  if (options.config) {
    try {
      const configContent = await fs.readFile(options.config, 'utf-8');
      const fileConfig = JSON.parse(configContent);
      config = { ...config, ...fileConfig };
    } catch (error) {
      logger.warn(`⚠️ Could not load config file ${options.config}, using defaults`);
    }
  } else {
    // Try to load from default location
    try {
      const defaultConfigPath = path.join(os.homedir(), '.cognitive-obs', 'config.json');
      const configContent = await fs.readFile(defaultConfigPath, 'utf-8');
      const fileConfig = JSON.parse(configContent);
      config = { ...config, ...fileConfig };
    } catch {
      // No config file found, use defaults
    }
  }

  return config;
}

// Parse command line arguments
program.parse();

// If no command specified, show help
if (!process.argv.slice(2).length) {
  program.outputHelp();
} 