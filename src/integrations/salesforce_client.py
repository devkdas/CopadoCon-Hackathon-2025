"""
Salesforce Integration Client
Handles Salesforce API interactions for monitoring and data retrieval
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import aiohttp

from ..core.config import settings

# Optional import - works without this package installed
try:
    from simple_salesforce import Salesforce
    HAS_SALESFORCE = True
except ImportError:
    logger.warning("simple_salesforce not installed - Salesforce integration disabled")
    Salesforce = None
    HAS_SALESFORCE = False

class SalesforceClient:
    """Client for Salesforce API interactions"""
    
    def __init__(self):
        self.sf = None
        self.session = None
        
    async def initialize(self):
        """Initialize Salesforce connection"""
        try:
            if not HAS_SALESFORCE:
                logger.warning("simple_salesforce not available - using mock data")
                return
                
            if not all([settings.SALESFORCE_USERNAME, settings.SALESFORCE_PASSWORD, settings.SALESFORCE_SECURITY_TOKEN]):
                logger.warning("Salesforce credentials not configured - using mock data")
                return
                
            self.sf = Salesforce(
                username=settings.SALESFORCE_USERNAME,
                password=settings.SALESFORCE_PASSWORD,
                security_token=settings.SALESFORCE_SECURITY_TOKEN,
                domain=settings.SALESFORCE_DOMAIN or 'login'
            )
            
            logger.info("Salesforce client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce client: {e}")
            # Continue with mock data for demo purposes
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def get_apex_errors(self, since: datetime) -> List[Dict[str, Any]]:
        """Get Apex errors since specified time"""
        try:
            if not self.sf:
                return self._mock_apex_errors()
            
            # Query ApexLog for errors
            since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            query = f"""
            SELECT Id, Application, DurationMilliseconds, Location, LogLength, 
                   LogUser.Name, Operation, Request, StartTime, Status, 
                   SystemModstamp, ApexClass.Name, MethodName, Line, Message, StackTrace
            FROM ApexLog 
            WHERE StartTime >= {since_str} 
            AND Status = 'Failed'
            ORDER BY StartTime DESC
            LIMIT 100
            """
            
            result = self.sf.query(query)
            return result['records']
            
        except Exception as e:
            logger.error(f"Error fetching Apex errors: {e}")
            return self._mock_apex_errors()
    
    async def get_flow_errors(self, since: datetime) -> List[Dict[str, Any]]:
        """Get Flow errors since specified time"""
        try:
            if not self.sf:
                return self._mock_flow_errors()
            
            since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            query = f"""
            SELECT Id, FlowVersionView.MasterLabel, ElementName, ErrorMessage, 
                   CreatedDate, CreatedBy.Name
            FROM FlowExecutionErrorEvent 
            WHERE CreatedDate >= {since_str}
            ORDER BY CreatedDate DESC
            LIMIT 100
            """
            
            result = self.sf.query(query)
            return result['records']
            
        except Exception as e:
            logger.error(f"Error fetching Flow errors: {e}")
            return self._mock_flow_errors()
    
    async def get_recent_deployments(self, since: datetime) -> List[Dict[str, Any]]:
        """Get recent deployments since specified time"""
        try:
            if not self.sf:
                return self._mock_deployments()
            
            since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            query = f"""
            SELECT Id, Status, CreatedDate, CreatedBy.Name, CompletedDate,
                   ErrorMessage, ComponentFailures
            FROM DeployRequest 
            WHERE CreatedDate >= {since_str}
            ORDER BY CreatedDate DESC
            LIMIT 50
            """
            
            result = self.sf.query(query)
            return result['records']
            
        except Exception as e:
            logger.error(f"Error fetching deployments: {e}")
            return self._mock_deployments()
    
    async def get_test_results(self, since: datetime) -> List[Dict[str, Any]]:
        """Get test results since specified time"""
        try:
            if not self.sf:
                return self._mock_test_results()
            
            since_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            query = f"""
            SELECT Id, ApexClass.Name, MethodName, Outcome, Message, 
                   StackTrace, TestTimestamp, SystemModstamp
            FROM ApexTestResult 
            WHERE SystemModstamp >= {since_str}
            AND Outcome = 'Fail'
            ORDER BY SystemModstamp DESC
            LIMIT 100
            """
            
            result = self.sf.query(query)
            return result['records']
            
        except Exception as e:
            logger.error(f"Error fetching test results: {e}")
            return self._mock_test_results()
    
    def _mock_apex_errors(self) -> List[Dict[str, Any]]:
        """Mock Apex errors for demo purposes"""
        return [
            {
                'Id': 'apex_001',
                'Message': 'System.NullPointerException: Attempt to de-reference a null object',
                'CreatedDate': (datetime.utcnow() - timedelta(minutes=15)).isoformat() + 'Z',
                'ApexClass': {'Name': 'AccountTriggerHandler'},
                'MethodName': 'updateAccountStatus',
                'Line': 42,
                'StackTrace': 'Class.AccountTriggerHandler.updateAccountStatus: line 42, column 1'
            },
            {
                'Id': 'apex_002', 
                'Message': 'System.DmlException: FIELD_CUSTOM_VALIDATION_EXCEPTION',
                'CreatedDate': (datetime.utcnow() - timedelta(minutes=8)).isoformat() + 'Z',
                'ApexClass': {'Name': 'OpportunityService'},
                'MethodName': 'validateOpportunity',
                'Line': 78,
                'StackTrace': 'Class.OpportunityService.validateOpportunity: line 78, column 1'
            }
        ]
    
    def _mock_flow_errors(self) -> List[Dict[str, Any]]:
        """Mock Flow errors for demo purposes"""
        return [
            {
                'Id': 'flow_001',
                'FlowVersionView': {'MasterLabel': 'Account Update Flow'},
                'ElementName': 'Update_Account_Record',
                'ErrorMessage': 'The flow failed to access the database.',
                'CreatedDate': (datetime.utcnow() - timedelta(minutes=12)).isoformat() + 'Z',
                'CreatedBy': {'Name': 'System User'}
            }
        ]
    
    def _mock_deployments(self) -> List[Dict[str, Any]]:
        """Mock deployment data for demo purposes"""
        return [
            {
                'Id': 'deploy_001',
                'Status': 'Failed',
                'CreatedDate': (datetime.utcnow() - timedelta(minutes=30)).isoformat() + 'Z',
                'CreatedBy': {'Name': 'John Developer'},
                'ErrorMessage': 'Apex class compilation failed',
                'ComponentFailures': ['AccountTrigger.trigger']
            },
            {
                'Id': 'deploy_002',
                'Status': 'Succeeded',
                'CreatedDate': (datetime.utcnow() - timedelta(hours=2)).isoformat() + 'Z',
                'CreatedBy': {'Name': 'Jane Developer'},
                'ErrorMessage': None,
                'ComponentFailures': []
            }
        ]
    
    def _mock_test_results(self) -> List[Dict[str, Any]]:
        """Mock test results for demo purposes"""
        return [
            {
                'Id': 'test_001',
                'ApexClass': {'Name': 'AccountTriggerTest'},
                'MethodName': 'testAccountUpdate',
                'Outcome': 'Fail',
                'Message': 'System.AssertException: Assertion Failed',
                'StackTrace': 'Class.AccountTriggerTest.testAccountUpdate: line 25',
                'TestTimestamp': (datetime.utcnow() - timedelta(minutes=20)).isoformat() + 'Z',
                'SystemModstamp': (datetime.utcnow() - timedelta(minutes=20)).isoformat() + 'Z'
            }
        ]
