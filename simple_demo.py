#!/usr/bin/env python3
"""
Simplified Demo Version - CopadoCon 2025 Hackathon
Works without external dependencies for immediate demonstration
"""

from datetime import datetime, timedelta, timezone
import json
import asyncio
from typing import Dict, List, Any
import os
import sys

# Check if we have the required packages
try:
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("Installing required packages...")
    os.system("pip install fastapi uvicorn python-dotenv")
    print("Please run the script again after installation completes.")
    sys.exit(1)

# Mock data for demonstration
MOCK_INCIDENTS = [
    {
        "id": "INC-20250830-173256",
        "title": "Apex Error: NullPointerException in AccountTriggerHandler",
        "description": "System.NullPointerException: Attempt to de-reference a null object",
        "severity": "high",
        "status": "investigating",
        "created_at": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
        "updated_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "signals_count": 3,
        "actions_count": 2,
        "confidence": 0.85,
        "analysis": {
            "root_cause": "Deployment abc123 introduced null reference in AccountTriggerHandler.updateAccountStatus() method",
            "confidence": 0.85,
            "related_deployments": ["deploy_001"],
            "related_commits": ["abc123def456"],
            "suggested_actions": [
                "Review AccountTriggerHandler.cls line 42",
                "Check null validation in updateAccountStatus method",
                "Consider rollback of deployment abc123"
            ],
            "impact_assessment": "High - Affects all account updates in production"
        },
        "signals": [
            {
                "id": "apex_001",
                "type": "error",
                "source": "salesforce",
                "component": "apex",
                "description": "System.NullPointerException in AccountTriggerHandler",
                "severity": "high",
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
            }
        ],
        "actions_taken": [
            {
                "id": "jira_001",
                "type": "jira_ticket",
                "description": "Created Jira ticket OBS-123",
                "status": "completed",
                "result": {"ticket_key": "OBS-123", "ticket_url": "https://company.atlassian.net/browse/OBS-123"}
            },
            {
                "id": "slack_001", 
                "type": "slack_notification",
                "description": "Sent Slack notification to #alerts",
                "status": "completed",
                "result": {"channel": "#alerts"}
            }
        ]
    },
    {
        "id": "INC-20250830-174512",
        "title": "Deployment Failure: Component compilation failed",
        "description": "Apex class compilation failed during deployment",
        "severity": "critical",
        "status": "resolving",
        "created_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
        "updated_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "signals_count": 2,
        "actions_count": 3,
        "confidence": 0.92,
        "analysis": {
            "root_cause": "Syntax error in OpportunityService.cls introduced in commit def456ghi789",
            "confidence": 0.92,
            "related_deployments": ["deploy_002"],
            "related_commits": ["def456ghi789"],
            "suggested_actions": [
                "Fix syntax error in OpportunityService.cls",
                "Re-run deployment after fix",
                "Update unit tests to catch similar issues"
            ],
            "impact_assessment": "Critical - Deployment blocked, no new features can be released"
        }
    },
    {
        "id": "INC-20250830-175823",
        "title": "Test Failure: AccountTriggerTest.testAccountUpdate",
        "description": "System.AssertException: Assertion Failed in test method",
        "severity": "medium",
        "status": "detected",
        "created_at": (datetime.now(timezone.utc) - timedelta(minutes=8)).isoformat(),
        "updated_at": (datetime.now(timezone.utc) - timedelta(minutes=8)).isoformat(),
        "signals_count": 1,
        "actions_count": 1,
        "confidence": 0.73,
        "analysis": {
            "root_cause": "Test data setup issue - missing required field validation",
            "confidence": 0.73,
            "suggested_actions": [
                "Review test data setup in AccountTriggerTest",
                "Add missing field validations",
                "Update test assertions"
            ]
        }
    }
]

# Initialize FastAPI app
app = FastAPI(
    title="CopadoCon 2025 Hackathon",
    description="Real-time Salesforce monitoring with AI-powered incident analysis",
    version="1.0.0"
)

# Serve static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Static files not required for basic demo

@app.get("/")
async def dashboard():
    """Serve the main dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CopadoCon 2025 Hackathon - Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: slideInDown 0.8s ease-out;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            color: #666;
            margin-bottom: 15px;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 500;
            animation: pulse 2s infinite;
        }
        
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #fff;
            border-radius: 50%;
            animation: pulse-dot 1.5s infinite;
        }
        
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 25px; 
            margin-bottom: 30px; 
        }
        
        .stat-card { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            animation: slideInUp 0.8s ease-out;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .stat-card:hover { 
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }
        
        .stat-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-value { 
            font-size: 3em; 
            font-weight: 700; 
            color: #333;
            margin-bottom: 5px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stat-label { 
            color: #666; 
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .incidents { 
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            animation: slideInUp 0.8s ease-out 0.2s both;
        }
        
        .incidents h2 {
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 25px;
            color: #333;
        }
        
        .incident { 
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0,0,0,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .incident::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 5px;
            transition: all 0.3s ease;
        }
        
        .incident:hover { 
            transform: translateX(5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
            background: rgba(255, 255, 255, 0.95);
        }
        
        .severity-high::before { background: linear-gradient(180deg, #ff6b6b, #ee5a52); }
        .severity-critical::before { background: linear-gradient(180deg, #dc3545, #c82333); }
        .severity-medium::before { background: linear-gradient(180deg, #ffa726, #ff9800); }
        
        .incident-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .incident h3 {
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        
        .incident p {
            color: #666;
            line-height: 1.5;
            margin-bottom: 15px;
        }
        
        .incident-meta {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .confidence { 
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            color: #1565c0;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 500;
            font-size: 0.9em;
        }
        
        .status { 
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-investigating { 
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            color: #856404;
        }
        .status-resolving { 
            background: linear-gradient(135deg, #d1ecf1, #74b9ff);
            color: #0c5460;
        }
        .status-detected { 
            background: linear-gradient(135deg, #f8d7da, #fd79a8);
            color: #721c24;
        }
        
        .severity-badge {
            background: rgba(0,0,0,0.05);
            color: #666;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .timestamp {
            font-size: 0.85em;
            color: #999;
        }
        
        @keyframes slideInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes pulse-dot {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.8; }
        }
        
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-brain"></i> CopadoCon 2025 Hackathon</h1>
            <p>Transforming Salesforce issue resolution from days to minutes with intelligent automation</p>
            <div class="status-badge">
                <div class="pulse-dot"></div>
                Active - Monitoring in real-time
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stat-value">3</div>
                <div class="stat-label">Active Incidents</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
                <div class="stat-value">12</div>
                <div class="stat-label">Resolved Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-clock"></i></div>
                <div class="stat-value">2m</div>
                <div class="stat-label">Avg Resolution</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-robot"></i></div>
                <div class="stat-value">83%</div>
                <div class="stat-label">AI Confidence</div>
            </div>
        </div>
        
        <div class="incidents">
            <h2><i class="fas fa-list-alt"></i> Recent Incidents</h2>
            <div id="incidents-list">
                <div class="loading">
                    <div class="spinner"></div>
                    Loading incidents...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Load incidents with enhanced UI
        fetch('/api/incidents')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('incidents-list');
                container.innerHTML = '';
                
                data.incidents.forEach((incident, index) => {
                    const div = document.createElement('div');
                    div.className = `incident severity-${incident.severity}`;
                    div.style.animationDelay = `${index * 0.1}s`;
                    
                    const createdDate = new Date(incident.created_at);
                    const timeAgo = getTimeAgo(createdDate);
                    
                    div.innerHTML = `
                        <div class="incident-header">
                            <div>
                                <h3><i class="fas fa-bug"></i> ${incident.title}</h3>
                                <p>${incident.description}</p>
                            </div>
                            <div style="text-align: right;">
                                <div class="severity-badge">${incident.severity}</div>
                                <div class="timestamp">${timeAgo}</div>
                            </div>
                        </div>
                        <div class="incident-meta">
                            <span class="status status-${incident.status}">
                                <i class="fas fa-${getStatusIcon(incident.status)}"></i>
                                ${incident.status}
                            </span>
                            <span class="confidence">
                                <i class="fas fa-brain"></i>
                                AI Confidence: ${Math.round(incident.confidence * 100)}%
                            </span>
                        </div>
                    `;
                    
                    div.onclick = () => showIncident(incident.id);
                    container.appendChild(div);
                });
            })
            .catch(error => {
                document.getElementById('incidents-list').innerHTML = 
                    '<div style="text-align: center; color: #666; padding: 20px;">Failed to load incidents</div>';
            });
        
        function getStatusIcon(status) {
            const icons = {
                'investigating': 'search',
                'resolving': 'tools',
                'detected': 'exclamation-circle'
            };
            return icons[status] || 'circle';
        }
        
        function getTimeAgo(date) {
            const now = new Date();
            const diff = now - date;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(minutes / 60);
            
            if (minutes < 60) return `${minutes}m ago`;
            if (hours < 24) return `${hours}h ago`;
            return date.toLocaleDateString();
        }
        
        function showIncident(id) {
            fetch(`/api/incidents/${id}`)
                .then(response => response.json())
                .then(incident => {
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                        background: rgba(0,0,0,0.5); backdrop-filter: blur(5px);
                        display: flex; align-items: center; justify-content: center;
                        z-index: 1000; animation: fadeIn 0.3s ease;
                    `;
                    
                    modal.innerHTML = `
                        <div style="
                            background: white; border-radius: 20px; padding: 30px;
                            max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;
                            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
                        ">
                            <h2 style="margin-bottom: 20px; color: #333;">
                                <i class="fas fa-bug"></i> Incident Details
                            </h2>
                            <div style="margin-bottom: 15px;">
                                <strong>Root Cause:</strong><br>
                                ${incident.analysis?.root_cause || 'Analyzing...'}
                            </div>
                            <div style="margin-bottom: 20px;">
                                <strong>Suggested Actions:</strong><br>
                                ${incident.analysis?.suggested_actions?.map(action => `- ${action}`).join('<br>') || 'None yet'}
                            </div>
                            <button onclick="this.parentElement.parentElement.remove()" style="
                                background: linear-gradient(135deg, #667eea, #764ba2);
                                color: white; border: none; padding: 10px 20px;
                                border-radius: 25px; cursor: pointer; font-weight: 500;
                            ">Close</button>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                    modal.onclick = (e) => {
                        if (e.target === modal) modal.remove();
                    };
                });
        }
        
        // Add fade in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
    """)

@app.get("/api/health", 
         summary="System Health Check",
         description="Comprehensive health status with system metrics and service information",
         response_description="Detailed health status including system performance metrics")
async def health_check():
    """
    ## System Health Check
    
    Returns comprehensive health information including:
    - Service status and uptime
    - System performance metrics (CPU, Memory, Disk)
    - Platform information
    - Demo configuration details
    
    **Perfect for monitoring and debugging!**
    """
    import platform
    import time
    import os
    
    # Try to get system metrics if psutil is available
    system_info = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "architecture": platform.machine()
    }
    
    # Try to add advanced metrics if psutil is available
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.' if os.name == 'nt' else '/')
        uptime_seconds = time.time() - psutil.Process().create_time()
        
        system_info.update({
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": round((disk.used / disk.total) * 100, 1)
            },
            "uptime": {
                "seconds": round(uptime_seconds, 2),
                "human_readable": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s"
            }
        })
    except ImportError:
        # Basic uptime without psutil
        system_info.update({
            "note": "Install psutil for detailed system metrics",
            "uptime": "Available after installing psutil"
        })
    except Exception:
        system_info.update({
            "note": "System metrics temporarily unavailable"
        })
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "service": "CopadoCon 2025 Hackathon",
        "description": "Intelligent Salesforce issue detection and resolution platform",
        "hackathon": {
            "team": "AI Signal Squad",
            "innovation": "AI correlation engine for DevOps observability",
            "impact": "Reduces incident resolution from days to minutes"
        },
        "system": system_info,
        "demo": {
            "mock_incidents": len(MOCK_INCIDENTS),
            "features": [
                "Real-time signal detection",
                "AI-powered root cause analysis (85-92% confidence)",
                "Automated Jira/GitHub/Slack integration",
                "Interactive dashboard with real-time updates"
            ]
        }
    }

@app.get("/api/incidents",
         summary="Get All Incidents",
         description="Retrieve all detected incidents with AI analysis and status information",
         response_description="List of incidents with metadata and AI confidence scores")
async def get_incidents():
    """
    ## Get All Incidents
    
    Returns all detected incidents including:
    - Incident metadata (ID, title, severity, status)
    - AI analysis results with confidence scores
    - Root cause analysis and suggested actions
    - Related deployments and commits
    
    **Essential for monitoring your Salesforce environment!**
    """
    return {"incidents": MOCK_INCIDENTS, "total": len(MOCK_INCIDENTS)}

@app.get("/api/incidents/{incident_id}",
         summary="Get Incident Details", 
         description="Get comprehensive details for a specific incident including AI analysis",
         response_description="Detailed incident information with root cause analysis")
async def get_incident_details(incident_id: str):
    """
    ## Get Incident Details
    
    Retrieve detailed information about a specific incident:
    - Complete incident metadata
    - AI-powered root cause analysis
    - Suggested remediation actions
    - Impact assessment
    - Related code changes and deployments
    
    **Perfect for deep-dive incident investigation!**
    """
    incident = next((inc for inc in MOCK_INCIDENTS if inc["id"] == incident_id), None)
    if not incident:
        return {"error": "Incident not found", "available_incidents": [inc["id"] for inc in MOCK_INCIDENTS]}
    return incident

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "total_incidents": len(MOCK_INCIDENTS),
        "resolved_incidents": len([inc for inc in MOCK_INCIDENTS if inc["status"] == "resolved"]),
        "active_incidents": len([inc for inc in MOCK_INCIDENTS if inc["status"] != "resolved"]),
        "average_resolution_time_seconds": 120,  # 2 minutes
        "recent_incidents_24h": len(MOCK_INCIDENTS),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    print("Starting CopadoCon 2025 Hackathon Demo")
    print("=" * 50)
    print("Dashboard: http://127.0.0.1:8080")
    print("API Docs: http://127.0.0.1:8080/docs") 
    print("Health Check: http://127.0.0.1:8080/api/health")
    print("=" * 50)
    print("Features demonstrated:")
    print("- Real-time incident detection")
    print("- AI-powered root cause analysis") 
    print("- Automated action workflows")
    print("- Interactive dashboard")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
