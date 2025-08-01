"""
Configuration management for MCP Usability Audit Agent.

Handles environment variables, default settings, and report output configuration.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class AuditConfig(BaseModel):
    """Configuration settings for the MCP audit agent."""
    
    # Report output configuration
    report_output_dir: str = Field(
        default_factory=lambda: os.getenv("MCP_AUDIT_REPORTS_DIR", os.getcwd()),
        description="Directory where audit reports will be saved"
    )
    
    # Monitoring configuration
    enable_real_time_monitoring: bool = Field(
        default=True,
        description="Enable real-time monitoring of MCP interactions"
    )
    
    # Analysis configuration
    cognitive_load_threshold: float = Field(
        default=75.0,
        description="Threshold for cognitive load alerts (0-100)"
    )
    
    friction_detection_sensitivity: str = Field(
        default="medium",
        description="Sensitivity level for friction detection (low, medium, high)"
    )
    
    # Tracing configuration
    enable_component_tracing: bool = Field(
        default=True,
        description="Enable detailed component interaction tracing"
    )
    
    trace_events_detail_level: str = Field(
        default="standard",
        description="Detail level for trace events (minimal, standard, verbose)"
    )
    
    # Session configuration
    session_timeout_minutes: int = Field(
        default=30,
        description="Session timeout in minutes"
    )
    
    # Export configuration
    auto_export_reports: bool = Field(
        default=True,
        description="Automatically export reports after each session"
    )
    
    export_format: str = Field(
        default="json",
        description="Default export format (json, csv, xml)"
    )
    
    def ensure_report_directory(self) -> Path:
        """Ensure the report output directory exists and return its path."""
        report_dir = Path(self.report_output_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir
    
    def get_report_path(self, filename: str) -> Path:
        """Get the full path for a report file."""
        return self.ensure_report_directory() / filename
    
    @classmethod
    def from_env(cls) -> "AuditConfig":
        """Create configuration from environment variables."""
        return cls(
            report_output_dir=os.getenv("MCP_AUDIT_REPORTS_DIR", os.getcwd()),
            enable_real_time_monitoring=os.getenv("MCP_AUDIT_REAL_TIME", "true").lower() == "true",
            cognitive_load_threshold=float(os.getenv("MCP_AUDIT_COGNITIVE_THRESHOLD", "75.0")),
            friction_detection_sensitivity=os.getenv("MCP_AUDIT_FRICTION_SENSITIVITY", "medium"),
            enable_component_tracing=os.getenv("MCP_AUDIT_COMPONENT_TRACING", "true").lower() == "true",
            trace_events_detail_level=os.getenv("MCP_AUDIT_TRACE_DETAIL", "standard"),
            session_timeout_minutes=int(os.getenv("MCP_AUDIT_SESSION_TIMEOUT", "30")),
            auto_export_reports=os.getenv("MCP_AUDIT_AUTO_EXPORT", "true").lower() == "true",
            export_format=os.getenv("MCP_AUDIT_EXPORT_FORMAT", "json")
        )


# Global configuration instance
config = AuditConfig.from_env()


def get_config() -> AuditConfig:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> None:
    """Update global configuration with new values."""
    global config
    current_data = config.model_dump()
    current_data.update(kwargs)
    config = AuditConfig(**current_data) 