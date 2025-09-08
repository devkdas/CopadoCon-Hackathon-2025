"""
Data models for incidents and signals
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Severity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Incident status values"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SignalType(Enum):
    """Types of signals that can be detected"""
    ERROR = "error"
    PERFORMANCE = "performance"
    DEPLOYMENT = "deployment"
    TEST_FAILURE = "test_failure"
    LOG_ANOMALY = "log_anomaly"
    MONITORING_ALERT = "monitoring_alert"

class Signal(BaseModel):
    """Represents a detected signal/event"""
    id: str
    type: SignalType
    source: str  # e.g., "salesforce", "github", "copado"
    component: Optional[str] = None  # e.g., "apex_class", "flow", "trigger"
    description: str
    severity: Severity
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    raw_data: Optional[str] = None

class Analysis(BaseModel):
    """AI analysis results"""
    root_cause: Optional[str] = None
    confidence: float = 0.0
    related_deployments: List[str] = []
    related_commits: List[str] = []
    suggested_actions: List[str] = []
    code_changes: List[Dict[str, Any]] = []
    impact_assessment: Optional[str] = None
    analysis_timestamp: datetime = datetime.utcnow()

class Action(BaseModel):
    """Represents an automated action taken"""
    id: str
    type: str  # e.g., "jira_ticket", "github_comment", "slack_notification"
    description: str
    status: str  # e.g., "pending", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

class Incident(BaseModel):
    """Main incident model"""
    id: str
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    signals: List[Signal] = []
    analysis: Optional[Analysis] = None
    actions_taken: List[Action] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    assignee: Optional[str] = None
    tags: List[str] = []
    
    class Config:
        use_enum_values = True
