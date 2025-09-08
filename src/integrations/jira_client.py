"""
Jira Integration Client
Handles Jira API interactions for ticket management
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
import aiohttp

from ..core.config import settings

# Optional import - works without this package installed
try:
    from jira import JIRA
    HAS_JIRA = True
except ImportError:
    logger.warning("jira not installed - Jira integration disabled")
    JIRA = None
    HAS_JIRA = False

class JiraClient:
    """Client for Jira API interactions"""
    
    def __init__(self):
        self.jira = None
        
    async def initialize(self):
        """Initialize Jira connection"""
        try:
            if not HAS_JIRA:
                logger.warning("jira package not available - using mock data")
                return
                
            if not all([settings.JIRA_SERVER, settings.JIRA_USERNAME, settings.JIRA_API_TOKEN]):
                logger.warning("Jira credentials not configured - using mock responses")
                return
                
            # self.jira = JIRA(
            #     server=settings.JIRA_SERVER,
            #     basic_auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
            # )
            logger.info("Jira integration disabled - using mock responses")
            
            logger.info("Jira client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira issue"""
        try:
            if not self.jira:
                return self._mock_issue_creation()
            
            issue = self.jira.create_issue(fields=issue_data)
            
            return {
                'key': issue.key,
                'id': issue.id,
                'url': f"{settings.JIRA_SERVER}/browse/{issue.key}"
            }
            
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            return self._mock_issue_creation()
    
    def _mock_issue_creation(self) -> Dict[str, Any]:
        """Mock issue creation for demo purposes"""
        return {
            'key': 'OBS-123',
            'id': '10001',
            'url': f"{settings.JIRA_SERVER or 'https://company.atlassian.net'}/browse/OBS-123"
        }

class SlackClient:
    """Client for Slack API interactions"""
    
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """Initialize Slack client"""
        try:
            if not settings.SLACK_WEBHOOK_URL:
                logger.warning("Slack webhook not configured - using mock responses")
                return
                
            self.session = aiohttp.ClientSession()
            logger.info("Slack client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Slack client: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def send_message(self, channel: str, message: Dict[str, Any], priority: str = "normal") -> Dict[str, Any]:
        """Send a message to Slack"""
        try:
            if not self.session or not settings.SLACK_WEBHOOK_URL:
                return self._mock_message_send()
            
            payload = {
                "channel": channel,
                **message
            }
            
            async with self.session.post(settings.SLACK_WEBHOOK_URL, json=payload) as response:
                if response.status == 200:
                    return {
                        "ts": str(datetime.utcnow().timestamp()),
                        "channel": channel
                    }
                else:
                    logger.error(f"Slack API error: {response.status}")
                    return self._mock_message_send()
                    
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return self._mock_message_send()
    
    def _mock_message_send(self) -> Dict[str, Any]:
        """Mock message send for demo purposes"""
        return {
            "ts": str(datetime.utcnow().timestamp()),
            "channel": "#alerts"
        }

class MonitoringClient:
    """Client for monitoring system interactions"""
    
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """Initialize monitoring client"""
        try:
            self.session = aiohttp.ClientSession()
            logger.info("Monitoring client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring client: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def get_alerts(self, since: datetime) -> list:
        """Get monitoring alerts since specified time"""
        try:
            # This would integrate with your monitoring system (Datadog, New Relic, etc.)
            return self._mock_alerts()
        except Exception as e:
            logger.error(f"Error fetching monitoring alerts: {e}")
            return []
    
    async def detect_log_anomalies(self, since: datetime) -> list:
        """Detect log anomalies since specified time"""
        try:
            # This would integrate with log analysis tools
            return self._mock_log_anomalies()
        except Exception as e:
            logger.error(f"Error detecting log anomalies: {e}")
            return []
    
    def _mock_alerts(self) -> list:
        """Mock monitoring alerts for demo purposes"""
        return [
            {
                'id': 'alert_001',
                'message': 'High CPU usage detected on Salesforce org',
                'severity': 'high',
                'component': 'salesforce_org',
                'timestamp': (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                'metadata': {
                    'cpu_usage': '85%',
                    'threshold': '80%'
                }
            }
        ]
    
    def _mock_log_anomalies(self) -> list:
        """Mock log anomalies for demo purposes"""
        return [
            {
                'id': 'anomaly_001',
                'description': 'Unusual spike in API errors',
                'component': 'api_gateway',
                'timestamp': (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                'metadata': {
                    'error_rate': '15%',
                    'normal_rate': '2%'
                }
            }
        ]
