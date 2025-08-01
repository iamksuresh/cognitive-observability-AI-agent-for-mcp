import { EventEmitter } from 'events';
export interface MCPMessageTrace {
    timestamp: string;
    direction: 'inbound' | 'outbound';
    messageType: string;
    method?: string;
    params?: any;
    result?: any;
    error?: any;
    latency_ms?: number;
    host: string;
    server: string;
}
export interface ComponentInteraction {
    id: string;
    startTime: string;
    endTime: string;
    duration_ms: number;
    messageCount: number;
    successRate: number;
    cognitiveLoad: number;
    method: string;
    server: string;
    host: string;
    messages: MCPMessageTrace[];
}
export interface TraceReport {
    generatedAt: string;
    timeRange: {
        start: string;
        end: string;
    };
    summary: {
        totalInteractions: number;
        totalMessages: number;
        averageCognitiveLoad: number;
        successRate: number;
        mostUsedMethods: Array<{
            method: string;
            count: number;
        }>;
        serversAnalyzed: string[];
    };
    componentInteractions: ComponentInteraction[];
    cognitiveAnalysis: {
        averageLatency: number;
        frictionPoints: Array<{
            method: string;
            issue: string;
            severity: 'low' | 'medium' | 'high';
            recommendation: string;
        }>;
        usabilityScore: number;
    };
}
export interface UsabilityReport {
    generatedAt: string;
    host: string;
    timeRange: string;
    cognitiveLoad: {
        overall: number;
        breakdown: {
            promptComplexity: number;
            contextSwitching: number;
            retryFrustration: number;
            configurationFriction: number;
            integrationCognition: number;
        };
    };
    usabilityInsights: {
        strengths: string[];
        weaknesses: string[];
        recommendations: string[];
    };
    performanceMetrics: {
        averageResponseTime: number;
        successRate: number;
        errorPatterns: Array<{
            pattern: string;
            frequency: number;
            impact: string;
        }>;
    };
    benchmarkComparison: {
        vsIndustryAverage: number;
        vsLastWeek: number;
        trendDirection: 'improving' | 'declining' | 'stable';
    };
}
export declare class CognitiveAnalyzer extends EventEmitter {
    private isRunning;
    private messageBuffer;
    private interactions;
    private cognitiveLoad;
    private reportsDirectory;
    constructor();
    private ensureReportsDirectory;
    /**
     * Start the cognitive analysis engine
     */
    start(): void;
    /**
     * Stop the cognitive analysis engine
     */
    stop(): void;
    /**
     * Analyze MCP message for cognitive patterns
     */
    analyzeMessage(message: any, host: string, server: string): void;
    /**
     * Process a complete interaction for component analysis
     */
    private processInteraction;
    /**
     * Calculate cognitive load for a specific interaction with enhanced algorithms
     */
    private calculateInteractionCognitiveLoad;
    /**
     * Enhanced cognitive load calculation based on recent patterns
     */
    private updateCognitiveLoad;
    /**
     * Calculate prompt complexity based on method usage patterns
     */
    private calculatePromptComplexity;
    /**
     * Calculate context switching based on host/server/method changes
     */
    private calculateContextSwitching;
    /**
     * Enhanced retry frustration calculation (renamed to avoid duplicate)
     */
    private calculateEnhancedRetryFrustration;
    /**
     * Calculate configuration friction based on error patterns
     */
    private calculateConfigurationFriction;
    /**
     * Calculate integration cognition based on system complexity
     */
    private calculateIntegrationCognition;
    /**
     * Detect friction patterns and emit insights
     */
    private detectFrictionPatterns;
    /**
     * Generate component trace report
     */
    generateTraceReport(timeRange?: {
        start: Date;
        end: Date;
    }): Promise<TraceReport>;
    /**
     * Generate usability report
     */
    generateUsabilityReport(host: string, timeRange?: string): Promise<UsabilityReport>;
    /**
     * Helper methods for report generation
     */
    private identifyFrictionPoints;
    private identifyStrengths;
    private identifyWeaknesses;
    private generateRecommendations;
    private identifyErrorPatterns;
    /**
     * Listen for insights
     */
    onInsight(callback: (insight: any) => void): void;
    /**
     * Get current status
     */
    getStatus(): {
        isRunning: boolean;
        cognitiveLoad: number;
        activeSessions: number;
        insightsGenerated: number;
        lastAnalysis: string | null;
        messageCount: number;
        interactionCount: number;
    };
}
//# sourceMappingURL=cognitive-analyzer.d.ts.map