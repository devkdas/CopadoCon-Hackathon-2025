"""
Slack integration client for team notifications and alerts
Sends notifications about incidents, status updates, and system alerts to Slack channels
"""

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    WebClient = None
    SlackApiError = Exception
    SLACK_AVAILABLE = False
    from loguru import logger
    logger.warning("slack-sdk not installed - Slack integration disabled")

import asyncio
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from ..core.config import settings

class SlackClient:
    """
    Slack integration for sending notifications and alerts
    """
    
    def __init__(self):
        """Initialize Slack client if token is available"""
        self.client = None
        self.enabled = False
        
        if not SLACK_AVAILABLE:
            logger.warning("Slack SDK not available - notifications disabled")
            return
            
        if settings.SLACK_BOT_TOKEN:
            try:
                self.client = WebClient(token=settings.SLACK_BOT_TOKEN)
                self.enabled = True
                logger.info("Slack client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Slack client: {e}")
        else:
            logger.warning("SLACK_BOT_TOKEN not configured - Slack notifications disabled")
    
    async def initialize(self):
        """Initialize the Slack client (async setup if needed)"""
        if self.enabled:
            logger.info("Slack client initialization complete")
        return True
    
    async def send_message(self, channel: str, message: str, blocks: Optional[List[Dict]] = None) -> bool:
        """
        Send a message to a Slack channel
        """
        if not self.enabled:
            logger.warning("Slack not enabled - message not sent")
            return False
            
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat_postMessage(
                    channel=channel,
                    text=message,
                    blocks=blocks
                )
            )
            
            if response["ok"]:
                logger.info(f"Message sent to Slack channel {channel}")
                return True
            else:
                logger.error(f"Failed to send Slack message: {response.get('error')}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False
    
    async def send_incident_alert(self, incident: Dict[str, Any]) -> bool:
        """
        Send an incident alert to Slack with formatted blocks
        """
        if not self.enabled:
            return False
            
        try:
            severity_color = {
                "critical": "#FF0000",
                "high": "#FF6600", 
                "medium": "#FFCC00",
                "low": "#00CC00"
            }.get(incident.get("severity", "medium"), "#FFCC00")
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Incident Alert: {incident.get('title', 'Unknown Issue')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:* {incident.get('severity', 'Unknown')}"
                        },
                        {
                            "type": "mrkdwn", 
                            "text": f"*Source:* {incident.get('source', 'Unknown')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {incident.get('status', 'New')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*ID:* {incident.get('id', 'N/A')}"
                        }
                    ]
                }
            ]
            
            if incident.get("description"):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{incident['description']}"
                    }
                })
            
            if incident.get("ai_analysis"):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn", 
                        "text": f"*AI Analysis:*\n{incident['ai_analysis']}"
                    }
                })
            
            message = f"Incident Alert: {incident.get('title', 'Unknown Issue')} - Severity: {incident.get('severity', 'Unknown')}"
            
            return await self.send_message("#alerts", message, blocks)
            
        except Exception as e:
            logger.error(f"Error sending incident alert: {e}")
            return False
    
    async def send_status_update(self, message: str, channel: str = "#general") -> bool:
        """
        Send a status update message
        """
        if not self.enabled:
            return False
            
        try:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*System Status Update*\n{message}"
                    }
                }
            ]
            
            return await self.send_message(channel, f"System Status: {message}", blocks)
            
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test the Slack connection
        """
        if not self.enabled:
            return False
            
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.auth_test()
            )
            
            if response["ok"]:
                logger.info(f"Slack connection test successful - Bot: {response.get('user')}")
                return True
            else:
                logger.error(f"Slack connection test failed: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Slack connection test error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup Slack client resources"""
        logger.info("Slack client cleanup complete")
        return True

# Global Slack client instance
slack_client = SlackClient()
