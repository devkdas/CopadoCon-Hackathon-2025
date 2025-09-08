"""
Monitoring client for system health and performance metrics
Collects and reports on system status, performance indicators, and health checks
"""

import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from ..core.config import settings

class MonitoringClient:
    """
    Monitors system health, performance, and application metrics
    """
    
    def __init__(self):
        """Initialize the monitoring client"""
        self.start_time = time.time()
        logger.info("Monitoring client initialized")
        
    async def initialize(self):
        """Initialize the monitoring client (async setup if needed)"""
        logger.info("Monitoring client initialization complete")
        return True
        
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health metrics
        """
        try:
            # CPU and Memory metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Application uptime
            uptime = time.time() - self.start_time
            
            health_data = {
                "status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
                "uptime_seconds": round(uptime, 2),
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "timestamp": time.time()
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error collecting system health metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_application_metrics(self) -> Dict[str, Any]:
        """
        Get application-specific metrics and performance data
        """
        try:
            metrics = {
                "app_status": "running",
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "debug_mode": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "integrations": {
                    "salesforce": bool(settings.SALESFORCE_USERNAME),
                    "github": bool(settings.GITHUB_TOKEN),
                    "jira": bool(settings.JIRA_SERVER),
                    "openai": bool(settings.OPENAI_API_KEY),
                    "slack": bool(settings.SLACK_BOT_TOKEN)
                },
                "timestamp": time.time()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def check_dependencies(self) -> Dict[str, bool]:
        """
        Check if all required dependencies and integrations are available
        """
        dependencies = {}
        
        # Check core dependencies
        try:
            import fastapi
            dependencies["fastapi"] = True
        except ImportError:
            dependencies["fastapi"] = False
            
        try:
            import uvicorn
            dependencies["uvicorn"] = True
        except ImportError:
            dependencies["uvicorn"] = False
            
        # Check integration dependencies
        try:
            import simple_salesforce
            dependencies["simple_salesforce"] = True
        except ImportError:
            dependencies["simple_salesforce"] = False
            
        try:
            import github
            dependencies["github"] = True
        except ImportError:
            dependencies["github"] = False
            
        try:
            import jira
            dependencies["jira"] = True
        except ImportError:
            dependencies["jira"] = False
            
        try:
            import openai
            dependencies["openai"] = True
        except ImportError:
            dependencies["openai"] = False
            
        return dependencies
    
    async def get_alerts(self, since: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Get current system alerts and monitoring notifications
        """
        try:
            alerts = []
            system_health = await self.get_system_health()
            
            # Check CPU usage
            if system_health.get("cpu_percent", 0) > 80:
                alerts.append({
                    "id": f"cpu-alert-{int(time.time())}",
                    "type": "cpu_high",
                    "severity": "high" if system_health["cpu_percent"] > 90 else "medium",
                    "message": f"High CPU usage: {system_health['cpu_percent']:.1f}%",
                    "timestamp": time.time()
                })
            
            # Check memory usage
            memory_percent = system_health.get("memory", {}).get("percent", 0)
            if memory_percent > 85:
                alerts.append({
                    "id": f"memory-alert-{int(time.time())}",
                    "type": "memory_high", 
                    "severity": "high" if memory_percent > 95 else "medium",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "timestamp": time.time()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    async def detect_log_anomalies(self, since: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Detect anomalies in system and application logs
        """
        try:
            anomalies = []
            
            # Mock log anomaly detection (in real implementation, this would analyze actual logs)
            if time.time() % 30 < 5:  # Simulate occasional anomalies
                anomalies.append({
                    "id": f"log-anomaly-{int(time.time())}",
                    "type": "error_spike",
                    "severity": "medium",
                    "message": "Unusual increase in error log entries detected",
                    "details": "Error rate increased by 200% in the last 5 minutes",
                    "timestamp": time.time()
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting log anomalies: {e}")
            return []

    async def get_full_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system and application status
        """
        try:
            system_health = await self.get_system_health()
            app_metrics = await self.get_application_metrics()
            dependencies = await self.check_dependencies()
            
            return {
                "overall_status": "healthy" if system_health.get("status") == "healthy" else "degraded",
                "system": system_health,
                "application": app_metrics,
                "dependencies": dependencies,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting full status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def cleanup(self):
        """Cleanup monitoring client resources"""
        logger.info("Monitoring client cleanup complete")
        return True

# Global monitoring client instance
monitoring_client = MonitoringClient()
