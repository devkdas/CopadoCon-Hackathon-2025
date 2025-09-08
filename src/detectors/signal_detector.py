"""
Signal Detection Module
Monitors various sources for issues and anomalies
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
import json

from ..models.incident import Signal, SignalType, Severity
from ..integrations.salesforce_client import SalesforceClient
from ..integrations.github_client import GitHubClient
from ..integrations.monitoring_client import MonitoringClient
from ..core.config import settings

class SignalDetector:
    """Detects signals from various monitoring sources"""
    
    def __init__(self):
        self.salesforce_client = SalesforceClient()
        self.github_client = GitHubClient()
        self.monitoring_client = MonitoringClient()
        self.last_check_time = datetime.utcnow() - timedelta(hours=1)
        
    async def initialize(self):
        """Initialize all detection clients"""
        try:
            await self.salesforce_client.initialize()
            await self.github_client.initialize()
            await self.monitoring_client.initialize()
            logger.info("Signal detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize signal detector: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.salesforce_client.cleanup()
        await self.github_client.cleanup()
        await self.monitoring_client.cleanup()
    
    async def detect_signals(self) -> List[Signal]:
        """Detect signals from all sources"""
        signals = []
        current_time = datetime.utcnow()
        
        try:
            # Detect Salesforce errors
            sf_signals = await self._detect_salesforce_signals()
            signals.extend(sf_signals)
            
            # Detect deployment issues
            deploy_signals = await self._detect_deployment_signals()
            signals.extend(deploy_signals)
            
            # Detect test failures
            test_signals = await self._detect_test_failures()
            signals.extend(test_signals)
            
            # Detect monitoring alerts
            monitor_signals = await self._detect_monitoring_alerts()
            signals.extend(monitor_signals)
            
            # Detect log anomalies
            log_signals = await self._detect_log_anomalies()
            signals.extend(log_signals)
            
            self.last_check_time = current_time
            logger.debug(f"Detected {len(signals)} signals")
            
        except Exception as e:
            logger.error(f"Error detecting signals: {e}")
        
        return signals
    
    async def _detect_salesforce_signals(self) -> List[Signal]:
        """Detect Salesforce-specific issues"""
        signals = []
        
        try:
            # Check for Apex errors
            apex_errors = await self.salesforce_client.get_apex_errors(
                since=self.last_check_time
            )
            
            for error in apex_errors:
                signal = Signal(
                    id=f"sf-apex-{error['Id']}",
                    type=SignalType.ERROR,
                    source="salesforce",
                    component="apex",
                    description=f"Apex error: {error.get('Message', 'Unknown error')}",
                    severity=self._determine_severity(error),
                    timestamp=datetime.fromisoformat(error['CreatedDate'].replace('Z', '+00:00')),
                    metadata={
                        "class_name": error.get('ApexClass', {}).get('Name'),
                        "method_name": error.get('MethodName'),
                        "line_number": error.get('Line'),
                        "stack_trace": error.get('StackTrace')
                    },
                    raw_data=json.dumps(error)
                )
                signals.append(signal)
            
            # Check for Flow errors
            flow_errors = await self.salesforce_client.get_flow_errors(
                since=self.last_check_time
            )
            
            for error in flow_errors:
                signal = Signal(
                    id=f"sf-flow-{error['Id']}",
                    type=SignalType.ERROR,
                    source="salesforce",
                    component="flow",
                    description=f"Flow error: {error.get('ErrorMessage', 'Unknown error')}",
                    severity=self._determine_severity(error),
                    timestamp=datetime.fromisoformat(error['CreatedDate'].replace('Z', '+00:00')),
                    metadata={
                        "flow_name": error.get('FlowVersionView', {}).get('MasterLabel'),
                        "element_name": error.get('ElementName')
                    },
                    raw_data=json.dumps(error)
                )
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error detecting Salesforce signals: {e}")
        
        return signals
    
    async def _detect_deployment_signals(self) -> List[Signal]:
        """Detect deployment-related issues"""
        signals = []
        
        try:
            # Check recent deployments
            deployments = await self.salesforce_client.get_recent_deployments(
                since=self.last_check_time
            )
            
            for deployment in deployments:
                if deployment.get('Status') == 'Failed':
                    signal = Signal(
                        id=f"deploy-{deployment['Id']}",
                        type=SignalType.DEPLOYMENT,
                        source="salesforce",
                        component="deployment",
                        description=f"Deployment failed: {deployment.get('ErrorMessage', 'Unknown error')}",
                        severity=Severity.HIGH,
                        timestamp=datetime.fromisoformat(deployment['CreatedDate'].replace('Z', '+00:00')),
                        metadata={
                            "deployment_id": deployment['Id'],
                            "created_by": deployment.get('CreatedBy', {}).get('Name'),
                            "component_failures": deployment.get('ComponentFailures', [])
                        },
                        raw_data=json.dumps(deployment)
                    )
                    signals.append(signal)
            
            # Check GitHub deployments
            gh_deployments = await self.github_client.get_failed_deployments(
                since=self.last_check_time
            )
            
            for deployment in gh_deployments:
                signal = Signal(
                    id=f"gh-deploy-{deployment['id']}",
                    type=SignalType.DEPLOYMENT,
                    source="github",
                    component="deployment",
                    description=f"GitHub deployment failed: {deployment.get('description', 'Unknown error')}",
                    severity=Severity.HIGH,
                    timestamp=datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00')),
                    metadata={
                        "deployment_id": deployment['id'],
                        "environment": deployment.get('environment'),
                        "ref": deployment.get('ref'),
                        "sha": deployment.get('sha')
                    },
                    raw_data=json.dumps(deployment)
                )
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error detecting deployment signals: {e}")
        
        return signals
    
    async def _detect_test_failures(self) -> List[Signal]:
        """Detect test failures"""
        signals = []
        
        try:
            # Check Apex test failures
            test_results = await self.salesforce_client.get_test_results(
                since=self.last_check_time
            )
            
            for result in test_results:
                if result.get('Outcome') == 'Fail':
                    signal = Signal(
                        id=f"test-{result['Id']}",
                        type=SignalType.TEST_FAILURE,
                        source="salesforce",
                        component="apex_test",
                        description=f"Test failure: {result.get('MethodName')} - {result.get('Message', 'Unknown error')}",
                        severity=Severity.MEDIUM,
                        timestamp=datetime.fromisoformat(result['SystemModstamp'].replace('Z', '+00:00')),
                        metadata={
                            "test_class": result.get('ApexClass', {}).get('Name'),
                            "test_method": result.get('MethodName'),
                            "stack_trace": result.get('StackTrace'),
                            "run_time": result.get('TestTimestamp')
                        },
                        raw_data=json.dumps(result)
                    )
                    signals.append(signal)
                    
        except Exception as e:
            logger.error(f"Error detecting test failure signals: {e}")
        
        return signals
    
    async def _detect_monitoring_alerts(self) -> List[Signal]:
        """Detect monitoring system alerts"""
        signals = []
        
        try:
            alerts = await self.monitoring_client.get_alerts(
                since=self.last_check_time
            )
            
            for alert in alerts:
                # Handle timestamp safely
                timestamp_str = alert.get('timestamp')
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.utcnow()  # Fallback to current time
                
                signal = Signal(
                    id=f"monitoring-{alert['id']}",
                    type=SignalType.MONITORING_ALERT,
                    source="monitoring",
                    component=alert.get('component'),
                    description=f"Monitoring alert: {alert.get('message')}",
                    severity=self._map_alert_severity(alert.get('severity')),
                    timestamp=timestamp,
                    metadata=alert.get('metadata', {}),
                    raw_data=json.dumps(alert)
                )
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error detecting monitoring signals: {e}")
        
        return signals
    
    async def _detect_log_anomalies(self) -> List[Signal]:
        """Detect anomalies in log patterns"""
        signals = []
        
        try:
            # This would integrate with log analysis tools
            # For now, simulate some log anomaly detection
            anomalies = await self.monitoring_client.detect_log_anomalies(
                since=self.last_check_time
            )
            
            for anomaly in anomalies:
                # Handle timestamp safely
                timestamp_str = anomaly.get('timestamp')
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.utcnow()  # Fallback to current time
                
                signal = Signal(
                    id=f"log-anomaly-{anomaly['id']}",
                    type=SignalType.LOG_ANOMALY,
                    source="logs",
                    component=anomaly.get('component'),
                    description=f"Log anomaly detected: {anomaly.get('description')}",
                    severity=Severity.MEDIUM,
                    timestamp=timestamp,
                    metadata=anomaly.get('metadata', {}),
                    raw_data=json.dumps(anomaly)
                )
                signals.append(signal)
                
        except Exception as e:
            logger.error(f"Error detecting log anomaly signals: {e}")
        
        return signals
    
    async def check_resolution(self, incident) -> bool:
        """Check if an incident has been resolved"""
        try:
            # Check if the original signals are still occurring
            for signal in incident.signals:
                if signal.type == SignalType.ERROR:
                    # Check if the error is still happening
                    recent_errors = await self._check_recent_errors(signal)
                    if recent_errors:
                        return False
                elif signal.type == SignalType.DEPLOYMENT:
                    # Check if deployment is now successful
                    deployment_status = await self._check_deployment_status(signal)
                    if deployment_status != "Success":
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking incident resolution: {e}")
            return False
    
    async def _check_recent_errors(self, signal: Signal) -> bool:
        """Check if similar errors are still occurring"""
        # Implementation would check for recent similar errors
        return False
    
    async def _check_deployment_status(self, signal: Signal) -> str:
        """Check current deployment status"""
        # Implementation would check deployment status
        return "Success"
    
    def _determine_severity(self, error_data: Dict[str, Any]) -> Severity:
        """Determine severity based on error data"""
        # Simple severity mapping - can be enhanced with ML
        error_message = error_data.get('Message', '').lower()
        
        if any(keyword in error_message for keyword in ['critical', 'fatal', 'system']):
            return Severity.CRITICAL
        elif any(keyword in error_message for keyword in ['error', 'exception', 'fail']):
            return Severity.HIGH
        elif any(keyword in error_message for keyword in ['warning', 'deprecated']):
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _map_alert_severity(self, alert_severity: str) -> Severity:
        """Map monitoring alert severity to our severity enum"""
        mapping = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'warning': Severity.MEDIUM,
            'error': Severity.HIGH
        }
        return mapping.get(alert_severity.lower(), Severity.MEDIUM)
