"""
The Brain of Our Monitoring System

This is the main orchestrator that coordinates everything. It watches for problems,
analyzes what went wrong, and takes action to fix things. Think of it as the conductor
of an orchestra - it doesn't play the instruments but makes sure they all work together.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from ..detectors.signal_detector import SignalDetector
from ..analyzers.ai_analyzer import AIAnalyzer
from ..actions.action_executor import ActionExecutor
from ..models.incident import Incident, IncidentStatus
from .config import settings

class ObservabilityAgent:
    """
    The main controller that brings everything together.
    
    This class coordinates between detecting problems, analyzing them with AI,
    and taking automated actions. It runs continuously in the background,
    watching for issues and responding to them.
    """
    
    def __init__(self):
        # Set up our three main components
        self.signal_detector = SignalDetector()  # Watches for problems
        self.ai_analyzer = AIAnalyzer()          # Figures out what went wrong
        self.action_executor = ActionExecutor()  # Takes action to fix things
        
        # Keep track of current incidents and whether we're running
        self.active_incidents: Dict[str, Incident] = {}
        self.is_running = False
        
    async def start(self):
        """
        Fires up the monitoring system and gets everything ready to go.
        This initializes all our components and starts the main monitoring loop.
        """
        logger.info("Starting up the monitoring system...")
        
        # Get all our components ready to work
        await self.signal_detector.initialize()
        await self.ai_analyzer.initialize()
        await self.action_executor.initialize()
        
        # Start the main monitoring loop that watches for problems
        self.is_running = True
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("Monitoring system is now active and watching for issues")
    
    async def stop(self):
        """
        Shuts down the monitoring system gracefully.
        Makes sure all components clean up properly to avoid any hanging processes.
        """
        logger.info("Shutting down the monitoring system...")
        self.is_running = False
        
        # Tell all our components to clean up after themselves
        await self.signal_detector.cleanup()
        await self.ai_analyzer.cleanup()
        await self.action_executor.cleanup()
        
        logger.info("Monitoring system stopped cleanly")
    
    async def _monitoring_loop(self):
        """
        The main heartbeat of our system.
        
        This runs continuously, checking for new problems every few seconds.
        When it finds something, it processes it through our AI analysis
        and takes whatever actions are needed.
        """
        while self.is_running:
            try:
                # Look for new problems in Salesforce, deployments, etc.
                signals = await self.signal_detector.detect_signals()
                
                # Handle each problem we found
                for signal in signals:
                    await self._process_signal(signal)
                    
            except Exception as e:
                logger.error(f"Something went wrong in the monitoring loop: {e}")
                
            # Take a breather before checking again
            await asyncio.sleep(settings.MONITORING_INTERVAL)
    
    async def _process_signal(self, signal):
        """
        When we detect a problem, this is where we handle it.
        
        This method takes a detected issue (signal) and runs it through our
        full pipeline: create an incident, analyze it with AI, and take action
        if we're confident about what went wrong.
        """
        try:
            logger.debug(f"Processing signal: {signal.type} - {signal.description}")
            
            # Either create a new incident or add this to an existing one
            incident = await self._create_or_update_incident(signal)
            
            # Let our AI figure out what's going on
            analysis = await self.ai_analyzer.analyze_incident(incident)
            incident.analysis = analysis
            
            # If we're pretty confident we know what's wrong, take action
            if analysis.confidence > 0.7:  # Only act when we're 70%+ sure
                actions = await self.action_executor.execute_actions(incident)
                incident.actions_taken = actions
                incident.status = IncidentStatus.RESOLVING
            else:
                # Not sure enough to act automatically - flag for human review
                incident.status = IncidentStatus.INVESTIGATING
            
            # Save our work
            self.active_incidents[incident.id] = incident
            
            logger.debug(f"Incident {incident.id} processed with confidence {analysis.confidence}")
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
    
    async def _create_or_update_incident(self, signal) -> Incident:
        """
        Decides whether this is a new problem or part of an existing one.
        
        Sometimes multiple signals are actually the same underlying issue,
        so we group them together instead of creating duplicate incidents.
        """
        # See if this signal is related to something we're already tracking
        for incident in self.active_incidents.values():
            if await self._signals_related(signal, incident):
                # Add this signal to the existing incident
                incident.signals.append(signal)
                incident.updated_at = datetime.utcnow()
                return incident
        
        # Create new incident
        incident = Incident(
            id=f"INC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            title=f"{signal.type}: {signal.description}",
            description=signal.description,
            severity=signal.severity,
            signals=[signal],
            status=IncidentStatus.DETECTED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return incident
    
    async def _signals_related(self, signal, incident) -> bool:
        """Check if a signal is related to an existing incident"""
        # Simple correlation logic - can be enhanced with ML
        for existing_signal in incident.signals:
            if (signal.source == existing_signal.source or 
                signal.component == existing_signal.component):
                return True
        return False
    
    async def _check_incident_updates(self):
        """Check for updates on existing incidents"""
        for incident in list(self.active_incidents.values()):
            if incident.status == IncidentStatus.RESOLVING:
                # Check if issue is resolved
                is_resolved = await self._check_if_resolved(incident)
                if is_resolved:
                    incident.status = IncidentStatus.RESOLVED
                    incident.resolved_at = datetime.utcnow()
                    logger.info(f"Incident {incident.id} resolved")
    
    async def _check_if_resolved(self, incident) -> bool:
        """Check if an incident is resolved"""
        # Check if the original issue still exists
        return await self.signal_detector.check_resolution(incident)
    
    async def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "is_running": self.is_running,
            "active_incidents": len(self.active_incidents),
            "incidents": [
                {
                    "id": inc.id,
                    "title": inc.title,
                    "status": getattr(inc.status, 'value', inc.status),
                    "severity": getattr(inc.severity, 'value', inc.severity),
                    "created_at": inc.created_at.isoformat(),
                    "confidence": inc.analysis.confidence if inc.analysis else 0
                }
                for inc in self.active_incidents.values()
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
