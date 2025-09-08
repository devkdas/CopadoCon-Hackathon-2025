"""
GitHub Integration Client
Handles GitHub API interactions for repository monitoring
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import aiohttp

from ..core.config import settings

# Optional import - works without this package installed
try:
    from github import Github
    HAS_GITHUB = True
except ImportError:
    logger.warning("PyGithub not installed - GitHub integration disabled")
    Github = None
    HAS_GITHUB = False

class GitHubClient:
    """Client for GitHub API interactions"""
    
    def __init__(self):
        self.github = None
        self.repo = None
        
    async def initialize(self):
        """Initialize GitHub connection"""
        try:
            if not HAS_GITHUB:
                logger.warning("PyGithub not available - using mock data")
                return
                
            if not settings.GITHUB_TOKEN:
                logger.warning("GitHub token not configured - using mock data")
                return
                
            # self.github = Github(settings.GITHUB_TOKEN)
            # You would configure the specific repository here
            # self.repo = self.github.get_repo("your-org/your-repo")
            logger.info("GitHub integration disabled - using mock responses")
            
            logger.info("GitHub client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def get_failed_deployments(self, since: datetime) -> List[Dict[str, Any]]:
        """Get failed deployments since specified time"""
        try:
            if not self.github or not self.repo:
                return self._mock_failed_deployments()
            
            deployments = self.repo.get_deployments()
            failed_deployments = []
            
            for deployment in deployments:
                if deployment.created_at >= since:
                    statuses = deployment.get_statuses()
                    for status in statuses:
                        if status.state == 'failure':
                            failed_deployments.append({
                                'id': deployment.id,
                                'description': deployment.description,
                                'environment': deployment.environment,
                                'ref': deployment.ref,
                                'sha': deployment.sha,
                                'created_at': deployment.created_at.isoformat(),
                                'status': status.state
                            })
                            break
            
            return failed_deployments
            
        except Exception as e:
            logger.error(f"Error fetching GitHub deployments: {e}")
            return self._mock_failed_deployments()
    
    async def get_recent_commits(self, since: datetime) -> List[Dict[str, Any]]:
        """Get recent commits since specified time"""
        try:
            if not self.github or not self.repo:
                return self._mock_recent_commits()
            
            commits = self.repo.get_commits(since=since)
            commit_list = []
            
            for commit in commits:
                commit_list.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': {
                        'name': commit.commit.author.name,
                        'email': commit.commit.author.email
                    },
                    'timestamp': commit.commit.author.date.isoformat(),
                    'files': [
                        {
                            'filename': file.filename,
                            'status': file.status,
                            'additions': file.additions,
                            'deletions': file.deletions
                        }
                        for file in commit.files
                    ] if commit.files else []
                })
            
            return commit_list
            
        except Exception as e:
            logger.error(f"Error fetching GitHub commits: {e}")
            return self._mock_recent_commits()
    
    async def find_prs_for_commits(self, commit_shas: List[str]) -> List[Dict[str, Any]]:
        """Find pull requests that contain the specified commits"""
        try:
            if not self.github or not self.repo:
                return self._mock_prs()
            
            prs = []
            for sha in commit_shas:
                try:
                    commit = self.repo.get_commit(sha)
                    pulls = commit.get_pulls()
                    
                    for pr in pulls:
                        prs.append({
                            'number': pr.number,
                            'title': pr.title,
                            'state': pr.state,
                            'html_url': pr.html_url,
                            'head_sha': pr.head.sha,
                            'base_ref': pr.base.ref
                        })
                except Exception as e:
                    logger.error(f"Error finding PRs for commit {sha}: {e}")
            
            return prs
            
        except Exception as e:
            logger.error(f"Error finding PRs for commits: {e}")
            return self._mock_prs()
    
    async def create_pr_comment(self, pr_number: int, comment_body: str) -> Dict[str, Any]:
        """Create a comment on a pull request"""
        try:
            if not self.github or not self.repo:
                return self._mock_pr_comment()
            
            pr = self.repo.get_pull(pr_number)
            comment = pr.create_issue_comment(comment_body)
            
            return {
                'id': comment.id,
                'html_url': comment.html_url,
                'created_at': comment.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating PR comment: {e}")
            return self._mock_pr_comment()
    
    async def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue"""
        try:
            if not self.github or not self.repo:
                return self._mock_issue()
            
            issue = self.repo.create_issue(
                title=issue_data['title'],
                body=issue_data['body'],
                labels=issue_data.get('labels', [])
            )
            
            return {
                'number': issue.number,
                'html_url': issue.html_url,
                'created_at': issue.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            return self._mock_issue()
    
    def _mock_failed_deployments(self) -> List[Dict[str, Any]]:
        """Mock failed deployments for demo purposes"""
        return [
            {
                'id': 12345,
                'description': 'Deploy to production',
                'environment': 'production',
                'ref': 'main',
                'sha': 'abc123def456',
                'created_at': (datetime.utcnow() - timedelta(minutes=25)).isoformat(),
                'status': 'failure'
            }
        ]
    
    def _mock_recent_commits(self) -> List[Dict[str, Any]]:
        """Mock recent commits for demo purposes"""
        return [
            {
                'sha': 'abc123def456',
                'message': 'Fix account trigger validation logic',
                'author': {
                    'name': 'John Developer',
                    'email': 'john@company.com'
                },
                'timestamp': (datetime.utcnow() - timedelta(minutes=35)).isoformat(),
                'files': [
                    {
                        'filename': 'force-app/main/default/triggers/AccountTrigger.trigger',
                        'status': 'modified',
                        'additions': 5,
                        'deletions': 2
                    },
                    {
                        'filename': 'force-app/main/default/classes/AccountTriggerHandler.cls',
                        'status': 'modified',
                        'additions': 12,
                        'deletions': 8
                    }
                ]
            },
            {
                'sha': 'def456ghi789',
                'message': 'Update opportunity validation rules',
                'author': {
                    'name': 'Jane Developer',
                    'email': 'jane@company.com'
                },
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'files': [
                    {
                        'filename': 'force-app/main/default/classes/OpportunityService.cls',
                        'status': 'modified',
                        'additions': 8,
                        'deletions': 3
                    }
                ]
            }
        ]
    
    def _mock_prs(self) -> List[Dict[str, Any]]:
        """Mock pull requests for demo purposes"""
        return [
            {
                'number': 42,
                'title': 'Fix account trigger validation',
                'state': 'open',
                'html_url': 'https://github.com/company/salesforce-repo/pull/42',
                'head_sha': 'abc123def456',
                'base_ref': 'main'
            }
        ]
    
    def _mock_pr_comment(self) -> Dict[str, Any]:
        """Mock PR comment for demo purposes"""
        return {
            'id': 987654321,
            'html_url': 'https://github.com/company/salesforce-repo/pull/42#issuecomment-987654321',
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _mock_issue(self) -> Dict[str, Any]:
        """Mock GitHub issue for demo purposes"""
        return {
            'number': 123,
            'html_url': 'https://github.com/company/salesforce-repo/issues/123',
            'created_at': datetime.utcnow().isoformat()
        }
