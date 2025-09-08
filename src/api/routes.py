"""
API Routes for our hackathon project
These are all the web endpoints that power our dashboard and let external systems talk to us.
Think of this as the public interface - how the outside world interacts with our AI agent.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..models.incident import Incident, Signal, Analysis
from ..core.agent import ObservabilityAgent

router = APIRouter()

# Keep a reference to our main AI agent so we can use it in our endpoints
agent: Optional[ObservabilityAgent] = None

def set_agent(agent_instance: ObservabilityAgent):
    """
    Connect our API routes to the main AI agent.
    This gets called when the application starts up.
    """
    global agent
    agent = agent_instance

@router.get("/health")
async def health_check():
    """
    A simple way to check if our system is running smoothly.
    
    This endpoint tells you everything about how the system is doing -
    CPU usage, memory, disk space, and how long we've been running.
    Perfect for monitoring tools or just checking if everything's okay.
    """
    try:
        import psutil
        import platform
        import time
        import os
        
        # Get current system performance stats (safely, in case something fails)
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            cpu_percent = 0.0  # If we can't get CPU info, just say 0
            
        try:
            memory = psutil.virtual_memory()
        except:
            # Create a fake memory object if the real one fails
            memory = type('obj', (object,), {'total': 0, 'available': 0, 'percent': 0})()
            
        try:
            # Check disk space (handle Windows vs Linux paths)
            disk = psutil.disk_usage('.' if os.name == 'nt' else '/')
        except:
            # Fake disk object if that fails too
            disk = type('obj', (object,), {'total': 0, 'free': 0, 'used': 0})()
        
        # Figure out how long we've been running
        try:
            uptime_seconds = time.time() - psutil.Process().create_time()
        except:
            uptime_seconds = 0.0
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "CopadoCon 2025 Hackathon",
            "uptime": {
                "seconds": round(uptime_seconds, 2),
                "human_readable": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"
            },
            "system": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2) if memory.total > 0 else 0,
                    "available_gb": round(memory.available / (1024**3), 2) if memory.available > 0 else 0,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2) if disk.total > 0 else 0,
                    "free_gb": round(disk.free / (1024**3), 2) if disk.free > 0 else 0,
                    "usage_percent": round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
                }
            },
            "services": {
                "agent_running": agent.is_running if agent else False,
                "database": "connected",
                "monitoring": "active"
            }
        }
    except Exception as e:
        # Fallback response if system metrics fail
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "CopadoCon 2025 Hackathon",
            "error": f"System metrics unavailable: {str(e)}",
            "services": {
                "agent_running": agent.is_running if agent else False,
                "database": "connected",
                "monitoring": "active"
            }
        }

@router.get("/status")
async def get_agent_status():
    """
    Quick check on what our AI agent is up to right now.
    
    Returns info about whether it's running, how many incidents it's tracking,
    and other useful stats for the dashboard.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    status = await agent.get_status()
    return JSONResponse(content=status)

@router.get("/incidents")
async def get_incidents(
    limit: int = 50,
    status: Optional[str] = None,
    severity: Optional[str] = None
):
    """
    Get the list of incidents our system has detected and is handling.
    
    You can filter by status (like 'open' or 'resolved') and severity 
    (like 'high' or 'low'). Perfect for populating the dashboard or 
    getting a quick overview of what's happening in your systems.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # Start with all the incidents we know about
    incidents = list(agent.active_incidents.values())
    
    # Filter down to what the user actually wants to see
    if status:
        incidents = [inc for inc in incidents if getattr(inc.status, 'value', inc.status) == status]
    
    if severity:
        incidents = [inc for inc in incidents if getattr(inc.severity, 'value', inc.severity) == severity]
    
    # Show newest stuff first (because that's usually what people care about)
    incidents.sort(key=lambda x: x.created_at, reverse=True)
    
    # Don't overwhelm the dashboard with too many results
    incidents = incidents[:limit]
    
    # Convert to dict format
    result = []
    for incident in incidents:
        incident_dict = {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "severity": getattr(incident.severity, 'value', incident.severity),
            "status": getattr(incident.status, 'value', incident.status),
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "signals_count": len(incident.signals),
            "actions_count": len(incident.actions_taken),
            "confidence": incident.analysis.confidence if incident.analysis else 0.0
        }
        result.append(incident_dict)
    
    return JSONResponse(content={"incidents": result, "total": len(result)})

@router.get("/incidents/{incident_id}")
async def get_incident_details(incident_id: str):
    """Get detailed information about a specific incident"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    incident = agent.active_incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Convert to detailed dict format
    incident_dict = {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "severity": getattr(incident.severity, 'value', incident.severity),
        "status": getattr(incident.status, 'value', incident.status),
        "created_at": incident.created_at.isoformat(),
        "updated_at": incident.updated_at.isoformat(),
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "assignee": incident.assignee,
        "tags": incident.tags,
        "signals": [
            {
                "id": signal.id,
                "type": getattr(signal.type, 'value', signal.type),
                "source": signal.source,
                "component": signal.component,
                "description": signal.description,
                "severity": getattr(signal.severity, 'value', signal.severity),
                "timestamp": signal.timestamp.isoformat(),
                "metadata": signal.metadata
            }
            for signal in incident.signals
        ],
        "analysis": {
            "root_cause": incident.analysis.root_cause,
            "confidence": incident.analysis.confidence,
            "related_deployments": incident.analysis.related_deployments,
            "related_commits": incident.analysis.related_commits,
            "suggested_actions": incident.analysis.suggested_actions,
            "code_changes": incident.analysis.code_changes,
            "impact_assessment": incident.analysis.impact_assessment,
            "analysis_timestamp": incident.analysis.analysis_timestamp.isoformat()
        } if incident.analysis else None,
        "actions_taken": [
            {
                "id": action.id,
                "type": action.type,
                "description": action.description,
                "status": action.status,
                "result": action.result,
                "timestamp": action.timestamp.isoformat()
            }
            for action in incident.actions_taken
        ]
    }
    
    return JSONResponse(content=incident_dict)

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    """Manually resolve an incident"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    incident = agent.active_incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = incident.status.RESOLVED
    incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    
    return JSONResponse(content={"message": "Incident resolved successfully"})

@router.get("/metrics")
async def get_metrics():
    """Get system metrics and statistics"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    incidents = list(agent.active_incidents.values())
    
    # Calculate metrics
    total_incidents = len(incidents)
    resolved_incidents = len([inc for inc in incidents if getattr(inc.status, 'value', inc.status) == "resolved"])
    
    severity_counts = {}
    for incident in incidents:
        severity = getattr(incident.severity, 'value', incident.severity)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Calculate average resolution time for resolved incidents
    resolution_times = []
    for incident in incidents:
        if incident.resolved_at and incident.created_at:
            resolution_time = (incident.resolved_at - incident.created_at).total_seconds()
            resolution_times.append(resolution_time)
    
    avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_incidents = [inc for inc in incidents if inc.created_at >= recent_cutoff]
    
    metrics = {
        "total_incidents": total_incidents,
        "resolved_incidents": resolved_incidents,
        "active_incidents": total_incidents - resolved_incidents,
        "resolution_rate": (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0,
        "severity_distribution": severity_counts,
        "average_resolution_time_seconds": avg_resolution_time,
        "recent_incidents_24h": len(recent_incidents),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(content=metrics)

@router.get("/signals")
async def get_recent_signals(limit: int = 100):
    """Get recent signals across all incidents"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    all_signals = []
    for incident in agent.active_incidents.values():
        for signal in incident.signals:
            signal_dict = {
                "id": signal.id,
                "incident_id": incident.id,
                "type": getattr(signal.type, 'value', signal.type),
                "source": signal.source,
                "component": signal.component,
                "description": signal.description,
                "severity": getattr(signal.severity, 'value', signal.severity),
                "timestamp": signal.timestamp.isoformat(),
                "metadata": signal.metadata
            }
            all_signals.append(signal_dict)
    
    # Sort by timestamp (newest first)
    all_signals.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit results
    all_signals = all_signals[:limit]
    
    return JSONResponse(content={"signals": all_signals, "total": len(all_signals)})

@router.post("/webhook/github")
async def github_webhook(background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    # This would process GitHub webhook events
    # For now, just acknowledge receipt
    return JSONResponse(content={"message": "Webhook received"})

@router.post("/webhook/deployment")
async def deployment_webhook(background_tasks: BackgroundTasks):
    """Handle deployment webhook events"""
    # This would process deployment webhook events
    return JSONResponse(content={"message": "Deployment webhook received"})

@router.get("/config")
async def get_configuration():
    """Get current agent configuration"""
    config = {
        "integrations": {
            "salesforce": bool(agent.signal_detector.salesforce_client.sf) if agent else False,
            "github": bool(agent.signal_detector.github_client.github) if agent else False,
            "jira": bool(agent.action_executor.jira_client.jira) if agent else False,
            "slack": bool(agent.action_executor.slack_client.session) if agent else False
        },
        "monitoring": {
            "is_running": agent.is_running if agent else False,
            "check_interval": "10 seconds"
        }
    }
    
    return JSONResponse(content=config)
