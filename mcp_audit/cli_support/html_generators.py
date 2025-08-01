"""
HTML generation functions extracted from the main CLI.
These generate the detailed HTML reports with cognitive load analysis.
"""

from typing import Dict, Any, Union


def generate_enhanced_trace_html_report(report_data):
    """Generate HTML version of trace report."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Trace Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .metric {{ font-size: 2em; font-weight: bold; color: #667eea; }}
            .trace {{ background: white; margin: 15px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
            .trace-header {{ font-weight: bold; margin-bottom: 10px; }}
            .trace-details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; }}
            .success {{ border-left-color: #28a745; }}
            .error {{ border-left-color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 MCP Trace Report</h1>
                <p>Generated at: {report_data.get('generated_at', 'Unknown')}</p>
            </div>
    """
    
    # Add summary if available
    if 'summary' in report_data:
        summary = report_data['summary']
        html_content += f"""
            <div class="summary-cards">
                <div class="card">
                    <div class="metric">{summary.get('total_interactions', 0)}</div>
                    <div>Total Interactions</div>
                </div>
                <div class="card">
                    <div class="metric">{summary.get('successful_interactions', 0)}</div>
                    <div>Successful</div>
                </div>
                <div class="card">
                    <div class="metric">{summary.get('error_count', 0)}</div>
                    <div>Errors</div>
                </div>
            </div>
        """
    
    # Add traces
    traces = report_data.get('traces', [])
    for trace in traces:
        status_class = 'success' if trace.get('success', True) else 'error'
        html_content += f"""
            <div class="trace {status_class}">
                <div class="trace-header">
                    {trace.get('method', 'Unknown Method')} - {trace.get('server_name', 'Unknown Server')}
                </div>
                <div class="timestamp">{trace.get('timestamp', '')}</div>
                <div class="trace-details">
                    <strong>Request:</strong> {str(trace.get('payload', {}))[:200]}...
                </div>
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content


# Note: The other massive HTML functions will be added in the next step
# to keep this modular and manageable