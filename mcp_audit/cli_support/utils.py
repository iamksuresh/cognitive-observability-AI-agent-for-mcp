"""
Utility functions extracted from the main CLI.
"""

from typing import Optional
from rich.console import Console

console = Console()


def parse_time_duration(since: Optional[str]) -> float:
    """Parse time duration string and return hours as float.
    
    Supported formats:
    - "15m" -> 0.25 hours (15 minutes)
    - "2h" -> 2.0 hours
    - "3d" -> 72.0 hours (3 days)
    
    Args:
        since: Time duration string (e.g., "15m", "2h", "3d")
        
    Returns:
        Hours as float (default: 24.0)
    """
    if not since:
        return 24.0  # Default to 24 hours
    
    try:
        if since.endswith('m'):
            minutes = int(since[:-1])
            return minutes / 60.0  # Convert minutes to hours
        elif since.endswith('h'):
            return float(since[:-1])
        elif since.endswith('d'):
            days = int(since[:-1])
            return days * 24.0  # Convert days to hours
        else:
            # Try to parse as just a number (assume hours)
            return float(since)
    except (ValueError, IndexError):
        console.print(f"[yellow]⚠️ Invalid time format '{since}', using default 24h[/yellow]")
        return 24.0


def _display_report_summary(report):
    """Display a brief summary of the usability report."""
    # Handle both dict and object types
    if hasattr(report, 'model_dump'):
        data = report.model_dump()
    elif hasattr(report, '__dict__'):
        data = report.__dict__
    else:
        data = report
    
    session_summary = data.get('session_summary', {})
    if session_summary:
        console.print(f"   • Total Sessions: {session_summary.get('total_sessions', 0)}")
        console.print(f"   • Success Rate: {session_summary.get('success_rate', 0):.1%}")
        console.print(f"   • Avg Response Time: {session_summary.get('avg_response_time_ms', 0):.0f}ms")
    
    console.print(f"   • Overall Score: {data.get('overall_usability_score', 0)}")
    console.print(f"   • Grade: {data.get('grade', 'N/A')}")