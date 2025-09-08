"""
AI Analysis Engine
Uses AI to perform intelligent root cause analysis and correlation
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import json
import re

from ..models.incident import Incident, Analysis, Signal, SignalType
from ..integrations.salesforce_client import SalesforceClient
from ..integrations.github_client import GitHubClient
from ..core.config import settings

# Optional import - works without this package installed
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    logger.warning("openai not installed - AI analysis disabled")
    openai = None
    HAS_OPENAI = False

class AIAnalyzer:
    """AI-powered incident analysis engine"""
    
    def __init__(self):
        self.openai_client = None
        self.salesforce_client = SalesforceClient()
        self.github_client = GitHubClient()
        
    async def initialize(self):
        """Initialize AI analyzer"""
        try:
            if not HAS_OPENAI:
                logger.warning("openai package not available - using mock analysis")
                return
                
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not configured - using fallback analysis")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def analyze_incident(self, incident: Incident) -> Analysis:
        """Perform comprehensive AI analysis of an incident"""
        try:
            logger.debug(f"Analyzing incident {incident.id}")
            
            # Gather context data
            context = await self._gather_context(incident)
            
            # Perform AI analysis
            if self.openai_client:
                analysis = await self._ai_analysis(incident, context)
            else:
                analysis = await self._fallback_analysis(incident, context)
            
            logger.debug(f"Analysis completed for {incident.id} with confidence {analysis.confidence}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing incident {incident.id}: {e}")
            return Analysis(
                root_cause="Analysis failed due to error",
                confidence=0.0,
                analysis_timestamp=datetime.utcnow()
            )
    
    async def _gather_context(self, incident: Incident) -> Dict[str, Any]:
        """Gather contextual information for analysis"""
        context = {
            "recent_deployments": [],
            "recent_commits": [],
            "related_code_changes": [],
            "similar_incidents": [],
            "system_metrics": {}
        }
        
        try:
            # Get recent deployments (last 24 hours)
            deployments = await self.salesforce_client.get_recent_deployments(
                since=datetime.utcnow() - timedelta(hours=24)
            )
            context["recent_deployments"] = deployments
            
            # Get recent commits from GitHub
            commits = await self.github_client.get_recent_commits(
                since=datetime.utcnow() - timedelta(hours=24)
            )
            context["recent_commits"] = commits
            
            # Analyze code changes for each signal
            for signal in incident.signals:
                if signal.type in [SignalType.ERROR, SignalType.TEST_FAILURE]:
                    code_analysis = await self._analyze_code_changes(signal, commits)
                    context["related_code_changes"].extend(code_analysis)
            
            # Find similar historical incidents
            similar = await self._find_similar_incidents(incident)
            context["similar_incidents"] = similar
            
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
        
        return context
    
    async def _ai_analysis(self, incident: Incident, context: Dict[str, Any]) -> Analysis:
        """Perform AI-powered analysis using OpenAI"""
        try:
            # Prepare analysis prompt
            prompt = self._build_analysis_prompt(incident, context)
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Salesforce developer and DevOps engineer specializing in root cause analysis. Analyze the provided incident data and provide detailed insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            analysis = self._parse_ai_response(ai_response, context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return await self._fallback_analysis(incident, context)
    
    async def _fallback_analysis(self, incident: Incident, context: Dict[str, Any]) -> Analysis:
        """Fallback analysis when AI is not available"""
        analysis = Analysis()
        
        try:
            # Rule-based analysis
            confidence = 0.0
            root_cause_factors = []
            suggested_actions = []
            
            # Check for deployment correlation
            deployment_correlation = self._check_deployment_correlation(incident, context)
            if deployment_correlation:
                root_cause_factors.append(f"Correlated with deployment: {deployment_correlation}")
                confidence += 0.4
                suggested_actions.append("Review recent deployment changes")
            
            # Check for code change correlation
            code_correlation = self._check_code_correlation(incident, context)
            if code_correlation:
                root_cause_factors.append(f"Related to code changes: {code_correlation}")
                confidence += 0.3
                suggested_actions.append("Review recent code changes")
            
            # Check for similar incidents
            if context.get("similar_incidents"):
                root_cause_factors.append("Similar incidents found in history")
                confidence += 0.2
                suggested_actions.append("Review resolution of similar incidents")
            
            # Analyze signal patterns
            pattern_analysis = self._analyze_signal_patterns(incident)
            if pattern_analysis:
                root_cause_factors.extend(pattern_analysis["factors"])
                confidence += pattern_analysis["confidence_boost"]
                suggested_actions.extend(pattern_analysis["actions"])
            
            analysis.root_cause = "; ".join(root_cause_factors) if root_cause_factors else "Unable to determine root cause"
            analysis.confidence = min(confidence, 1.0)
            analysis.suggested_actions = suggested_actions
            analysis.related_deployments = [d["Id"] for d in context.get("recent_deployments", [])]
            analysis.related_commits = [c["sha"] for c in context.get("recent_commits", [])]
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            analysis.root_cause = "Analysis failed"
            analysis.confidence = 0.0
        
        return analysis
    
    def _build_analysis_prompt(self, incident: Incident, context: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for AI"""
        prompt = f"""
Analyze this Salesforce incident and provide root cause analysis:

INCIDENT DETAILS:
- ID: {incident.id}
- Title: {incident.title}
- Description: {incident.description}
- Severity: {incident.severity.value}
- Created: {incident.created_at}

SIGNALS:
"""
        
        for i, signal in enumerate(incident.signals, 1):
            prompt += f"""
Signal {i}:
- Type: {signal.type.value}
- Source: {signal.source}
- Component: {signal.component}
- Description: {signal.description}
- Timestamp: {signal.timestamp}
- Metadata: {json.dumps(signal.metadata, indent=2)}
"""
        
        prompt += f"""

CONTEXT:
Recent Deployments: {len(context.get('recent_deployments', []))} deployments in last 24h
Recent Commits: {len(context.get('recent_commits', []))} commits in last 24h
Related Code Changes: {len(context.get('related_code_changes', []))} potential correlations
Similar Incidents: {len(context.get('similar_incidents', []))} historical matches

ANALYSIS REQUIRED:
1. Root Cause Analysis: What is the most likely root cause?
2. Confidence Level: How confident are you (0.0-1.0)?
3. Correlation Analysis: Which deployments/commits are related?
4. Impact Assessment: What is the business impact?
5. Suggested Actions: What specific actions should be taken?
6. Code Changes: Any specific code changes to investigate?

Please provide your analysis in the following JSON format:
{{
    "root_cause": "detailed root cause explanation",
    "confidence": 0.85,
    "related_deployments": ["deployment_id1", "deployment_id2"],
    "related_commits": ["commit_sha1", "commit_sha2"],
    "impact_assessment": "impact description",
    "suggested_actions": ["action1", "action2", "action3"],
    "code_changes": [
        {{
            "file": "path/to/file",
            "change_type": "modification/addition/deletion",
            "description": "what changed",
            "likelihood": 0.8
        }}
    ]
}}
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, context: Dict[str, Any]) -> Analysis:
        """Parse AI response into Analysis object"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                
                return Analysis(
                    root_cause=response_data.get("root_cause", "Unknown"),
                    confidence=float(response_data.get("confidence", 0.0)),
                    related_deployments=response_data.get("related_deployments", []),
                    related_commits=response_data.get("related_commits", []),
                    suggested_actions=response_data.get("suggested_actions", []),
                    code_changes=response_data.get("code_changes", []),
                    impact_assessment=response_data.get("impact_assessment"),
                    analysis_timestamp=datetime.utcnow()
                )
            else:
                # Fallback parsing
                return Analysis(
                    root_cause=ai_response[:500],  # First 500 chars as root cause
                    confidence=0.5,
                    analysis_timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return Analysis(
                root_cause="Failed to parse AI analysis",
                confidence=0.0,
                analysis_timestamp=datetime.utcnow()
            )
    
    async def _analyze_code_changes(self, signal: Signal, commits: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze code changes related to a signal"""
        related_changes = []
        
        try:
            # Look for commits that might be related to the error
            for commit in commits:
                relevance_score = 0.0
                
                # Check commit message for keywords
                message = commit.get("message", "").lower()
                if signal.component and signal.component.lower() in message:
                    relevance_score += 0.4
                
                # Check for error-related keywords
                error_keywords = ["fix", "bug", "error", "issue", "problem"]
                if any(keyword in message for keyword in error_keywords):
                    relevance_score += 0.3
                
                # Check file changes
                files_changed = commit.get("files", [])
                for file_info in files_changed:
                    filename = file_info.get("filename", "")
                    if signal.component and signal.component.lower() in filename.lower():
                        relevance_score += 0.5
                
                if relevance_score > 0.3:  # Threshold for relevance
                    related_changes.append({
                        "commit_sha": commit["sha"],
                        "message": commit["message"],
                        "author": commit.get("author", {}).get("name"),
                        "timestamp": commit["timestamp"],
                        "relevance_score": relevance_score,
                        "files_changed": files_changed
                    })
                    
        except Exception as e:
            logger.error(f"Error analyzing code changes: {e}")
        
        return related_changes
    
    async def _find_similar_incidents(self, incident: Incident) -> List[Dict[str, Any]]:
        """Find similar historical incidents"""
        # This would typically query a database of historical incidents
        # For now, return empty list as placeholder
        return []
    
    def _check_deployment_correlation(self, incident: Incident, context: Dict[str, Any]) -> Optional[str]:
        """Check if incident correlates with recent deployments"""
        deployments = context.get("recent_deployments", [])
        
        for deployment in deployments:
            try:
                deploy_time = datetime.fromisoformat(deployment["CreatedDate"].replace('Z', '+00:00'))
                
                # Check if any signal occurred after this deployment
                for signal in incident.signals:
                    # Ensure both datetimes are timezone-aware for comparison
                    signal_time = signal.timestamp
                    if signal_time.tzinfo is None:
                        signal_time = signal_time.replace(tzinfo=deploy_time.tzinfo)
                    
                    time_diff = (signal_time - deploy_time).total_seconds()
                    if 0 < time_diff < 3600:  # Within 1 hour after deployment
                        return deployment["Id"]
            except (ValueError, AttributeError) as e:
                logger.debug(f"Error parsing deployment time: {e}")
                continue
        
        return None
    
    def _check_code_correlation(self, incident: Incident, context: Dict[str, Any]) -> Optional[str]:
        """Check if incident correlates with code changes"""
        code_changes = context.get("related_code_changes", [])
        
        if code_changes:
            # Return the most relevant code change
            most_relevant = max(code_changes, key=lambda x: x.get("relevance_score", 0))
            return most_relevant["commit_sha"]
        
        return None
    
    def _analyze_signal_patterns(self, incident: Incident) -> Optional[Dict[str, Any]]:
        """Analyze patterns in the incident signals"""
        if not incident.signals:
            return None
        
        analysis = {
            "factors": [],
            "confidence_boost": 0.0,
            "actions": []
        }
        
        # Check for error clustering
        error_signals = [s for s in incident.signals if s.type == SignalType.ERROR]
        if len(error_signals) > 1:
            analysis["factors"].append(f"Multiple errors detected ({len(error_signals)})")
            analysis["confidence_boost"] += 0.1
            analysis["actions"].append("Investigate error clustering pattern")
        
        # Check for component concentration
        components = [s.component for s in incident.signals if s.component]
        if len(set(components)) == 1 and len(components) > 1:
            analysis["factors"].append(f"All errors in same component: {components[0]}")
            analysis["confidence_boost"] += 0.2
            analysis["actions"].append(f"Focus investigation on {components[0]} component")
        
        # Check timing patterns
        timestamps = [s.timestamp for s in incident.signals]
        if len(timestamps) > 1:
            # Ensure all timestamps are timezone-aware for comparison
            from datetime import timezone
            normalized_timestamps = []
            for ts in timestamps:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                normalized_timestamps.append(ts)
            
            time_span = (max(normalized_timestamps) - min(normalized_timestamps)).total_seconds()
            if time_span < 300:  # All within 5 minutes
                analysis["factors"].append("Signals clustered in time (< 5 minutes)")
                analysis["confidence_boost"] += 0.15
                analysis["actions"].append("Investigate what triggered simultaneous issues")
        
        return analysis if analysis["factors"] else None
