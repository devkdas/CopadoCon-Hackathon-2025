"""
Automated Action Executor
Executes automated remediation actions based on incident analysis
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
import json

from ..models.incident import Incident, Action, Analysis
from ..integrations.jira_client import JiraClient
from ..integrations.github_client import GitHubClient
from ..integrations.slack_client import SlackClient
from ..core.config import settings

class ActionExecutor:
    """Executes automated actions for incident resolution"""
    
    def __init__(self):
        self.jira_client = JiraClient()
        self.github_client = GitHubClient()
        self.slack_client = SlackClient()
        
    async def initialize(self):
        """Initialize action executor"""
        try:
            await self.jira_client.initialize()
            await self.github_client.initialize()
            await self.slack_client.initialize()
            logger.info("Action executor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize action executor: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.jira_client.cleanup()
        await self.github_client.cleanup()
        await self.slack_client.cleanup()
    
    async def execute_actions(self, incident: Incident) -> List[Action]:
        """Execute all appropriate actions for an incident"""
        actions = []
        
        try:
            logger.debug(f"Executing actions for incident {incident.id}")
            
            # Determine which actions to take based on analysis
            action_plan = self._determine_actions(incident)
            
            # Execute actions concurrently
            action_tasks = []
            
            if action_plan.get("create_jira_ticket"):
                action_tasks.append(self._create_jira_ticket(incident))
            
            if action_plan.get("comment_on_pr"):
                action_tasks.append(self._comment_on_pr(incident))
            
            if action_plan.get("send_slack_notification"):
                action_tasks.append(self._send_slack_notification(incident))
            
            if action_plan.get("create_github_issue"):
                action_tasks.append(self._create_github_issue(incident))
            
            if action_plan.get("suggest_rollback"):
                action_tasks.append(self._suggest_rollback(incident))
            
            # Execute all actions
            if action_tasks:
                results = await asyncio.gather(*action_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Action):
                        actions.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Action execution failed: {result}")
            
            logger.debug(f"Executed {len(actions)} actions for incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Error executing actions for incident {incident.id}: {e}")
        
        return actions
    
    def _determine_actions(self, incident: Incident) -> Dict[str, bool]:
        """Determine which actions should be taken"""
        action_plan = {
            "create_jira_ticket": False,
            "comment_on_pr": False,
            "send_slack_notification": False,
            "create_github_issue": False,
            "suggest_rollback": False
        }
        
        analysis = incident.analysis
        if not analysis:
            return action_plan
        
        # Always send Slack notification for high confidence issues
        if analysis.confidence > 0.7:
            action_plan["send_slack_notification"] = True
        
        # Create Jira ticket for medium+ confidence issues
        if analysis.confidence > 0.5:
            action_plan["create_jira_ticket"] = True
        
        # Comment on PR if related commits identified
        if analysis.related_commits and analysis.confidence > 0.6:
            action_plan["comment_on_pr"] = True
        
        # Create GitHub issue for code-related problems
        if any("code" in action.lower() for action in analysis.suggested_actions):
            action_plan["create_github_issue"] = True
        
        # Suggest rollback for deployment-related high-severity issues
        severity_value = getattr(incident.severity, 'value', incident.severity)
        if (analysis.related_deployments and 
            severity_value in ["high", "critical"] and
            analysis.confidence > 0.8):
            action_plan["suggest_rollback"] = True
        
        return action_plan
    
    async def _create_jira_ticket(self, incident: Incident) -> Action:
        """Create a Jira ticket for the incident"""
        action = Action(
            id=f"jira-{incident.id}-{datetime.utcnow().strftime('%H%M%S')}",
            type="jira_ticket",
            description="Create Jira ticket for incident",
            status="pending"
        )
        
        try:
            # Prepare ticket data
            ticket_data = self._prepare_jira_ticket_data(incident)
            
            # Create ticket
            ticket = await self.jira_client.create_issue(ticket_data)
            ticket_key = ticket.get("key", "UNKNOWN") if isinstance(ticket, dict) else str(ticket)
            
            action.result = {
                "ticket_key": ticket_key,
                "ticket_url": f"{settings.JIRA_SERVER}/browse/{ticket_key}"
            }
            
            logger.debug(f"Created Jira ticket {ticket_key} for incident {incident.id}")
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            logger.error(f"Failed to create Jira ticket: {e}")
        
        return action
    
    async def _comment_on_pr(self, incident: Incident) -> Action:
        """Comment on related pull requests"""
        action = Action(
            id=f"gh-comment-{incident.id}-{datetime.utcnow().strftime('%H%M%S')}",
            type="github_comment",
            description="Comment on related pull request",
            status="pending"
        )
        
        try:
            if not incident.analysis or not incident.analysis.related_commits:
                action.status = "skipped"
                action.result = {"reason": "No related commits found"}
                return action
            
            # Find PRs for related commits
            prs = await self.github_client.find_prs_for_commits(
                incident.analysis.related_commits
            )
            
            comments_created = []
            for pr in prs:
                comment_body = self._prepare_pr_comment(incident, pr)
                comment = await self.github_client.create_pr_comment(
                    pr["number"], comment_body
                )
                comments_created.append({
                    "pr_number": pr["number"],
                    "comment_id": comment["id"],
                    "comment_url": comment["html_url"]
                })
            
            action.status = "completed"
            action.result = {"comments": comments_created}
            
            logger.debug(f"Created {len(comments_created)} PR comments for incident {incident.id}")
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            logger.error(f"Failed to create PR comments: {e}")
        
        return action
    
    async def _send_slack_notification(self, incident: Incident) -> Action:
        """Send Slack notification about the incident"""
        action = Action(
            id=f"slack-{incident.id}-{datetime.utcnow().strftime('%H%M%S')}",
            type="slack_notification",
            description="Send Slack notification",
            status="pending"
        )
        
        try:
            message = self._prepare_slack_message(incident)
            
            response = await self.slack_client.send_message(
                channel="#alerts",  # Configure as needed
                message=message
            )
            
            action.status = "completed"
            if isinstance(response, dict):
                action.result = {
                    "message_ts": response.get("ts"),
                    "channel": response.get("channel")
                }
            else:
                action.result = {"success": bool(response)}
            
            logger.debug(f"Sent Slack notification for incident {incident.id}")
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            logger.error(f"Failed to send Slack notification: {e}")
        
        return action
    
    async def _create_github_issue(self, incident: Incident) -> Action:
        """Create a GitHub issue for code-related incidents"""
        action = Action(
            id=f"gh-issue-{incident.id}-{datetime.utcnow().strftime('%H%M%S')}",
            type="github_issue",
            description="Create GitHub issue",
            status="pending"
        )
        
        try:
            issue_data = self._prepare_github_issue_data(incident)
            
            issue = await self.github_client.create_issue(issue_data)
            
            action.status = "completed"
            action.result = {
                "issue_number": issue["number"],
                "issue_url": issue["html_url"]
            }
            
            logger.debug(f"Created GitHub issue #{issue['number']} for incident {incident.id}")
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            logger.error(f"Failed to create GitHub issue: {e}")
        
        return action
    
    async def _suggest_rollback(self, incident: Incident) -> Action:
        """Suggest rollback for deployment-related issues"""
        action = Action(
            id=f"rollback-{incident.id}-{datetime.utcnow().strftime('%H%M%S')}",
            type="rollback_suggestion",
            description="Suggest deployment rollback",
            status="pending"
        )
        
        try:
            if not incident.analysis or not incident.analysis.related_deployments:
                action.status = "skipped"
                action.result = {"reason": "No related deployments found"}
                return action
            
            # Create rollback suggestion message
            rollback_message = self._prepare_rollback_message(incident)
            
            # Send to Slack with high priority
            response = await self.slack_client.send_message(
                channel="#deployments",  # Configure as needed
                message=rollback_message,
                priority="high"
            )
            
            action.status = "completed"
            action.result = {
                "message_ts": response.get("ts"),
                "deployments": incident.analysis.related_deployments
            }
            
            logger.debug(f"Suggested rollback for incident {incident.id}")
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            logger.error(f"Failed to suggest rollback: {e}")
        
        return action
    
    def _prepare_jira_ticket_data(self, incident: Incident) -> Dict[str, Any]:
        """Prepare Jira ticket data"""
        analysis = incident.analysis
        
        description = f"""
*Incident Details:*
- ID: {incident.id}
- Severity: {getattr(incident.severity, 'value', incident.severity).upper()}
- Created: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

*Description:*
{incident.description}

*Signals Detected:*
"""
        
        for i, signal in enumerate(incident.signals, 1):
            description += f"""
{i}. *{getattr(signal.type, 'value', signal.type).title()}* from {signal.source}
   - Component: {signal.component or 'Unknown'}
   - Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
   - Details: {signal.description}
"""
        
        if analysis:
            description += f"""

*AI Analysis:*
- Root Cause: {analysis.root_cause}
- Confidence: {analysis.confidence:.1%}
- Impact: {analysis.impact_assessment or 'Not assessed'}

*Suggested Actions:*
"""
            for action in analysis.suggested_actions:
                description += f"- {action}\n"
            
            if analysis.related_deployments:
                description += f"\n*Related Deployments:* {', '.join(analysis.related_deployments)}"
            
            if analysis.related_commits:
                description += f"\n*Related Commits:* {', '.join(analysis.related_commits[:5])}"
        
        return {
            "project": {"key": "OBS"},  # Configure project key
            "summary": f"[{getattr(incident.severity, 'value', incident.severity).upper()}] {incident.title}",
            "description": description,
            "issuetype": {"name": "Bug"},
            "priority": {"name": self._map_severity_to_jira_priority(incident.severity)},
            "labels": ["observability-agent", "auto-created", getattr(incident.severity, 'value', incident.severity)]
        }
    
    def _prepare_pr_comment(self, incident: Incident, pr: Dict[str, Any]) -> str:
        """Prepare PR comment body"""
        analysis = incident.analysis
        
        comment = f"""## Observability Agent Alert

This PR may be related to incident **{incident.id}** detected in production.

**Incident Details:**
- **Severity:** {getattr(incident.severity, 'value', incident.severity).upper()}
- **Description:** {incident.description}
- **Detected:** {incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        if analysis:
            comment += f"""
**AI Analysis:**
- **Root Cause:** {analysis.root_cause}
- **Confidence:** {analysis.confidence:.1%}
"""
            
            if analysis.suggested_actions:
                comment += "\n**Recommended Actions:**\n"
                for action in analysis.suggested_actions[:3]:  # Top 3 actions
                    comment += f"- {action}\n"
        
        comment += f"""
**Next Steps:**
1. Review the changes in this PR for potential issues
2. Consider if a rollback might be necessary
3. Check the [incident dashboard](http://localhost:8080) for real-time updates

*This comment was automatically generated by the CopadoCon 2025 Hackathon.*
"""
        
        return comment
    
    def _prepare_slack_message(self, incident: Incident) -> Dict[str, Any]:
        """Prepare Slack message"""
        analysis = incident.analysis
        
        color = {
            "critical": "danger",
            "high": "warning", 
            "medium": "#ff9900",
            "low": "good"
        }.get(getattr(incident.severity, 'value', incident.severity), "#808080")
        
        fields = [
            {
                "title": "Incident ID",
                "value": incident.id,
                "short": True
            },
            {
                "title": "Severity",
                "value": getattr(incident.severity, 'value', incident.severity).upper(),
                "short": True
            },
            {
                "title": "Status",
                "value": getattr(incident.status, 'value', incident.status).title(),
                "short": True
            }
        ]
        
        if analysis:
            fields.append({
                "title": "AI Confidence",
                "value": f"{analysis.confidence:.1%}",
                "short": True
            })
            
            if analysis.root_cause:
                fields.append({
                    "title": "Root Cause",
                    "value": analysis.root_cause[:200] + "..." if len(analysis.root_cause) > 200 else analysis.root_cause,
                    "short": False
                })
        
        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"ALERT: {incident.title}",
                    "text": incident.description,
                    "fields": fields,
                    "footer": "CopadoCon 2025 Hackathon",
                    "ts": int(incident.created_at.timestamp())
                }
            ]
        }
    
    def _prepare_github_issue_data(self, incident: Incident) -> Dict[str, Any]:
        """Prepare GitHub issue data"""
        analysis = incident.analysis
        
        body = f"""## Incident Report: {incident.id}

**Severity:** {getattr(incident.severity, 'value', incident.severity).upper()}
**Status:** {getattr(incident.status, 'value', incident.status).title()}
**Created:** {incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

### Description
{incident.description}

### Signals Detected
"""
        
        for signal in incident.signals:
            body += f"""
- **{getattr(signal.type, 'value', signal.type).title()}** from `{signal.source}`
  - Component: `{signal.component or 'Unknown'}`
  - Time: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
  - Details: {signal.description}
"""
        
        if analysis:
            body += f"""
### AI Analysis
- **Root Cause:** {analysis.root_cause}
- **Confidence:** {analysis.confidence:.1%}

### Recommended Actions
"""
            for action in analysis.suggested_actions:
                body += f"- [ ] {action}\n"
            
            if analysis.code_changes:
                body += "\n### Code Changes to Investigate\n"
                for change in analysis.code_changes:
                    body += f"- `{change.get('file')}` - {change.get('description')} (likelihood: {change.get('likelihood', 0):.1%})\n"
        
        body += f"""
### Links
- [Incident Dashboard](http://localhost:8080)
- Incident ID: `{incident.id}`

---
*This issue was automatically created by the CopadoCon 2025 Hackathon.*
"""
        
        labels = ["observability", "auto-created", getattr(incident.severity, 'value', incident.severity)]
        if analysis and analysis.related_commits:
            labels.append("deployment-related")
        
        return {
            "title": f"[{getattr(incident.severity, 'value', incident.severity).upper()}] {incident.title}",
            "body": body,
            "labels": labels
        }
    
    def _prepare_rollback_message(self, incident: Incident) -> Dict[str, Any]:
        """Prepare rollback suggestion message"""
        analysis = incident.analysis
        
        return {
            "text": f"*URGENT: Rollback Recommendation*",
            "attachments": [
                {
                    "color": "danger",
                    "title": f"Incident {incident.id} - {incident.title}",
                    "fields": [
                        {
                            "title": "Severity",
                            "value": getattr(incident.severity, 'value', incident.severity).upper(),
                            "short": True
                        },
                        {
                            "title": "Confidence",
                            "value": f"{analysis.confidence:.1%}" if analysis else "N/A",
                            "short": True
                        },
                        {
                            "title": "Related Deployments",
                            "value": ", ".join(analysis.related_deployments) if analysis else "Unknown",
                            "short": False
                        },
                        {
                            "title": "Root Cause",
                            "value": analysis.root_cause if analysis else "Under investigation",
                            "short": False
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "Initiate Rollback",
                            "style": "danger",
                            "url": f"http://localhost:8080/incidents/{incident.id}"
                        },
                        {
                            "type": "button", 
                            "text": "View Details",
                            "url": f"http://localhost:8080/incidents/{incident.id}"
                        }
                    ]
                }
            ]
        }
    
    def _map_severity_to_jira_priority(self, severity) -> str:
        """Map incident severity to Jira priority"""
        mapping = {
            "critical": "Highest",
            "high": "High",
            "medium": "Medium", 
            "low": "Low"
        }
        return mapping.get(getattr(severity, 'value', severity), "Medium")
