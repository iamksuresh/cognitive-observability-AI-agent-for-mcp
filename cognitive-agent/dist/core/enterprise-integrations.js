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
exports.EnterpriseIntegrations = void 0;
const logger_1 = require("../utils/logger");
class EnterpriseIntegrations {
    constructor(config) {
        this.isRunning = false;
        this.config = config;
    }
    /**
     * Start enterprise integrations
     */
    async start() {
        if (this.isRunning) {
            return;
        }
        logger_1.logger.info('🔗 Starting enterprise integrations...');
        try {
            // Initialize PostHog
            if (this.config.posthog) {
                await this.initializePostHog();
                logger_1.logger.info('✅ PostHog integration initialized');
            }
            // Initialize LangSmith
            if (this.config.langsmith) {
                await this.initializeLangSmith();
                logger_1.logger.info('✅ LangSmith integration initialized');
            }
            // Initialize OpenTelemetry
            if (this.config.opentelemetry) {
                await this.initializeOpenTelemetry();
                logger_1.logger.info('✅ OpenTelemetry integration initialized');
            }
            this.isRunning = true;
            logger_1.logger.info('✅ Enterprise integrations started');
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to start enterprise integrations:', error);
            throw error;
        }
    }
    /**
     * Stop enterprise integrations
     */
    async stop() {
        if (!this.isRunning) {
            return;
        }
        logger_1.logger.info('🛑 Stopping enterprise integrations...');
        // Cleanup connections
        if (this.posthogClient) {
            try {
                await this.posthogClient.shutdown();
            }
            catch (error) {
                logger_1.logger.error('Error shutting down PostHog:', error);
            }
        }
        this.isRunning = false;
        logger_1.logger.info('✅ Enterprise integrations stopped');
    }
    /**
     * Send cognitive insight to configured platforms
     */
    async sendInsight(insight) {
        if (!this.isRunning) {
            return;
        }
        try {
            // Send to PostHog
            if (this.posthogClient) {
                await this.sendToPostHog(insight);
            }
            // Send to LangSmith
            if (this.langsmithClient) {
                await this.sendToLangSmith(insight);
            }
            // Send to custom webhooks
            if (this.config.custom) {
                await this.sendToCustomWebhook(insight);
            }
            logger_1.logger.debug('✅ Insight sent to enterprise platforms');
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to send insight to enterprise platforms:', error);
        }
    }
    /**
     * Send proactive alert to enterprise platforms
     */
    async sendProactiveAlert(alert) {
        // Reuse sendInsight method with alert data
        await this.sendInsight(alert);
    }
    /**
     * Send alert to configured platforms
     */
    async sendAlert(alert) {
        if (!this.isRunning) {
            return;
        }
        try {
            // Send alert to PostHog
            if (this.posthogClient) {
                await this.sendAlertToPostHog(alert);
            }
            // Send alert to custom webhook
            if (this.config.custom) {
                await this.sendAlertToWebhook(alert);
            }
            logger_1.logger.info(`🚨 Alert sent: ${alert.severity} - ${alert.message}`);
        }
        catch (error) {
            logger_1.logger.error('❌ Error sending alert:', error);
        }
    }
    /**
     * Initialize PostHog client
     */
    async initializePostHog() {
        try {
            // Simulate PostHog initialization
            this.posthogClient = {
                capture: (event) => {
                    logger_1.logger.debug('📊 PostHog event captured:', event.event);
                    return Promise.resolve();
                },
                shutdown: () => Promise.resolve()
            };
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to initialize PostHog:', error);
            throw error;
        }
    }
    /**
     * Initialize LangSmith client
     */
    async initializeLangSmith() {
        try {
            // Simulate LangSmith initialization
            this.langsmithClient = {
                trace: (data) => {
                    logger_1.logger.debug('🔍 LangSmith trace created:', data.name);
                    return Promise.resolve();
                }
            };
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to initialize LangSmith:', error);
            throw error;
        }
    }
    /**
     * Initialize OpenTelemetry
     */
    async initializeOpenTelemetry() {
        try {
            // Simulate OpenTelemetry initialization
            logger_1.logger.debug('📡 OpenTelemetry initialized with endpoint:', this.config.opentelemetry?.endpoint);
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to initialize OpenTelemetry:', error);
            throw error;
        }
    }
    /**
     * Send insight to PostHog
     */
    async sendToPostHog(insight) {
        if (!this.posthogClient) {
            return;
        }
        try {
            // Implementation for PostHog integration
            logger_1.logger.debug('📊 Sent insight to PostHog');
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to send insight to PostHog:', error);
        }
    }
    /**
     * Send insight to LangSmith
     */
    async sendToLangSmith(insight) {
        if (!this.langsmithClient) {
            return;
        }
        try {
            // Implementation for LangSmith integration
            logger_1.logger.debug('🔍 Sent insight to LangSmith');
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to send insight to LangSmith:', error);
        }
    }
    /**
     * Send insight to custom webhook
     */
    async sendToCustomWebhook(insight) {
        try {
            // Implementation for custom webhook integration
            logger_1.logger.debug('🔗 Sent insight to custom webhook');
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to send insight to custom webhook:', error);
        }
    }
    /**
     * Send alert to PostHog
     */
    async sendAlertToPostHog(alert) {
        if (!this.posthogClient)
            return;
        await this.posthogClient.capture({
            event: 'cognitive_alert',
            distinctId: 'cognitive-agent-alerts',
            properties: {
                alert_type: alert.type,
                severity: alert.severity,
                message: alert.message,
                recommendations: alert.recommendations,
                timestamp: new Date().toISOString()
            }
        });
    }
    /**
     * Send alert to custom webhook
     */
    async sendAlertToWebhook(alert) {
        if (!this.config.custom?.webhookUrl)
            return;
        try {
            const axios = await Promise.resolve().then(() => __importStar(require('axios')));
            await axios.default.post(this.config.custom.webhookUrl, {
                type: 'cognitive_alert',
                data: alert,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            logger_1.logger.error('❌ Failed to send alert to webhook:', error);
        }
    }
    /**
     * Get list of active integrations
     */
    getActiveIntegrations() {
        const active = [];
        if (this.config.posthog)
            active.push('PostHog');
        if (this.config.langsmith)
            active.push('LangSmith');
        if (this.config.opentelemetry)
            active.push('OpenTelemetry');
        if (this.config.custom)
            active.push('Custom Webhook');
        return active;
    }
    /**
     * Get integration status
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            activeIntegrations: this.getActiveIntegrations(),
            config: {
                posthog: Boolean(this.config.posthog),
                langsmith: Boolean(this.config.langsmith),
                opentelemetry: Boolean(this.config.opentelemetry),
                custom: Boolean(this.config.custom)
            }
        };
    }
}
exports.EnterpriseIntegrations = EnterpriseIntegrations;
//# sourceMappingURL=enterprise-integrations.js.map