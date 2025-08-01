interface Insight {
    severity: string;
    summary: string;
    recommendations: string[];
    [key: string]: any;
}
export interface EnterpriseConfig {
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
}
export interface AlertData {
    type: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    message: string;
    recommendations: string[];
}
export declare class EnterpriseIntegrations {
    private config;
    private posthogClient?;
    private langsmithClient?;
    private isRunning;
    constructor(config: EnterpriseConfig);
    /**
     * Start enterprise integrations
     */
    start(): Promise<void>;
    /**
     * Stop enterprise integrations
     */
    stop(): Promise<void>;
    /**
     * Send cognitive insight to configured platforms
     */
    sendInsight(insight: Insight): Promise<void>;
    /**
     * Send proactive alert to enterprise platforms
     */
    sendProactiveAlert(alert: Insight): Promise<void>;
    /**
     * Send alert to configured platforms
     */
    sendAlert(alert: AlertData): Promise<void>;
    /**
     * Initialize PostHog client
     */
    private initializePostHog;
    /**
     * Initialize LangSmith client
     */
    private initializeLangSmith;
    /**
     * Initialize OpenTelemetry
     */
    private initializeOpenTelemetry;
    /**
     * Send insight to PostHog
     */
    private sendToPostHog;
    /**
     * Send insight to LangSmith
     */
    private sendToLangSmith;
    /**
     * Send insight to custom webhook
     */
    private sendToCustomWebhook;
    /**
     * Send alert to PostHog
     */
    private sendAlertToPostHog;
    /**
     * Send alert to custom webhook
     */
    private sendAlertToWebhook;
    /**
     * Get list of active integrations
     */
    private getActiveIntegrations;
    /**
     * Get integration status
     */
    getStatus(): any;
}
export {};
//# sourceMappingURL=enterprise-integrations.d.ts.map